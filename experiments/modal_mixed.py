"""Run audit_mixed.py on a Modal CPU container (the Hub datasets are gated; the Modal HF secret has access).

usage: MODAL_PROFILE=modal-profile modal run modal_mixed.py   -> writes results/mixed_audit.json next to this file
"""
from pathlib import Path
import modal

HERE = Path(__file__).resolve().parent
image = (modal.Image.debian_slim(python_version="3.12").pip_install("pyarrow", "huggingface_hub==1.19.0")
         .add_local_file(str(HERE / "audit_mixed.py"), "/root/audit_mixed.py"))
app = modal.App("kaleidopii-naacl-mixed-audit")


@app.function(image=image, cpu=4, memory=16384, timeout=3 * 3600, secrets=[modal.Secret.from_name("huggingface-secret")])
def run() -> str:
    import json, sys
    sys.path.insert(0, "/root")
    import audit_mixed
    audit_mixed.main("/tmp/work", "/tmp/out.json")
    return open("/tmp/out.json").read()


@app.local_entrypoint()
def main():
    out = HERE / "results" / "mixed_audit.json"
    out.write_text(run.remote(), encoding="utf8")
    print("wrote", out)
