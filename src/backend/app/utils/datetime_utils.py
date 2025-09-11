"""Timezone-aware datetime helpers.

Centralised helpers replacing scattered uses of naive ``datetime.utcnow()``.

Functions:
    utc_now() -> aware datetime in UTC
    iso_utc_now() -> ISO8601 string with explicit +00:00 offset
"""
from __future__ import annotations

from datetime import datetime, timezone

__all__ = ["utc_now", "iso_utc_now"]


def utc_now() -> datetime:
    """Return current UTC time as a timezone-aware datetime object."""
    return datetime.now(timezone.utc)


def iso_utc_now() -> str:
    """Return current UTC time as ISO8601 string with timezone offset."""
    return utc_now().isoformat()
