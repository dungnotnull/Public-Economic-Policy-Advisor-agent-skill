"""Structured, dependency-free logging for the skill runtime.

A thin wrapper around the stdlib ``logging`` module that emits JSON lines by
default (toggleable via ``Settings.log_format``). JSON logs are safe to ingest
into downstream observability pipelines without a third-party dependency.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

_FORMATTER_CACHE: dict[str, logging.Formatter] = {}


class JsonFormatter(logging.Formatter):
    """Render each log record as a single JSON object on one line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key in ("request_id", "route", "tool", "sub_advisor", "tokens", "event"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        # Attach any extra fields the caller supplied via ``extra=``.
        reserved = _LOGRECORD_RESERVED
        for key, value in record.__dict__.items():
            if key in reserved or key in payload:
                continue
            if key.startswith("_"):
                continue
            payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


# Standard ``LogRecord`` attribute names that must NOT be serialised as extra
# fields (they are either already promoted to top-level keys or are internal).
_LOGRECORD_RESERVED = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "asctime", "taskName",
})


class _PlainFormatter(logging.Formatter):
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"

    def __init__(self) -> None:
        super().__init__(fmt=self.fmt, datefmt="%Y-%m-%dT%H:%M:%S")


class StructuredLogger:
    """Convenience wrapper exposing context-aware ``with_context`` logging."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._context: dict[str, Any] = {}

    def with_context(self, **kwargs: Any) -> "StructuredLogger":
        clone = StructuredLogger(self._logger)
        clone._context = {**self._context, **kwargs}
        return clone

    def _emit(self, level: int, msg: str, **kwargs: Any) -> None:
        extra = {**self._context, **kwargs}
        self._logger.log(level, msg, extra=extra)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._emit(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._emit(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._emit(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._emit(logging.ERROR, msg, **kwargs)

    def exception(self, msg: str, **kwargs: Any) -> None:
        self._emit(logging.ERROR, msg, exc_info=True, **kwargs)


_CONFIGURED = False


def _configure_root(log_format: str, log_level: str) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(stream=sys.stderr)
    if log_format.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(_PlainFormatter())
    root = logging.getLogger("pepa")
    root.handlers[:] = [handler]
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str = "pepa", log_format: str = "json", log_level: str = "INFO") -> StructuredLogger:
    """Return a configured ``StructuredLogger``.

    The root handler is configured once; subsequent calls reuse it. The
    ``log_format`` / ``log_level`` arguments are honoured on first call and can
    be overridden later by re-running configuration through the settings.
    """
    _configure_root(log_format, log_level)
    return StructuredLogger(logging.getLogger(f"pepa.{name}"))
