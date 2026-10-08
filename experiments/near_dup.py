"""Near-duplicate rate of the v2 training split under MinHash-LSH (within language).

usage: python near_dup.py <v2 dir> <out_json> [threshold=0.8] [num_perm=64] [comma-separated language folders]
Shingles: character 5-grams of the text with annotation-independent whitespace collapsed. A document is a
near-duplicate if some *earlier* document in the same language has estimated Jaccard >= threshold. Also reports the
share after masking digits (so templates differing only in numbers collapse) -- the failure mode expected on a fixed
attribute grid.
"""
import glob, json, os, re, sys
import pyarrow.parquet as pq
from datasketch import MinHash, MinHashLSH

def sig(text, num_perm, mask):
    t = re.sub(r"\s+", " ", text.lower())
    if mask:
        t = re.sub(r"\d", "0", t)
    m = MinHash(num_perm=num_perm)
    m.update_batch([g.encode("utf8") for g in {t[i:i + 5] for i in range(max(1, len(t) - 4))}])
    return m

def main(root, out, thr=0.8, num_perm=64, only=None):
    thr, num_perm = float(thr), int(num_perm)
    only = set(only.split(',')) if only else None
    res = {}
    for f in sorted(glob.glob(os.path.join(root, "*/train-*.parquet"))):
        lang = os.path.basename(os.path.dirname(f))
        if lang.startswith("eval") or (only and lang not in only):
            continue
        texts = pq.read_table(f, columns=["text"]).column("text").to_pylist()
        res[lang] = {"docs": len(texts)}
        for mask in (False, True):
            lsh = MinHashLSH(threshold=thr, num_perm=num_perm); dup = 0
            for i, t in enumerate(texts):
                m = sig(t, num_perm, mask)
                if lsh.query(m):
                    dup += 1
                else:
                    lsh.insert(str(i), m)
            res[lang]["near_dup_digitmasked" if mask else "near_dup"] = dup
        print(lang, res[lang], flush=True)
    tot = sum(v["docs"] for v in res.values())
    res["_total"] = {"docs": tot, "near_dup": sum(v.get("near_dup", 0) for k, v in res.items() if k != "_total"),
                     "near_dup_digitmasked": sum(v.get("near_dup_digitmasked", 0) for k, v in res.items() if k != "_total"),
                     "threshold": thr, "num_perm": num_perm}
    json.dump(res, open(out, "w"), indent=1)

if __name__ == "__main__":
    main(*sys.argv[1:6])
