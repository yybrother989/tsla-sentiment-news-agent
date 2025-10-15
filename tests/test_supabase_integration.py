"""Test Supabase integration and data persistence."""
from datetime import datetime, timezone

import pytest

from app.domain.schemas import SentimentAnalysisRecord
from app.services.storage import StorageService


@pytest.mark.asyncio
async def test_supabase_basic_upsert():
    """Test upserting a basic article without sentiment analysis."""
    storage = StorageService()
    
    test_record = SentimentAnalysisRecord(
        ticker="TSLA",
        url="https://example.com/test-basic-article",
        title="Test TSLA Article",
        text="This is a test article about Tesla stock.",
        source="test-source",
        published_at=datetime.now(timezone.utc),
        canonical_hash="test-hash-basic",
        user_id=1,
    )
    
    try:
        storage.upsert_records([test_record])
        print("✅ Successfully upserted basic record to Supabase")
    except Exception as exc:
        pytest.fail(f"Failed to upsert basic record: {exc}")


@pytest.mark.asyncio
async def test_supabase_full_analysis_upsert():
    """Test upserting a complete record with sentiment analysis."""
    storage = StorageService()
    
    test_record = SentimentAnalysisRecord(
        ticker="TSLA",
        url="https://example.com/test-full-analysis",
        title="Full Analysis Test Article",
        text="Complete test article with sentiment data.",
        source="test-source",
        published_at=datetime.now(timezone.utc),
        canonical_hash="test-hash-full",
        sentiment=0.5,
        stance="bullish",
        event_type="earnings",
        summary="Positive earnings report",
        user_id=1,
    )
    
    try:
        storage.upsert_records([test_record])
        print("✅ Successfully upserted full analysis record to Supabase")
    except Exception as exc:
        pytest.fail(f"Failed to upsert full record: {exc}")


@pytest.mark.asyncio
async def test_supabase_update_existing():
    """Test updating an existing record with new sentiment data."""
    storage = StorageService()
    
    # First insert basic record
    basic_record = SentimentAnalysisRecord(
        ticker="TSLA",
        url="https://example.com/test-update-article",
        title="Update Test Article",
        text="Article that will be updated with sentiment.",
        source="test-source",
        published_at=datetime.now(timezone.utc),
        canonical_hash="test-hash-update",
        user_id=1,
    )
    
    # Then update with sentiment data
    updated_record = SentimentAnalysisRecord(
        ticker="TSLA",
        url="https://example.com/test-update-article",  # Same URL triggers upsert
        title="Update Test Article",
        text="Article that will be updated with sentiment.",
        source="test-source",
        published_at=datetime.now(timezone.utc),
        canonical_hash="test-hash-update",
        sentiment=-0.3,
        stance="bearish",
        event_type="recall",
        summary="Added sentiment analysis",
        user_id=1,
    )
    
    try:
        storage.upsert_records([basic_record])
        storage.upsert_records([updated_record])  # Should update, not create new
        print("✅ Successfully updated existing record with sentiment")
    except Exception as exc:
        pytest.fail(f"Failed to update record: {exc}")


@pytest.mark.asyncio
async def test_supabase_batch_upsert():
    """Test upserting multiple records in batch."""
    storage = StorageService()
    
    records = [
        SentimentAnalysisRecord(
            ticker="TSLA",
            url=f"https://example.com/test-batch-{i}",
            title=f"Batch Test Article {i}",
            text=f"Batch test content {i}",
            source="test-batch",
            published_at=datetime.now(timezone.utc),
            canonical_hash=f"test-hash-batch-{i}",
            sentiment=float(i * 0.2 - 0.5),
            stance="neutral",
            summary=f"Test article {i}",
            user_id=1,
        )
        for i in range(1, 4)
    ]
    
    try:
        storage.upsert_records(records)
        print(f"✅ Successfully batch upserted {len(records)} records")
    except Exception as exc:
        pytest.fail(f"Batch upsert failed: {exc}")
