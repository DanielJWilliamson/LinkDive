from fastapi.testclient import TestClient
from app.main import app
import types


class DummyLogger:
    def __init__(self):
        self.events = []
        self._ctx = {}

    def bind(self, **kwargs):
        # Merge bindings so later binds extend context
        self._ctx.update(kwargs)
        return self

    def info(self, event, **kwargs):  # mimic structlog API
        self.events.append({"event": event, **self._ctx, **kwargs})

    def exception(self, event, **kwargs):  # capture exceptions similarly
        self.events.append({"event": event, "level": "exception", **self._ctx, **kwargs})


def test_request_log_includes_user(monkeypatch):
    # Monkeypatch the middleware module's logger with our dummy capturing logger
    from app.middleware import logging_middleware
    dummy = DummyLogger()
    monkeypatch.setattr(logging_middleware, "logger", dummy)

    client = TestClient(app)
    r = client.get("/api/campaigns", headers={"X-User-Email": "tester@example.com"})
    assert r.status_code in (200, 404)

    # Find request.start or request.end event
    user_values = [e.get("user") for e in dummy.events if e.get("event") in ("request.start", "request.end")]
    assert "tester@example.com" in user_values, f"Captured events missing user: {dummy.events}"
