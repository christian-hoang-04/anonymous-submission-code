#!/usr/bin/env python
"""Build Kaleido Labels span JSONL plus migration audit sidecars."""

from kaleidopii.training.bioes.data.build_legacy_pii_label_corpus import main

if __name__ == "__main__":
    main()
