"""Dump the label maps the evaluator applies (read-only import of the repository package) to JSON for the paper appendix.

usage: python export_mappings.py <repo>/src <out.json>
"""
import json, sys
import types
sys.modules.setdefault("fcntl", types.ModuleType("fcntl"))  # Unix-only import in opf_backend; irrelevant to the label map
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from kaleidopii.annotations import source_mapping as sm, label_aliases as la
from kaleidopii.eval_baseline.adapters import gliner2, lfm25_pii, opf, openmed
out = {
    "opf_fold": dict(opf.OPF_LABEL_FOLD),
    "gliner2_fold": dict(gliner2.GLINER2_LABEL_FOLD),
    "liquid_lfm25_fold": dict(lfm25_pii.LIQUID_LABEL_FOLD),
    "openmed_overrides": dict(openmed._OPENMED_OVERRIDES),
    "openmed_generic_alias_map": {k: v.strip("<>") for k, v in la.LABEL_MAP.items()},
    "dropped_generic_labels": sorted(la.INVALID_LABELS)[:60],
    "ai4privacy_source_map": dict(sm.AI4PRIVACY_LABEL_MAP),
    "nemotron_source_map": dict(sm.NEMOTRON_LABEL_MAP),
    "gretel_source_map": dict(sm.GRETEL_LABEL_MAP),
}
json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
print({k: len(v) for k, v in out.items()})
