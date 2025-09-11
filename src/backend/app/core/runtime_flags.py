"""In-memory runtime feature flags and diagnostics.

Provides a thread-safe toggle for mock/live data usage and a small cache of
provider error notes to surface in the UI.
"""
from __future__ import annotations
from typing import Dict, Optional
from threading import RLock

from config.settings import settings


class _RuntimeFlags:
    def __init__(self):
        self._lock = RLock()
        # Initialize from settings (env-driven default)
        self._mock_mode: bool = bool(getattr(settings, "enable_mock_mode", True))
        # Keep last provider error notes keyed by provider name
        self._provider_errors: Dict[str, str] = {}

    # Mock mode
    def set_mock_mode(self, enabled: bool) -> None:
        with self._lock:
            self._mock_mode = bool(enabled)

    def is_mock_mode(self) -> bool:
        with self._lock:
            return self._mock_mode

    # Provider diagnostics
    def set_provider_error(self, provider: str, message: str) -> None:
        if not provider:
            return
        with self._lock:
            self._provider_errors[provider.lower()] = message.strip()

    def get_provider_errors(self) -> Dict[str, str]:
        with self._lock:
            # Return a shallow copy
            return dict(self._provider_errors)


# Singleton
runtime_flags = _RuntimeFlags()
