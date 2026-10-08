"""Post-hoc sensitivity analysis (NOT the primary result): drop the source-label families on which the two annotation
guidelines and the Kaleido ontology disagree about what counts as PII, then re-score every system.

Dropped as ignored regions (same treatment as age/profession in the primary analysis):
  GraSCCo_PHI : LOCATION_HOSPITAL, LOCATION_ORGANIZATION, LOCATION_COUNTRY
  MEDDOCAN    : HOSPITAL, CENTRO_SALUD, INSTITUCION, PAIS, FAMILIARES_SUJETO_ASISTENCIA
The families were chosen after seeing the error taxonomy, so this analysis is exploratory.
usage: python sensitivity_guideline.py <prepped_dir> <results_dir> <out_json>
"""
import json
import os
import random
import sys

from score import doc_counts, f1_from, prf

DROP = {
    "grascco_phi": {"LOCATION_HOSPITAL", "LOCATION_ORGANIZATION", "LOCATION_COUNTRY"},
    "meddocan_test": {"HOSPITAL", "CENTRO_SALUD", "INSTITUCION", "PAIS", "FAMILIARES_SUJETO_ASISTENCIA"},
}


def main(prepped, results, out):
    table = {}
    for ds, drop in DROP.items():
        rows = [json.loads(line) for line in open(os.path.join(prepped, ds + ".jsonl"), encoding="utf8")]
        for r in rows:
            for g in r["gold"]:
                if g["src"] in drop:
                    g["label"] = None
        for fn in sorted(os.listdir(results)):
            res = json.load(open(os.path.join(results, fn), encoding="utf8"))
            preds = res["predictions"][ds]
            entry = {}
            for mode in ("exact", "relaxed"):
                per_doc = []
                for r in rows:
                    p = [x for x in preds.get(r["id"], []) if x[2] != "company_name"]
                    per_doc.append(doc_counts(r["gold"], p, mode))
                tot = [0, 0, 0]
                for d in per_doc:
                    for v in d.values():
                        for i in range(3):
                            tot[i] += v[i]
                rng = random.Random(0)
                boots = []
                for _ in range(1000):
                    agg = [0, 0, 0]
                    for _ in per_doc:
                        for v in per_doc[rng.randrange(len(per_doc))].values():
                            for i in range(3):
                                agg[i] += v[i]
                    boots.append(prf(*agg)[2])
                boots.sort()
                entry[mode] = {"f1": prf(*tot)[2], "ci95": [boots[24], boots[974]]}
            table.setdefault(ds, {})[res["model"]] = entry
    json.dump(table, open(out, "w"), indent=1)
    for ds, ms in table.items():
        print(ds)
        for m, e in sorted(ms.items(), key=lambda kv: -kv[1]["exact"]["f1"]):
            print(f"  {m:8} exact {e['exact']['f1']:.3f} [{e['exact']['ci95'][0]:.3f},{e['exact']['ci95'][1]:.3f}]  relaxed {e['relaxed']['f1']:.3f}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
