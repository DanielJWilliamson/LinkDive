"""Logging middleware adding request_id correlation and structured context.

This middleware:
 - Generates a unique request_id per incoming HTTP request (UUID4)
 - Binds request metadata (method, path) to structlog context
 - Measures latency and records status code
 - Propagates an existing X-Request-ID header if supplied
 - Adds the request_id to the response headers for client correlation

Lightweight and dependency free (aside from structlog) to avoid
introducing heavy APM agents at this stage.
"""
from __future__ import annotations

import time
import uuid
from typing import Callable
from datetime import datetime, timezone

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from app.core.metrics import metrics

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware providing per-request logging with correlation id."""

    async def dispatch(self, request: Request, call_next: Callable):  # type: ignore[override]
        start = time.perf_counter()
        # Reuse inbound header if present (avoid generating new IDs mid trace)
        inbound_id = request.headers.get("X-Request-ID")
        request_id = inbound_id or str(uuid.uuid4())

        # Bind context (structlog is thread/task local aware)
        user_email = request.headers.get("X-User-Email") or getattr(request.state, "user_email", None)
        log = logger.bind(request_id=request_id, method=request.method, path=request.url.path, user=user_email)
        log.info("request.start")

        try:
            response: Response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            metrics.inc("http_requests_total")
            metrics.inc("http_requests_error_total")
            log.exception("request.error", duration_ms=round(duration_ms, 2))
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        log.info(
            "request.end",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        metrics.inc("http_requests_total")
        if response.status_code >= 500:
            metrics.inc("http_requests_error_total")
        return response


def register_request_logging(app) -> None:
    """Helper to register middleware (keeps main.py lean)."""
    app.add_middleware(RequestLoggingMiddleware)
