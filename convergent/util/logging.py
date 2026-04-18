"""structlog configuration for Convergent.

Phase 0: minimum configuration so the Statutory Mining bootstrap and
future modules have a consistent log interface. Log file lives at
``%APPDATA%\\Convergent\\convergent.log`` in production.
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stderr)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
