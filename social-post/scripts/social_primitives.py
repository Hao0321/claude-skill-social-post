"""Stable domain primitives shared without importing the full schema engine."""

from __future__ import annotations

from datetime import datetime

PLATFORMS = ("facebook", "instagram", "youtube", "threads", "x")
PLATFORM_VALUES = frozenset(PLATFORMS)


def parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return parsed
