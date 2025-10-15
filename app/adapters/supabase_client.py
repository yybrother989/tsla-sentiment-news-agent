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
        
        # All tables now use url as the unique constraint
        response = self.client.table(table).upsert(payload, on_conflict="url").execute()
        
        if getattr(response, "error", None):
            raise SupabaseClientError(response.error.message)
        self.logger.debug("Upserted %d records into %s", len(payload), table)


__all__ = ["SupabaseAdapter", "SupabaseClientError"]

