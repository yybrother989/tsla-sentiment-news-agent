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
        
        # Articles table has unique constraint on url, so we can upsert
        if table == "articles":
            response = self.client.table(table).upsert(payload, on_conflict="url").execute()
        else:
            # Events and scores don't have unique constraints, so just insert
            # Duplicates will be handled by application logic
            response = self.client.table(table).insert(payload).execute()
        
        if getattr(response, "error", None):
            raise SupabaseClientError(response.error.message)
        self.logger.debug("Upserted %d records into %s", len(payload), table)


__all__ = ["SupabaseAdapter", "SupabaseClientError"]

