#!/usr/bin/env python
"""Split a PII Labels JSONL bundle into no-leakage train/validation splits."""

from pii.training.bioes.data.splits import main

if __name__ == "__main__":
    main()
