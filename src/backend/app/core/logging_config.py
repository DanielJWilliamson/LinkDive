"""Structured logging configuration for the application."""
from __future__ import annotations

import logging
import sys
import structlog
from datetime import datetime, timezone


def _iso_utc_ts(_: structlog.types.WrappedLogger, __: str, event_dict: dict) -> dict:
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def configure_logging(log_level: str = "INFO", json: bool = True) -> None:
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        _iso_utc_ts,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.processors.KeyValueRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level.upper(), logging.INFO)),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        stream=sys.stdout,
        format="%(message)s",
    )