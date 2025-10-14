from __future__ import annotations

from typing import Iterable

from app.adapters.supabase_client import SupabaseAdapter
from app.domain.schemas import ArticleRecord, EventRecord, ScoreRecord
from app.infra import get_logger


class StorageService:
    def __init__(self, adapter: SupabaseAdapter | None = None) -> None:
        self.adapter = adapter or SupabaseAdapter.default_adapter()
        self.logger = get_logger(__name__)

    def upsert_articles(self, records: Iterable[ArticleRecord]) -> None:
        payload = [record.model_dump(mode="json", exclude_none=True) for record in records]
        self.adapter.upsert("articles", payload)

    def upsert_events(self, records: Iterable[EventRecord]) -> None:
        payload = [record.model_dump(mode="json", exclude_none=True) for record in records]
        self.adapter.upsert("events", payload)

    def upsert_scores(self, records: Iterable[ScoreRecord]) -> None:
        payload = [record.model_dump(mode="json", exclude_none=True) for record in records]
        self.adapter.upsert("scores", payload)


__all__ = ["StorageService"]

