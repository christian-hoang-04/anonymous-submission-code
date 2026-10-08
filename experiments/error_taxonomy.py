"""Where do exact-match misses on the human-annotated corpora come from?

For every scored gold span not matched exactly, classify it as
  boundary   : a prediction with the SAME label overlaps it (wrong boundaries)
  label      : only predictions with a DIFFERENT label overlap it
  missed     : no prediction overlaps it
and for every unmatched prediction as
  boundary-fp: overlaps a gold span of the same label (counterpart of 'boundary')
  label-fp   : overlaps a gold span of a different label
  spurious   : overlaps no scored gold span (and no ignored region)
usage: python error_taxonomy.py <prepped_dir> <results_dir> <out_json>
"""
import json
import os
import sys
from collections import Counter


def ov(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def main(prepped, results, out):
    res = {}
    for fn in sorted(os.listdir(results)):
        r = json.load(open(os.path.join(results, fn), encoding="utf8"))
        model = r["model"]
        for ds in ("grascco_phi", "meddocan_test"):
            rows = [json.loads(line) for line in open(os.path.join(prepped, ds + ".jsonl"), encoding="utf8")]
            c = Counter()
            for row in rows:
                gold = [(g["start"], g["end"], g["label"]) for g in row["gold"] if g["label"]]
                ign = [(g["start"], g["end"]) for g in row["gold"] if not g["label"]]
                pred = sorted({tuple(p) for p in r["predictions"][ds].get(row["id"], [])})
                gset = set(gold)
                for g in gold:
                    if g in set(pred):
                        c["match"] += 1
                        continue
                    hits = [p for p in pred if ov(p, g) > 0]
                    if not hits:
                        c["missed"] += 1
                    elif any(p[2] == g[2] for p in hits):
                        c["boundary"] += 1
                    else:
                        c["label"] += 1
                for p in pred:
                    if p in gset:
                        continue
                    hits = [g for g in gold if ov(p, g) > 0]
                    if hits:
                        c["boundary_fp" if any(g[2] == p[2] for g in hits) else "label_fp"] += 1
                    elif any(ov(p, i) > 0 for i in ign):
                        c["ignored_region"] += 1
                    else:
                        c["spurious_fp"] += 1
            res.setdefault(ds, {})[model] = dict(c)
    json.dump(res, open(out, "w"), indent=1)
    for ds, ms in res.items():
        print(ds)
        for m, c in ms.items():
            gold = c.get("match", 0) + c.get("missed", 0) + c.get("boundary", 0) + c.get("label", 0)
            print(f"  {m:8} gold={gold:5} match={c.get('match',0)/gold:.2f} boundary={c.get('boundary',0)/gold:.2f} "
                  f"label={c.get('label',0)/gold:.2f} missed={c.get('missed',0)/gold:.2f} | fp: spurious={c.get('spurious_fp',0)} "
                  f"boundary={c.get('boundary_fp',0)} label={c.get('label_fp',0)} ignored={c.get('ignored_region',0)}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
