from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from app.adapters.browser_client import BrowserClient
from app.domain.schemas import Article, CollectorDocument, CollectorResult
from app.domain.validators import ensure_timezone
from app.infra import get_logger


async def collect_articles(plan) -> CollectorResult:
    logger = get_logger(__name__)
    client = BrowserClient()
    raw_docs = await client.fetch_documents(plan.model_dump())

    documents: List[CollectorDocument] = []
    seen_hashes = set()

    for doc in raw_docs:
        canonical = Article.from_raw(
            ticker=plan.ticker,
            url=doc.url,
            title=doc.title,
            text=doc.text,
            source=doc.source,
            published_at=ensure_timezone(doc.published_at),
        )
        if canonical.canonical_hash in seen_hashes:
            continue
        seen_hashes.add(canonical.canonical_hash)
        documents.append(doc)

    logger.info("Collected %d unique documents", len(documents))
    return CollectorResult(documents=documents, fetched_at=datetime.now(timezone.utc))


__all__ = ["collect_articles"]
