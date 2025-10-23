from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from supabase import Client, create_client

from app.infra import get_logger, get_settings


class SupabaseClientError(RuntimeError):
    pass


class SupabaseAdapter:
    def __init__(self, client: Client) -> None:
        self.client = client
        self.logger = get_logger(__name__)

    @staticmethod
    def default_adapter() -> "SupabaseAdapter":
        settings = get_settings()
        credentials = settings.supabase_credentials
        if not credentials:
            raise SupabaseClientError("Supabase credentials are not configured")
        client = create_client(credentials["url"], credentials["key"])
        return SupabaseAdapter(client)

    def upsert(self, table: str, records: Iterable[Dict[str, Any]]) -> None:
        payload = list(records)
        if not payload:
            return
        
        # Determine unique constraint column based on table
        conflict_column = {
            "sentiment_analysis": "url",
            "twitter_sentiment": "tweet_id",  # Twitter uses tweet_id as unique constraint
            "reddit_sentiment": "post_url",  # Reddit uses post_url instead of url
        }.get(table, "url")  # Default to "url" for other tables
        
        response = self.client.table(table).upsert(payload, on_conflict=conflict_column).execute()
        
        if getattr(response, "error", None):
            raise SupabaseClientError(response.error.message)
        self.logger.debug("Upserted %d records into %s (conflict: %s)", len(payload), table, conflict_column)


__all__ = ["SupabaseAdapter", "SupabaseClientError"]

