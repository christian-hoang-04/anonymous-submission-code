"""Per-day generation usage tracking and HTML reporting."""

from __future__ import annotations

from kaleidopii.generation.usage.dashboard import render_usage_dashboard
from kaleidopii.generation.usage.records import (
    AccountUsage,
    ProviderLimits,
    ProviderRunStats,
    ProviderUsage,
    UsageRecord,
    UsageTotals,
    build_usage_record,
    decode_usage_record,
)
from kaleidopii.generation.usage.storage import write_usage_record

__all__ = [
    "AccountUsage",
    "ProviderLimits",
    "ProviderRunStats",
    "ProviderUsage",
    "UsageRecord",
    "UsageTotals",
    "build_usage_record",
    "decode_usage_record",
    "render_usage_dashboard",
    "write_usage_record",
]
