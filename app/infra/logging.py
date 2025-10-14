from __future__ import annotations

import logging
from logging.config import dictConfig
from typing import Optional

from rich.logging import RichHandler


def setup_logging(level: str = "INFO", rich_tracebacks: bool = True) -> None:
    """Configure application-wide logging."""

    handlers = [RichHandler(rich_tracebacks=rich_tracebacks)]

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "rich": {
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "rich": {
                    "class": "rich.logging.RichHandler",
                    "level": level,
                    "formatter": "rich",
                    "rich_tracebacks": rich_tracebacks,
                }
            },
            "root": {
                "level": level,
                "handlers": ["rich"],
            },
        }
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or "app")


__all__ = ["get_logger", "setup_logging"]
