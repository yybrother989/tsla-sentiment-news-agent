from __future__ import annotations

from typing import Iterable

from app.adapters.supabase_client import SupabaseAdapter
from app.domain.schemas import SentimentAnalysisRecord
from app.infra import get_logger


class StorageService:
    def __init__(self, adapter: SupabaseAdapter | None = None) -> None:
        self.adapter = adapter or SupabaseAdapter.default_adapter()
        self.logger = get_logger(__name__)

    def upsert_records(self, records: Iterable[SentimentAnalysisRecord]) -> None:
        """Upsert sentiment analysis records to the unified table."""
        payload = [record.model_dump(mode="json", exclude_none=True) for record in records]
        self.adapter.upsert("sentiment_analysis", payload)
        self.logger.info("Upserted %d records to sentiment_analysis", len(payload))

    # Legacy methods for backward compatibility
    def upsert_articles(self, records: Iterable[SentimentAnalysisRecord]) -> None:
        self.upsert_records(records)

    def upsert_events(self, records: Iterable[SentimentAnalysisRecord]) -> None:
        self.upsert_records(records)

    def upsert_scores(self, records: Iterable[SentimentAnalysisRecord]) -> None:
        self.upsert_records(records)


__all__ = ["StorageService"]
