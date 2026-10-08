#!/usr/bin/env python
"""Build PII Labels span JSONL plus migration audit sidecars."""

from pii.training.bioes.data.build_legacy_pii_label_corpus import main

if __name__ == "__main__":
    main()
