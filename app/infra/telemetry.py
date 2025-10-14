from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from app.infra import get_logger


@contextmanager
def timed_span(name: str) -> Iterator[None]:
    logger = get_logger("telemetry")
    start = datetime.now(timezone.utc)
    logger.info("%s started", name)
    try:
        yield
    finally:
        end = datetime.now(timezone.utc)
        elapsed = (end - start).total_seconds()
        logger.info("%s completed in %.2fs", name, elapsed)


__all__ = ["timed_span"]
