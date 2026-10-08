#!/usr/bin/env python
"""Build a mixed PII Labels JSONL bundle: medical anchor plus general-domain PII."""

from pii.training.bioes.data.mixed_build import main

if __name__ == "__main__":
    main()
