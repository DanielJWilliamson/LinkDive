"""Simple in-memory token bucket rate limiter for external API calls."""
from __future__ import annotations
from time import time
from threading import RLock
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.database.models import RateLimitState
from config.settings import settings

class RateLimiter:
    """Persistent token bucket backed by DB state.

    Falls back to in-memory if DB unavailable.
    """
    def __init__(self, name: str, rate_per_minute: int, burst: int | None = None):
        self.name = name
        self.rate_per_minute = rate_per_minute
        self.capacity = burst or rate_per_minute
        self.tokens = float(self.capacity)
        self.updated = time()
        self._lock = RLock()
        self._load_state()

    def _db_session(self) -> Session:
        return SessionLocal()

    def _load_state(self):
        if not settings.enable_persistent_rate_limits:
            return
        try:
            db = self._db_session()
            state = db.query(RateLimitState).filter(RateLimitState.name == self.name).first()
            if state:
                self.tokens = float(state.tokens)
                self.rate_per_minute = state.rate_per_minute
                self.capacity = state.capacity
            else:
                db.add(RateLimitState(name=self.name, tokens=self.tokens, capacity=self.capacity, rate_per_minute=self.rate_per_minute))
                db.commit()
        except Exception:
            pass
        finally:
            try:
                db.close()
            except Exception:
                pass

    def _persist(self):
        if not settings.enable_persistent_rate_limits:
            return
        try:
            db = self._db_session()
            db.query(RateLimitState).filter(RateLimitState.name == self.name).update({
                'tokens': self.tokens,
                'rate_per_minute': self.rate_per_minute,
                'capacity': self.capacity,
            })
            db.commit()
        except Exception:
            pass
        finally:
            try:
                db.close()
            except Exception:
                pass

    def allow(self) -> bool:
        with self._lock:
            now = time()
            elapsed = now - self.updated
            refill = (self.rate_per_minute / 60.0) * elapsed
            if refill > 0:
                self.tokens = min(self.capacity, self.tokens + refill)
                self.updated = now
            if self.tokens >= 1:
                self.tokens -= 1
                self._persist()
                return True
            self._persist()
            return False

ahrefs_limiter = RateLimiter(name="ahrefs", rate_per_minute=30)
dataforseo_limiter = RateLimiter(name="dataforseo", rate_per_minute=30)