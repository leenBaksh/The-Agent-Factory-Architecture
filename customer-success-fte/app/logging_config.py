"""
Structured logging configuration using structlog.

Sets up:
  - JSON output for production / staging / CI environments
  - Pretty console output for interactive local development (TTY detected)
  - stdlib logging bridge — every logging.getLogger() call in the codebase is
    captured and formatted through the same structlog processor chain
  - contextvars integration — bind conversation_id / message_id / channel once
    at the start of a request or message processing; every log line in that
    scope automatically inherits those fields

Usage:
    from app.logging_config import configure_logging
    configure_logging()          # call once at process start (idempotent)

    # To bind request-scoped context (e.g. in the Kafka worker):
    import structlog
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        conversation_id="...", message_id="...", channel="web"
    )
"""

import logging
import sys
from typing import Any

import structlog

from app.config import get_settings

settings = get_settings()

# ── Custom processors ─────────────────────────────────────────────────────────


def _add_service(logger: Any, method: str, event_dict: dict) -> dict:
    """Inject a constant 'service' field into every log record."""
    event_dict.setdefault("service", "customer-success-fte")
    event_dict.setdefault("environment", settings.environment)
    return event_dict


# ── Configuration ─────────────────────────────────────────────────────────────

_configured = False


def configure_logging() -> None:
    """
    Configure structlog and install a stdlib logging bridge.

    Safe to call multiple times — configuration is applied only once.
    The bridge means that every call to logging.getLogger(__name__).info(...)
    throughout the codebase is automatically captured and emitted as a
    structured JSON log line (or pretty console output in dev mode).
    """
    global _configured
    if _configured:
        return

    # Use JSON in all non-interactive environments; pretty output for local dev
    use_json = not sys.stdout.isatty() or settings.environment != "development"

    # Processors applied to BOTH structlog-native and stdlib-bridged records
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_service,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.ExceptionRenderer(),
    ]

    renderer: Any = (
        structlog.processors.JSONRenderer()
        if use_json
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    # ── structlog-native logger pipeline ─────────────────────────────────────
    structlog.configure(
        processors=shared_processors
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ── stdlib bridge ─────────────────────────────────────────────────────────
    # ProcessorFormatter intercepts stdlib log records and routes them through
    # the same shared_processors, then applies the same renderer.
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level)

    _configured = True
