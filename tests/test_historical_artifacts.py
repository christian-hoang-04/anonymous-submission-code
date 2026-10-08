from __future__ import annotations

import pytest

from kaleidopii.historical_artifacts import (
    LEGACY_ADVERSARIAL_SOURCE,
    LEGACY_LABEL_POLICY,
    LEGACY_RECORD_ID_PREFIX,
    LEGACY_REPAIRED_REJECTS_DATASET_ID,
    LEGACY_SYNTHETIC_DATASET_IDS,
    legacy_audit_jsonl_locator,
    legacy_jsonl_locator,
    legacy_summary_json_locator,
)


def test_historical_wire_values_remain_exact() -> None:
    assert LEGACY_LABEL_POLICY == "anonymous9_bioes"
    assert LEGACY_RECORD_ID_PREFIX == "mimo_anonymous9_"
    assert LEGACY_ADVERSARIAL_SOURCE == "anonymous9.synthetic_adversarial"
    assert LEGACY_REPAIRED_REJECTS_DATASET_ID == "anonymous-placeholder/mimo-anonymous9-repaired-rejects"
    assert LEGACY_SYNTHETIC_DATASET_IDS == {
        "medical": "anonymous-placeholder/mimo-anonymous9-targeted-synthetic",
        "general": "anonymous-placeholder/mimo-anonymous9-general-synthetic",
        "code_logs": "anonymous-placeholder/mimo-anonymous9-code-log-synthetic",
        "mixed": "anonymous-placeholder/mimo-anonymous9-general-synthetic",
        "challenge": "anonymous-placeholder/mimo-anonymous9-adversarial-challenge",
    }


def test_historical_artifact_locators_remain_exact() -> None:
    assert legacy_jsonl_locator("train") == "train.anonymous9.jsonl"
    assert legacy_audit_jsonl_locator("train") == "train.anonymous9.audit.jsonl"
    assert legacy_summary_json_locator("train") == "train.anonymous9.summary.json"


def test_historical_dataset_identifiers_are_read_only() -> None:
    with pytest.raises(TypeError):
        # reason: the rejected write is the behaviour under test — this must stay a type error, and an
        # reason: annotation admitting it would delete the very property the assertion proves.
        LEGACY_SYNTHETIC_DATASET_IDS["new"] = "anonymous-placeholder/new"  # ty: ignore[invalid-assignment]
