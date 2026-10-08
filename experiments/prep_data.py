"""Download-free converter: unpacked GraSCCo_PHI / MEDDOCAN -> normalized JSONL.

usage: python prep_data.py <data_root> <out_dir>
  <data_root>/grascco_phi/grascco_phi_annotation_json/*.json   (Zenodo 10.5281/zenodo.11502329, CC-BY-4.0)
  <data_root>/meddocan/meddocan/{train,dev,test}/brat/*.{txt,ann} (Zenodo 10.5281/zenodo.4279323, CC-BY-4.0)
Each output row: {"id","text","language","gold":[{"start","end","src","label"|null}]}; label=None => ignored region.
"""
import glob, json, os, sys
from mapping import GRASCCO_MAP, GRASCCO_IGNORED, MEDDOCAN_MAP, MEDDOCAN_IGNORED

def grascco(root):
    for f in sorted(glob.glob(os.path.join(root, "grascco_phi/grascco_phi_annotation_json/*.json"))):
        d = json.load(open(f, encoding="utf8"))
        fs = d["%FEATURE_STRUCTURES"]
        text = next(x for x in fs if x["%TYPE"] == "uima.cas.Sofa")["sofaString"]
        gold = []
        for x in fs:
            if x["%TYPE"] != "webanno.custom.PHI":
                continue
            kind = x.get("kind")
            if kind is None or "begin" not in x:
                continue
            if kind in GRASCCO_MAP:
                lab = GRASCCO_MAP[kind]
            elif kind in GRASCCO_IGNORED:
                lab = None
            else:
                raise ValueError(f"unmapped GraSCCo kind {kind}")
            gold.append({"start": x["begin"], "end": x["end"], "src": kind, "label": lab})
        yield {"id": os.path.basename(f).split(".txt")[0], "text": text, "language": "de", "gold": gold}

def meddocan(root, split):
    for ann in sorted(glob.glob(os.path.join(root, f"meddocan/meddocan/{split}/brat/*.ann"))):
        text = open(ann[:-4] + ".txt", encoding="utf8", newline="").read()
        gold = []
        for line in open(ann, encoding="utf8"):
            if not line.startswith("T"):
                continue
            _, meta, _surface = line.rstrip("\n").split("\t", 2)
            kind, *offs = meta.split(" ", 1)[0], meta.split(" ", 1)[1]
            # discontinuous spans are written "a b;c d"; use the outer extent
            nums = [int(n) for part in meta.split(" ", 1)[1].split(";") for n in part.split()]
            lab = MEDDOCAN_MAP.get(kind)
            if lab is None and kind not in MEDDOCAN_IGNORED:
                raise ValueError(f"unmapped MEDDOCAN kind {kind}")
            gold.append({"start": min(nums), "end": max(nums), "src": kind, "label": lab})
        yield {"id": os.path.basename(ann)[:-4], "text": text, "language": "es", "gold": gold}

def main(root, out):
    os.makedirs(out, exist_ok=True)
    sets = {"grascco_phi": list(grascco(root)), "meddocan_test": list(meddocan(root, "test")),
            "meddocan_dev": list(meddocan(root, "dev"))}
    for name, rows in sets.items():
        with open(os.path.join(out, name + ".jsonl"), "w", encoding="utf8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        n = sum(1 for r in rows for g in r["gold"] if g["label"])
        print(name, "docs", len(rows), "scored gold spans", n, "ignored", sum(1 for r in rows for g in r["gold"] if not g["label"]))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
