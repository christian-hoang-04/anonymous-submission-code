"""Cumulative ladder separating convention/definition mismatch from genuine detection failure (exploratory).

Levels (cumulative, identical for every system):
  L0  primary analysis (as in the paper's main table)
  L1  + boundary convention: strip a leading honorific (Herr/Frau/Dr./Prof./Sr./Sra./Dña. ...) from predicted
        human_name spans, because both guidelines annotate the name only
  L2  + definition mismatch: ignore gold spans that OUR definition does not cover:
        countries (GraSCCo LOCATION_COUNTRY, MEDDOCAN PAIS), kinship words (MEDDOCAN FAMILIARES_SUJETO_ASISTENCIA),
        and non-specific dates (a bare year, or a duration such as "3 anos")
  L3  + hospitals/institutions removed (company_name gold and predictions ignored) -- NOT a definition mismatch:
        our definition includes hospitals, so L2 -> L3 measures a real weakness shared by most systems.
The L2 families were fixed from the Pii label definitions in the paper (address = street/postal/coordinates/care
location; date = specific date tied to a person or encounter), not from the error counts, but the ladder is exploratory.
usage: python sensitivity_ladder.py <prepped_dir> <results_dir> <out_json>
"""
import json
import os
import re
import sys

from score import doc_counts, prf

HON = re.compile(r"^(?:(?:herrn?|frau|dr|dra|prof|pd|med|dipl|d|dna|dña|sr|sra|srta|don|doña|doña)\.?\s*)+", re.I)
MISMATCH_SRC = {"LOCATION_COUNTRY", "PAIS", "FAMILIARES_SUJETO_ASISTENCIA"}
YEAR = re.compile(r"^\D{0,12}(?:19|20)\d{2}$")
DURATION = re.compile(r"\b(a[nñ]os?|meses|mes|d[ií]as|semanas|jahre|jahren|monate|monaten|tage|tagen|wochen)\b", re.I)


def nonspecific_date(t):
    t = t.strip()
    return bool(YEAR.match(t)) or bool(DURATION.search(t) and not re.search(r"\d{1,2}[./-]\d{1,2}", t))


def strip_hon(text, p):
    if p[2] != "human_name":
        return p
    m = HON.match(text[p[0]:p[1]])
    if m and m.end() < p[1] - p[0]:
        return [p[0] + m.end(), p[1], p[2]]
    return p


def f1(rows, preds, mode="exact"):
    tot = [0, 0, 0]
    for r in rows:
        for v in doc_counts(r["gold"], preds.get(r["id"], []), mode).values():
            for i in range(3):
                tot[i] += v[i]
    return prf(*tot)[2]


def main(prepped, results, out):
    table = {}
    for ds in ("grascco_phi", "meddocan_test"):
        base = [json.loads(line) for line in open(os.path.join(prepped, ds + ".jsonl"), encoding="utf8")]
        for fn in sorted(os.listdir(results)):
            res = json.load(open(os.path.join(results, fn), encoding="utf8"))
            preds0 = res["predictions"][ds]
            texts = {r["id"]: r["text"] for r in base}
            preds1 = {k: [strip_hon(texts[k], p) for p in v] for k, v in preds0.items()}
            rows2 = json.loads(json.dumps(base))
            n_ignored = 0
            for r in rows2:
                for g in r["gold"]:
                    if g["label"] and (g["src"] in MISMATCH_SRC or (g["label"] == "date" and nonspecific_date(r["text"][g["start"]:g["end"]]))):
                        g["label"] = None
                        n_ignored += 1
            rows3 = json.loads(json.dumps(rows2))
            for r in rows3:
                for g in r["gold"]:
                    if g["label"] == "company_name":
                        g["label"] = None
            preds3 = {k: [p for p in v if p[2] != "company_name"] for k, v in preds1.items()}
            table.setdefault(ds, {})[res["model"]] = {
                "L0": f1(base, preds0), "L1": f1(base, preds1), "L2": f1(rows2, preds1), "L3": f1(rows3, preds3),
                "L0_relaxed": f1(base, preds0, "relaxed"), "L2_relaxed": f1(rows2, preds1, "relaxed"),
                "L3_relaxed": f1(rows3, preds3, "relaxed"), "gold_ignored_at_L2": n_ignored}
    json.dump(table, open(out, "w"), indent=1)
    for ds, ms in table.items():
        print(ds, "(gold spans ignored at L2:", next(iter(ms.values()))["gold_ignored_at_L2"], ")")
        for m, e in sorted(ms.items(), key=lambda kv: -kv[1]["L3"]):
            print(f"  {m:8} L0 {e['L0']:.3f}  L1 {e['L1']:.3f}  L2 {e['L2']:.3f}  L3 {e['L3']:.3f}   relaxed L0 {e['L0_relaxed']:.3f} L3 {e['L3_relaxed']:.3f}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
