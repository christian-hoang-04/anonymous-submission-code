"""Score prediction files against the prepped gold.

usage: python score.py <prepped_dir> <results_dir> <out_dir>
Metrics (micro, pooled over documents):
  exact    TP iff label AND both character boundaries match a gold span.
  relaxed  TP iff label matches and the spans overlap (>=1 char); one-to-one greedy by overlap length.
  untyped  exact boundaries, label ignored (boundary quality independent of the ontology mapping).
Gold spans with label None (age, profession, sex, honorific title, ...) are ignored regions: a prediction overlapping
one (and no scored gold span) is dropped rather than counted as a false positive.
95% CIs: percentile bootstrap over documents (1000 resamples, seed 0).
"""
import json, os, random, sys
from collections import defaultdict
from mapping import PII_LABELS

def overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))

def doc_counts(gold, pred, mode):
    """Return {label: [tp, fp, fn]} for one doc."""
    scored = [(g["start"], g["end"], g["label"]) for g in gold if g["label"]]
    ignored = [(g["start"], g["end"]) for g in gold if not g["label"]]
    pred = sorted({tuple(p) for p in pred})
    kept = []
    for p in pred:
        hit_scored = any(overlap(p, g) > 0 for g in scored)
        if not hit_scored and any(overlap(p, i) > 0 for i in ignored):
            continue
        kept.append(p)
    out = defaultdict(lambda: [0, 0, 0])
    if mode == "relaxed":
        pairs = sorted(((overlap(p, g), pi, gi) for pi, p in enumerate(kept) for gi, g in enumerate(scored)
                        if p[2] == g[2] and overlap(p, g) > 0), reverse=True)
        up, ug = set(), set()
        for _, pi, gi in pairs:
            if pi in up or gi in ug:
                continue
            up.add(pi); ug.add(gi)
        for pi, p in enumerate(kept):
            out[p[2]][0 if pi in up else 1] += 1
        for gi, g in enumerate(scored):
            if gi not in ug:
                out[g[2]][2] += 1
        return out
    gset = {(g[0], g[1], g[2] if mode == "exact" else None) for g in scored}
    pset = {(p[0], p[1], p[2] if mode == "exact" else None) for p in kept}
    lab = lambda t, src: t[2] if mode == "exact" else "all"  # noqa: E731
    for t in pset:
        key = t[2] if mode == "exact" else next((p[2] for p in kept if (p[0], p[1]) == (t[0], t[1])), "all")
        out[key][0 if t in gset else 1] += 1
    for t in gset:
        if t not in pset:
            key = t[2] if mode == "exact" else next((g[2] for g in scored if (g[0], g[1]) == (t[0], t[1])), "all")
            out[key][2] += 1
    return out

def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0)

def f1_from(counts):
    tp = sum(c[0] for c in counts); fp = sum(c[1] for c in counts); fn = sum(c[2] for c in counts)
    return prf(tp, fp, fn)

def drop_label(rows, preds, label):
    """Sensitivity variant: treat `label` gold spans as ignored regions and discard predictions of that label."""
    rows2 = [dict(r, gold=[dict(g, label=None) if g["label"] == label else g for g in r["gold"]]) for r in rows]
    preds2 = {k: [p for p in v if p[2] != label] for k, v in preds.items()}
    return rows2, preds2

def main(prepped, results, out):
    os.makedirs(out, exist_ok=True)
    table = {}
    for dset in ("grascco_phi", "meddocan_test"):
        rows = [json.loads(l) for l in open(os.path.join(prepped, dset + ".jsonl"), encoding="utf8")]
        for fn in sorted(os.listdir(results)):
            res = json.load(open(os.path.join(results, fn), encoding="utf8"))
            model = res["model"]
            preds = res["predictions"].get(dset)
            if preds is None:
                continue
            variants = {"": (rows, preds), "_excl_company": drop_label(rows, preds, "company_name")}
            for vname, (vrows, vpreds) in variants.items():
              for mode in ("exact", "relaxed", "untyped"):
                per_doc = [doc_counts(r["gold"], vpreds.get(r["id"], []), mode) for r in vrows]
                tot = defaultdict(lambda: [0, 0, 0])
                for d in per_doc:
                    for k, v in d.items():
                        for i in range(3):
                            tot[k][i] += v[i]
                p, r_, f = f1_from(tot.values())
                rng = random.Random(0); boots = []
                for _ in range(1000):
                    sample = [per_doc[rng.randrange(len(per_doc))] for _ in per_doc]
                    agg = [0, 0, 0]
                    for d in sample:
                        for v in d.values():
                            for i in range(3):
                                agg[i] += v[i]
                    boots.append(prf(*agg)[2])
                boots.sort()
                entry = {"precision": p, "recall": r_, "f1": f, "ci95": [boots[24], boots[974]],
                         "tp_fp_fn": [sum(v[i] for v in tot.values()) for i in range(3)]}
                if mode in ("exact", "relaxed"):
                    entry["per_label"] = {k: dict(zip(("p", "r", "f1"), prf(*tot[k]))) | {"support": tot[k][0] + tot[k][2]}
                                          for k in PII_LABELS if k in tot}
                table.setdefault(dset, {}).setdefault(model, {})[mode + vname] = entry
            table[dset][model]["predict_seconds"] = res.get("predict_seconds", {}).get(dset)
    json.dump(table, open(os.path.join(out, "scores.json"), "w"), indent=1)
    for dset, models in table.items():
        print(f"\n== {dset}")
        print(f"{'model':10} {'exact F1 [95% CI]':26} {'P':>6} {'R':>6} {'relaxed F1':>10} {'untyped F1':>10}")
        for m, v in sorted(models.items(), key=lambda kv: -kv[1]["exact"]["f1"]):
            e = v["exact"]
            print(f"{m:10} {e['f1']:.3f} [{e['ci95'][0]:.3f},{e['ci95'][1]:.3f}]   {e['precision']:6.3f} {e['recall']:6.3f} "
                  f"{v['relaxed']['f1']:10.3f} {v['untyped']['f1']:10.3f}")

if __name__ == "__main__":
    main(*sys.argv[1:4])
