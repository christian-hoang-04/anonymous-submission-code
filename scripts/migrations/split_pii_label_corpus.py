#!/usr/bin/env python
"""Split a Kaleido Labels JSONL bundle into no-leakage train/validation splits."""

from kaleidopii.training.bioes.data.splits import main

if __name__ == "__main__":
    main()
