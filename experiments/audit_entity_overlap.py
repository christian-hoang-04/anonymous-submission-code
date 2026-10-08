"""Entity-value overlap between the 1M-row training table and each evaluation set (run on Modal; Hub data is gated).

For every evaluation set and label, the share of gold spans whose exact (label, value) string occurs among the training
spans of (a) Kaleido synthetic rows (kaleidopii-v1 + v2), (b) rows from the same public source as the evaluation set.
High (a) on a public benchmark that Kaleido did not generate => shared placeholder inventory; high (b) => in-distribution
entity values (same personas / templates), i.e. not out-of-distribution transfer.
usage: python audit_entity_overlap.py <work_dir> <out_json>
"""
import hashlib, json, os, sys
from collections import Counter, defaultdict
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

def h(cat, val):
    return hashlib.blake2b(f"{cat}\x00{val}".encode("utf8"), digest_size=8).digest()

GROUPS = {"kaleidopii-v1": "kaleido", "kaleidopii-v2": "kaleido", "nemotron": "nemotron", "gretel": "gretel",
          "ai4privacy": "ai4privacy", "creddata": "creddata"}
EVAL_SOURCE = {"nemotron_en": "nemotron", "gretel_en": "gretel", "creddata_en": "creddata"}

def main(work, out):
    api = HfApi(); sets = defaultdict(set)
    shards = sorted(s.rfilename for s in api.dataset_info("anonymous-placeholder/kaleidopii-mixed").siblings if s.rfilename.startswith("data/train-"))
    for fn in shards:
        p = hf_hub_download("anonymous-placeholder/kaleidopii-mixed", fn, repo_type="dataset", local_dir=work)
        for r in pq.read_table(p, columns=["label", "info"]).to_pylist():
            g = GROUPS.get(r["info"].get("source_dataset"), "other")
            for s in r["label"] or []:
                sets[g].add(h(s["category"], s["text"]))
        os.remove(p); print(fn, {k: len(v) for k, v in sets.items()}, flush=True)
    res = {"train_unique_values": {k: len(v) for k, v in sets.items()}, "eval": {}}
    ext = [s.rfilename for s in api.dataset_info("anonymous-placeholder/kaleidopii-external").siblings if s.rfilename.endswith(".parquet") and "/eval" in s.rfilename]
    v2 = [s.rfilename for s in api.dataset_info("anonymous-placeholder/kaleidopii-v2", revision="060980f190b94913814d067c9b60d415949c2720").siblings
          if s.rfilename.startswith("eval") and s.rfilename.endswith(".parquet")]
    jobs = [("anonymous-placeholder/kaleidopii-external", f, None) for f in ext] + [("anonymous-placeholder/kaleidopii-v2", f, "060980f190b94913814d067c9b60d415949c2720") for f in v2]
    for repo, f, rev in jobs:
        name = f.split("/")[0]; p = hf_hub_download(repo, f, repo_type="dataset", local_dir=work, revision=rev)
        src = EVAL_SOURCE.get(name, "ai4privacy" if name.startswith("ai4privacy") else None)
        tot = Counter(); in_m = Counter(); in_s = Counter()
        for r in pq.read_table(p, columns=["label"]).to_pylist():
            for s in r["label"] or []:
                k = h(s["category"], s["text"]); c = s["category"]
                tot[c] += 1; in_m[c] += k in sets["kaleido"]
                if src: in_s[c] += k in sets[src]
        res["eval"][name] = {"spans": sum(tot.values()), "in_kaleido_train": sum(in_m.values()),
                             "in_same_source_train": sum(in_s.values()) if src else None,
                             "per_label": {c: {"n": tot[c], "kaleido": in_m[c], "same_source": in_s[c] if src else None} for c in tot}}
        print(name, res["eval"][name]["spans"], res["eval"][name]["in_kaleido_train"], res["eval"][name]["in_same_source_train"], flush=True)
        os.remove(p)
    json.dump(res, open(out, "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:3])
