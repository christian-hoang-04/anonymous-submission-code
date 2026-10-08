# Anonymous code release

Code accompanying an anonymous double-blind submission: dataset generation, verification, a compact BIOES PII model and its evaluation.

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

**Author information:** omitted for double-blind review. The dataset and model are available through an anonymized link: `[ANONYMOUS-DATA-URL]`.

## Resources

| Resource | Link |
| --- | --- |
| Dataset and model (anonymous) | `[ANONYMOUS-DATA-URL]` |
| Analyses and evaluations | [`experiments/`](experiments/) |

## What the paper contributes

- **A large multilingual resource:** a one-million-row training table covering seventeen languages and nine PII labels. About 80% of the rows (799,306) are generated clinical-style documents; the remaining 20% are training-split rows of four public PII corpora. All text is synthetic or surrogate; no real patient record was used.
- **A fully documented generation pipeline:** attribute-conditioned prompts over 12 document types, 11 text formats, 12 scenarios and 13 surface perturbations, nine generator LLMs, and a deterministic verification and repair stage. The complete prompts, catalogues, checks and label maps are in the paper's appendices and in this repository.
- **A compact model and a broad evaluation:** a 350M-parameter BIOES token classifier reaches a mean exact-match micro-F1 of **0.827** on fifteen public benchmarks, against **0.658** for the strongest of four public systems, and is also evaluated on two human-annotated clinical-style corpora (GraSCCo_PHI, MEDDOCAN), with a data analysis (near-duplicates, train/evaluation overlap) and an explicit list of limitations.

These are paper-reported benchmark results, not a guarantee of safe deployment or regulatory compliance. The paper's Limitations section lists the known issues of the current release (no human adjudication, placeholder-like values and markup characters in parts of the data, one dominant scenario in the refined collection).

## Reproducing the added analyses

The scripts under [`experiments/`](experiments/) reproduce the real-text evaluation, the data audits and the alignment analysis reported in the paper. See [`experiments/README.md`](experiments/README.md). They need the dataset and model repositories (placeholder ids `anonymous-placeholder/...` must be replaced with the private repository ids) and, for the GPU runs, a Modal account.

## Repository structure

```text
src/pii/             Package implementation and CLI
src/pii/eval_baseline/
    baseline/                Shared evaluation harness and aggregation
    adapters/                Model adapters
    regex_release/           Regex release evaluation
    opf_benchmark/           OPF benchmark evaluation
    pii350_release/          PII350 release evaluation
tests/                       Automated tests
scripts/                     Generation, evaluation, migration, and reporting tools
examples/                    Small offline examples
docs/ARCHITECTURE.md         Codebase architecture guide
```

The publication release intentionally excludes review-workspace artifacts,
internal planning notes, temporary data, virtual environments, and local
execution caches. The dataset and trained model are not bundled in this Git
repository; follow the paper's release status and linked project artifacts for
those resources.

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pii labels
uv run pii validate examples/sample.inline.jsonl
uv run pii demo
```

The quick-start workflow is offline after dependencies are installed. It does
not require provider API keys, cloud credentials, or network access to validate
the bundled example.

The demo writes three local artifacts under its output directory:

- `plain.jsonl` - stripped clinical text;
- `spans.jsonl` - text with character-offset spans; and
- `report.json` - record, span, and label summary.

## Development and reproduction checks

Run the core checks with:

```bash
uv run pytest
uv run ruff check --config ruff-strict.toml .
uv run mypy src/pii
uv run basedpyright src/pii
```

Strict MyPy checks every module under `src/pii` with no MyPy exclusions. BasedPyright runs in standard mode across the same source and excludes only `.venv`.

The broader generation, evaluation, training, and reporting workflows are
implemented under `src/pii/` and `scripts/`. Their commands may require
large model artifacts, external datasets, GPU runtimes, or provider
credentials; the offline quick start is the minimal reproducibility path.

## Annotation format

PII uses inline annotations in the form `[value]<label>`:

```text
Patient [Nguyen Van A]<human_name> visited [Cho Ray Hospital]<company_name>
on [2024-03-15]<date>. Contact: [0901234567]<phone_number>.
```

The nine-label ontology is:

| Label | Scope |
| --- | --- |
| `address` | Street addresses, postal codes, coordinates, and care locations |
| `company_name` | Hospitals, clinics, departments, companies, and organizations |
| `date` | Person- or encounter-linked dates and datetimes |
| `email_address` | Email addresses |
| `human_name` | Patient, clinician, and other person names |
| `id_number` | Medical records, government IDs, passports, IPs, and account numbers |
| `phone_number` | Telephone and fax numbers |
| `private_url` | Access-bearing portal, result, signed, or private-record URLs |
| `secret` | Passwords, API keys, session tokens, cookies, PINs, and OTPs |

## Limitations and responsible use

The corpus is entirely synthetic. Deterministic gates enforce declared
structural and annotation requirements, but they do not directly measure the
semantic naturalness of every generated document. The evaluation focuses on
public benchmarks, the PII Benchmark and two human-annotated clinical-style corpora; evaluation on
appropriately governed real clinical records remains future work.

This project is a research resource, not a certification that clinical text is
safe to share. Any deployment in a regulated workflow requires local validation,
privacy review, audit controls, and human oversight.

## Citation

Citation information is omitted for double-blind review.

## License

Code in this repository is released under the
[Apache License 2.0](LICENSE). See [SECURITY.md](SECURITY.md) for responsible
vulnerability reporting.
