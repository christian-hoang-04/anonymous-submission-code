"""Aggregate audit of the released KaleidoPII v2 training split (revision 060980f1...), no raw text persisted.

usage: python audit_v2.py <dir with <language>/train-*.parquet> <out_json> [train|eval]
Reports, per language and overall: document/span counts, document-length and spans-per-document distributions,
per-label counts and unique-value ratios, offset consistency, bracket/markup-contaminated spans, U+FFFD rate,
placeholder-value rates (555 phones, sequential-filler phones, canonical placeholder names), intra-document tag
inconsistency (a value tagged somewhere in a document but left bare elsewhere), scenario concentration, and per-generator
repair/defect rates.
"""
import glob, json, os, re, sys
from collections import Counter, defaultdict
import pyarrow.parquet as pq

PLACEHOLDER_NAMES = {"john doe", "jane doe", "john smith", "jane smith", "山田太郎", "山田 太郎", "佐藤花子", "佐藤 花子",
                     "张伟", "李明", "王芳", "홍길동", "김철수", "nguyễn văn a", "nguyễn văn an", "juan dela cruz",
                     "ivan ivanov", "иван иванов", "max mustermann", "erika mustermann"}

def nanp555(digits):
    """555 as area code or exchange of a North-American-style number (a reserved-for-fiction exchange)."""
    d = digits[1:] if len(digits) == 11 and digits[0] == "1" else digits
    if len(d) == 10:
        return d[:3] == "555" or d[3:6] == "555"
    return len(d) == 7 and d[:3] == "555"

SEQ = re.compile(r"1234567|123-4567|12345678|0123456|9876543")
LABELS = ["address", "company_name", "date", "email_address", "human_name", "id_number", "phone_number", "private_url", "secret"]
CHECK_LABELS = {"human_name", "id_number", "phone_number", "email_address"}

def pct(xs, q):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else 0

def main(root, out, group="train"):
    res = {"per_language": {}}
    gen = defaultdict(lambda: Counter())
    scen = Counter(); doc_types = Counter(); fmts = Counter()
    all_vals = defaultdict(Counter)
    for f in sorted(glob.glob(os.path.join(root, "*/train-*.parquet"))):
        lang = os.path.basename(os.path.dirname(f))
        if lang.startswith("eval") != (group == "eval"):
            continue
        t = pq.read_table(f).to_pylist()
        L = Counter(); lens = []; spd = []
        lab_n = Counter(); lab_vals = defaultdict(set); toplang = defaultdict(Counter)
        for r in t:
            text, spans, info = r["text"], r["label"] or [], r["info"]
            m = info.get("generation_model") or "<EMPTY>"
            g = gen[m]; g["docs"] += 1
            g["repaired"] += bool(info.get("had_label_repairs"))
            scen[info.get("scenario") or "<EMPTY>"] += 1
            doc_types[info.get("document_type") or "<EMPTY>"] += 1
            fmts[info.get("text_format") or "<EMPTY>"] += 1
            L["docs"] += 1; lens.append(len(text)); spd.append(len(spans))
            if "\ufffd" in text: L["docs_with_fffd"] += 1; g["fffd"] += 1
            doc_flag_bracket = doc_flag_incons = False
            tagged = defaultdict(int)
            for s in spans:
                lab_n[s["category"]] += 1; L["spans"] += 1; g["spans"] += 1
                val = text[s["start"]:s["end"]]
                if val != s["text"]: L["offset_mismatch"] += 1
                if "[" in val or "]" in val or "\n" in val:
                    L["spans_with_markup_or_newline"] += 1; g["bad_span"] += 1; doc_flag_bracket = True
                if len(val) > 80 and s["category"] not in ("address", "private_url", "secret", "company_name"):
                    L["overlong_span_gt80"] += 1; g["bad_span"] += 1
                lab_vals[s["category"]].add(val)
                if s["category"] in CHECK_LABELS and len(val) >= 4:
                    tagged[(s["category"], val)] += 1
                if s["category"] == "human_name":
                    toplang["human_name"][val] += 1
                    if val.strip().lower() in PLACEHOLDER_NAMES: L["placeholder_names"] += 1
                if s["category"] == "phone_number":
                    L["phones"] += 1
                    digits = re.sub(r"\D", "", val)
                    if "555" in digits: L["phones_with_555"] += 1  # loose substring (overcounts)
                    if nanp555(digits): L["phones_nanp555"] += 1
                    if SEQ.search(digits): L["phones_sequential_filler"] += 1
                    toplang["phone_number"][val] += 1
            for (cat, val), n in tagged.items():
                if text.count(val) > n:
                    L["tagged_value_also_bare"] += 1; doc_flag_incons = True
            L["docs_with_bare_repeat"] += doc_flag_incons
            L["docs_with_markup_span"] += doc_flag_bracket
            L["docs_zero_spans"] += (len(spans) == 0)
        for k, v in lab_vals.items(): all_vals[k].update(v)
        res["per_language"][lang] = {
            **L, "len_chars": {q: pct(lens, q) for q in (.05, .5, .95)},
            "spans_per_doc": {q: pct(spd, q) for q in (.05, .5, .95)},
            "label_counts": dict(lab_n),
            "unique_value_ratio": {k: round(len(lab_vals[k]) / max(1, lab_n[k]), 3) for k in LABELS},
            "top5_names_share": round(sum(c for _, c in toplang["human_name"].most_common(5)) / max(1, lab_n["human_name"]), 4),
            "top5_phone_share": round(sum(c for _, c in toplang["phone_number"].most_common(5)) / max(1, lab_n["phone_number"]), 4),
        }
        print(lang, L["docs"], flush=True)
    tot = Counter()
    for v in res["per_language"].values():
        for k, x in v.items():
            if isinstance(x, int): tot[k] += x
    res["total"] = dict(tot)
    res["generators"] = {m: dict(c, repair_rate=round(c["repaired"] / c["docs"], 4), bad_span_rate=round(c["bad_span"] / max(1, c["spans"]), 4))
                         for m, c in sorted(gen.items(), key=lambda kv: -kv[1]["docs"])}
    res["scenario_counts"] = scen.most_common(); res["document_type_count"] = len(doc_types)
    res["document_type_top"] = doc_types.most_common(15); res["format_count"] = len(fmts); res["format_top"] = fmts.most_common(15)
    json.dump(res, open(out, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(json.dumps(res["total"], indent=1))

if __name__ == "__main__":
    main(*sys.argv[1:4])
