"""Composition of anonymous-placeholder/kaleidopii-mixed (the 1,000,000-row training table) and text overlap with the evaluation sets.

usage: python audit_overlap.py <work_dir> <out_json>
Streams shards from the Hub into <work_dir>, keeps only hashes/counters, and deletes shards afterwards.
Keys: exact = sha256(text); norm = sha256(lowercase, whitespace-collapsed text). Eval sets: every config/split of
anonymous-placeholder/kaleidopii-external (ai4privacy_*, gretel_en, creddata_en, nemotron_en; split "eval") and anonymous-placeholder/kaleidopii-v2
(eval, eval-challenge, eval-v2).
"""
import glob, hashlib, json, os, re, sys
from collections import Counter, defaultdict
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

def h(t):
    return hashlib.sha256(t.encode("utf8")).digest()[:16]

def norm(t):
    return hashlib.sha256(re.sub(r"\s+", " ", t.lower()).strip().encode("utf8")).digest()[:16]

def main(work, out):
    api = HfApi(); os.makedirs(work, exist_ok=True)
    comp = Counter(); comp_lang = defaultdict(Counter); ex_idx = {}; nm_idx = {}
    shards = [s.rfilename for s in api.dataset_info("anonymous-placeholder/kaleidopii-mixed").siblings
              if s.rfilename.startswith("data/train-")]
    for fn in sorted(shards):
        p = hf_hub_download("anonymous-placeholder/kaleidopii-mixed", fn, repo_type="dataset", local_dir=work)
        t = pq.read_table(p, columns=["text", "info"]).to_pylist()
        for r in t:
            src = (r["info"].get("source_dataset") or "<EMPTY>"); comp[src] += 1
            comp_lang[src][r["info"].get("language_bucket") or r["info"].get("language") or "?"] += 1
            ex_idx.setdefault(h(r["text"]), src); nm_idx.setdefault(norm(r["text"]), src)
        os.remove(p); print(fn, len(t), flush=True)
    res = {"mixed_rows": sum(comp.values()), "composition": comp.most_common(),
           "composition_by_language": {k: dict(v) for k, v in comp_lang.items()}, "overlap": {}}
    ext = api.dataset_info("anonymous-placeholder/kaleidopii-external")
    targets = []
    for s in ext.siblings:
        n = s.rfilename
        if n.endswith(".parquet") and "/eval" in n:
            targets.append(("anonymous-placeholder/kaleidopii-external", n))
    v2 = api.dataset_info("anonymous-placeholder/kaleidopii-v2", revision="060980f190b94913814d067c9b60d415949c2720")
    for s in v2.siblings:
        if s.rfilename.startswith(("eval", "eval-")) and s.rfilename.endswith(".parquet"):
            targets.append(("anonymous-placeholder/kaleidopii-v2", s.rfilename))
    for repo, n in targets:
        p = hf_hub_download(repo, n, repo_type="dataset", local_dir=work, revision=("060980f190b94913814d067c9b60d415949c2720" if "v2" in repo else None))
        rows = pq.read_table(p, columns=["text"]).column("text").to_pylist()
        e = sum(1 for t in rows if h(t) in ex_idx); m = sum(1 for t in rows if norm(t) in nm_idx)
        srcs = Counter(ex_idx[h(t)] for t in rows if h(t) in ex_idx)
        res["overlap"][f"{repo}:{n}"] = {"rows": len(rows), "exact_in_train": e, "normalized_in_train": m, "exact_sources": dict(srcs)}
        print(n, len(rows), e, m, flush=True); os.remove(p)
    json.dump(res, open(out, "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:3])
