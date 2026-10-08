"""Defect / distribution audit of anonymous-placeholder/kaleidopii-mixed (the 1,000,000-row training table), grouped by source.

Same heuristics as audit_v2.py (documented there): markup-or-newline inside a span, over-long non-address spans,
U+FFFD, '555' and sequential-filler phones, canonical placeholder names, a tagged value left bare elsewhere in the same
document. Also document length / spans-per-document percentiles, label counts and unique-value ratios.
Runs on Modal (gated data). usage: python audit_mixed.py <work_dir> <out_json>
"""
import json, os, re, sys
from collections import Counter, defaultdict
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

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
CHECK = {"human_name", "id_number", "phone_number", "email_address"}
LONG_OK = {"address", "private_url", "secret", "company_name"}
SAMPLE = 200000  # reservoir for percentiles per group

def main(work, out):
    api = HfApi(); G = defaultdict(Counter); lens = defaultdict(list); spds = defaultdict(list)
    lab = defaultdict(Counter); vals = defaultdict(lambda: defaultdict(set)); lang = defaultdict(Counter)
    for fn in sorted(s.rfilename for s in api.dataset_info("anonymous-placeholder/kaleidopii-mixed").siblings if s.rfilename.startswith("data/train-")):
        p = hf_hub_download("anonymous-placeholder/kaleidopii-mixed", fn, repo_type="dataset", local_dir=work)
        for r in pq.read_table(p, columns=["text", "label", "info"]).to_pylist():
            g = r["info"].get("source_dataset") or "<EMPTY>"; c = G[g]; text = r["text"]; spans = r["label"] or []
            c["docs"] += 1; c["spans"] += len(spans); lens[g].append(len(text)); spds[g].append(len(spans))
            lang[g][r["info"].get("language_bucket") or r["info"].get("language") or "?"] += 1
            if "�" in text: c["docs_fffd"] += 1
            tagged = Counter(); markup_doc = False
            for s in spans:
                v = text[s["start"]:s["end"]]; cat = s["category"]; lab[g][cat] += 1; vals[g][cat].add(v)
                if v != s["text"]: c["offset_mismatch"] += 1
                if "[" in v or "]" in v or "\n" in v: c["markup_spans"] += 1; markup_doc = True
                if len(v) > 80 and cat not in LONG_OK: c["overlong_spans"] += 1
                if cat in CHECK and len(v) >= 4: tagged[(cat, v)] += 1
                if cat == "human_name" and v.strip().lower() in PLACEHOLDER_NAMES: c["placeholder_names"] += 1
                if cat == "phone_number":
                    c["phones"] += 1; d = re.sub(r"\D", "", v)
                    c["phones_555_loose"] += "555" in d; c["phones_nanp555"] += nanp555(d); c["phones_seq"] += bool(SEQ.search(d))
            c["docs_markup_span"] += markup_doc
            c["docs_bare_repeat"] += any(text.count(v) > n for (cat, v), n in tagged.items())
            c["docs_zero_spans"] += not spans
        os.remove(p); print(fn, {k: v["docs"] for k, v in G.items()}, flush=True)
    pc = lambda xs, q: sorted(xs)[min(len(xs) - 1, int(q * len(xs)))]  # noqa: E731
    res = {g: dict(c, len_chars={q: pc(lens[g], q) for q in (.05, .5, .95)}, spans_per_doc={q: pc(spds[g], q) for q in (.05, .5, .95)},
                   label_counts=dict(lab[g]), unique_value_ratio={k: round(len(v) / max(1, lab[g][k]), 3) for k, v in vals[g].items()},
                   languages=dict(lang[g])) for g, c in G.items()}
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)

if __name__ == "__main__":
    main(*sys.argv[1:3])
