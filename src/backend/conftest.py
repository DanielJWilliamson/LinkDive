"""Pytest configuration ensuring the backend root is on sys.path.

Some CI / execution contexts were failing to resolve the top-level
`app` package (ModuleNotFoundError). Adding an explicit path injection
keeps tests stable across environments.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest

from app.core.database import create_tables, drop_tables

BACKEND_ROOT = Path(__file__).parent.resolve()
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture(scope="session", autouse=True)
def _create_db_schema():
    """Automatically create (and later drop) DB schema for test session."""
    create_tables()
    yield
    # Optionally drop tables to keep workspace clean between runs
    try:
        drop_tables()
    except Exception:
        pass
