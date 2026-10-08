#!/usr/bin/env python
"""Build a mixed Kaleido Labels JSONL bundle: medical anchor plus general-domain PII."""

from kaleidopii.training.bioes.data.mixed_build import main

if __name__ == "__main__":
    main()
