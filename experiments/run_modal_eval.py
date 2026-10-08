"""Run five PII systems on the prepped real-text corpora (GraSCCo_PHI, MEDDOCAN) on Modal GPUs.

Read-only use of the repository: `src` is mounted as a copy and its pinned adapters are called
unchanged. Nothing in the repository is modified. Images are defined here (not in the repo runners) so that the
known runner failures are avoided: Python 3.12 (PEP 695 `type` alias), `tiktoken`+`sentencepiece` for GLiNER2, and
Linux (OPF imports `fcntl`).

usage (from this folder):
  MODAL_PROFILE=modal-profile SCRATCH=<scratch> modal run run_modal_eval.py --model ours
models: ours | openmed | gliner2 | lfm25 | opf
PII_ROOT must point at the repository folder (read-only use). SCRATCH must contain prepped/*.jsonl (from prep_data.py) and refs/liquidai-pii-detection-space (pinned Space clone,
sha256 of pii.py verified) and receives results/<model>.json holding character offsets + labels only.
"""
import json
import os
from pathlib import Path

import modal

# Paths are only meaningful on the local client; inside the container this module is re-imported, so keep defaults safe.
SCRATCH = Path(os.environ.get("SCRATCH", "/tmp"))
PROJECT = Path(os.environ.get("PII_ROOT", "/tmp"))  # <project-root>
REPO = PROJECT
PY = "3.12"
HF = {"HF_HOME": "/cache/hf", "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}
SECRET = [modal.Secret.from_name("huggingface-secret")]


def _img(pkgs, env=None, extra_dirs=()):
    image = modal.Image.debian_slim(python_version=PY).apt_install("gcc").pip_install(*pkgs).env({**HF, **(env or {})})
    for local, remote in extra_dirs:
        image = image.add_local_dir(str(local), remote_path=remote)
    return image.add_local_dir(str(REPO / "src"), remote_path="/root/src").add_local_dir(
        str(SCRATCH / "prepped"), remote_path="/data")


BASE = ["torch==2.13.0", "transformers==5.11.0", "huggingface_hub==1.19.0", "safetensors==0.8.0", "numpy"]
IMAGES = {
    "ours": _img(BASE + ["peft==0.19.1"], {"PYTHONPATH": "/root/src"}),
    "openmed": _img(BASE + ["sentencepiece", "protobuf"], {"PYTHONPATH": "/root/src"}),
    "gliner2": _img(["gliner2[local]==1.3.2", "huggingface_hub==1.19.0", "tiktoken", "sentencepiece", "protobuf"],
                    {"PYTHONPATH": "/root/src", "FLASH_DEBERTA": "1"}),
    "lfm25": _img(BASE + ["tokenizers==0.22.2", "pyarrow"], {"PYTHONPATH": "/root/src"},
                  [(SCRATCH / "refs" / "liquidai-pii-detection-space", "/reference/liquidai-pii-detection-space")]),
    "opf": _img(BASE + ["triton==3.7.1", "tiktoken==0.12.0"],
                {"PYTHONPATH": "/root/src:/root/openai-privacy-filter"},
                [(PROJECT / "context" / "references" / "openai-privacy-filter",
                  "/root/openai-privacy-filter")]),
}
app = modal.App("naacl-revision-eval")
SETS = ("grascco_phi", "meddocan_test")


def _rows():
    for name in SETS:
        yield name, [json.loads(line) for line in open(f"/data/{name}.jsonl", encoding="utf8")]


def _run(model: str) -> str:
    import time

    out, timing = {}, {}
    if model == "ours":
        import sys
        from huggingface_hub import snapshot_download
        path = snapshot_download("anonymous-placeholder/v2")
        sys.path.insert(0, path)
        from modeling_pii import PiiExtractor
        ex = PiiExtractor.from_pretrained(path, device="cuda")
        predict = lambda texts: [[(s.start, s.end, s.label) for s in ex.extract(t)] for t in texts]  # noqa: E731
    else:
        if model == "openmed":
            from pii.eval_baseline.adapters.openmed import OpenMedAdapter
            adapter = OpenMedAdapter()
        elif model == "gliner2":
            from pii.eval_baseline.adapters.gliner2 import Gliner2Adapter
            adapter = Gliner2Adapter(batch_size=16, num_workers=2)
        elif model == "opf":
            from pii.eval_baseline.adapters.opf import OpfAdapter
            adapter = OpfAdapter()
        elif model == "lfm25":
            from huggingface_hub import snapshot_download
            from pii.eval_baseline.adapters import lfm25_pii as m
            root = Path("/reference/liquidai-pii-detection-space")
            detector = m.load_pinned_space_detector(
                snapshot_path=Path(snapshot_download(m.MODEL_ID, revision=m.MODEL_REVISION)),
                source_path=root / "pii.py", space_root=root,
                space_revision="f645508a233038955a4e20bc1ccfcfb771bee1da",
                expected_source_sha256="00b4e681fdecc70e33e58588f1f7db63302a370b7cc4a72604fc5cfefba7f1af")
            adapter = m.Lfm25PiiSpaceAdapter(detector)
        else:
            raise ValueError(model)
        adapter.load()
        predict = lambda texts: [[(s.start, s.end, s.label) for s in spans] for spans in adapter.predict(texts)]  # noqa: E731
    for name, rows in _rows():
        t0 = time.perf_counter()
        preds = predict([r["text"] for r in rows])
        timing[name] = round(time.perf_counter() - t0, 2)
        out[name] = {r["id"]: p for r, p in zip(rows, preds)}
    return json.dumps({"model": model, "predict_seconds": timing, "predictions": out})


_KW = dict(gpu="A10G", timeout=3600, secrets=SECRET)


@app.function(image=IMAGES["ours"], **_KW)
def run_ours() -> str:
    return _run("ours")


@app.function(image=IMAGES["openmed"], **_KW)
def run_openmed() -> str:
    return _run("openmed")


@app.function(image=IMAGES["gliner2"], **_KW)
def run_gliner2() -> str:
    return _run("gliner2")


@app.function(image=IMAGES["lfm25"], **_KW)
def run_lfm25() -> str:
    return _run("lfm25")


@app.function(image=IMAGES["opf"], **_KW)
def run_opf() -> str:
    return _run("opf")


FUNCS = {"ours": run_ours, "openmed": run_openmed, "gliner2": run_gliner2, "lfm25": run_lfm25, "opf": run_opf}


@app.local_entrypoint()
def main(model: str):
    res = FUNCS[model].remote()
    dest = SCRATCH / "results"
    dest.mkdir(exist_ok=True)
    (dest / f"{model}.json").write_text(res, encoding="utf8")
    print("wrote", dest / f"{model}.json", len(res), "bytes")
