"""In-memory metrics registry (lightweight) for Link Dive AI."""
from __future__ import annotations
from typing import Dict, Any
from threading import RLock
from time import time

class MetricsRegistry:
    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._timestamps: Dict[str, float] = {}
        self._lock = RLock()

    def inc(self, name: str, value: int = 1):
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float):
        with self._lock:
            self._gauges[name] = value

    def mark(self, name: str):
        with self._lock:
            self._timestamps[name] = time()

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timestamps": dict(self._timestamps)
            }

metrics = MetricsRegistry()