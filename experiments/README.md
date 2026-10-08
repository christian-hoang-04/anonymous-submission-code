# Experiments added in this version

All scripts are read-only with respect to the main package: the GPU runs mount `src/` and call the pinned evaluation adapters unchanged.
Dataset and model ids of the form `anonymous-placeholder/...` are placeholders; replace them with the private repository ids.

| Step | Script | Output (in `results/`) |
| --- | --- | --- |
| Convert GraSCCo_PHI and MEDDOCAN (CC BY 4.0, downloaded from Zenodo) to one JSONL format with the label mapping | `prep_data.py`, `mapping.py` | (local) |
| Run five systems on both corpora on Modal GPUs | `run_modal_eval.py --model {kaleido,openmed,gliner2,lfm25,opf}` | `predictions/*.json` (offsets and labels only) |
| Exact / relaxed / untyped F1, per label, bootstrap CIs | `score.py` | `scores/real_text_scores.json` |
| Error taxonomy, exploratory sensitivity analyses | `error_taxonomy.py`, `sensitivity_guideline.py`, `sensitivity_ladder.py` | `scores/*.json` |
| Audit of the refined collection (heuristics defined in the paper's Appendix G) | `audit_v2.py` | `v2_audit_train.json`, `v2_audit_eval.json` |
| Audit of the full one-million-row table by origin | `audit_mixed.py` via `modal_mixed.py` | `mixed_audit.json` |
| Document-level overlap between training table and all evaluation sets | `audit_overlap.py` via `modal_overlap.py` | `overlap_audit.json` |
| Entity-value overlap | `audit_entity_overlap.py` via `modal_entity_overlap.py` | `entity_overlap_audit.json` |
| Near-duplicates (MinHash-LSH, Jaccard >= 0.8) | `near_dup.py` | `near_dup_part*.json` |
| Label folds used for scoring | `export_mappings.py` | `ontology_mappings.json` |

The corpora themselves are not redistributed; the prediction files contain only character offsets and labels.
Note: `near_dup_part0.json` was transcribed from the console output of a serial run that was stopped for speed (same script and parameters).
