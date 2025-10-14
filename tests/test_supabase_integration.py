"""Test Supabase integration and data persistence."""
from datetime import datetime, timezone

import pytest

from app.domain.schemas import ArticleRecord, EventRecord, ScoreRecord
from app.services.storage import StorageService


@pytest.mark.asyncio
async def test_supabase_article_upsert():
    """Test upserting articles to Supabase."""
    storage = StorageService()
    
    test_article = ArticleRecord(
        ticker="TSLA",
        url="https://example.com/test-article-1",
        title="Test TSLA Article",
        text="This is a test article about Tesla stock.",
        source="test-source",
        published_at=datetime.now(timezone.utc),
        canonical_hash="test-hash-123",
        user_id=1,
    )
    
    try:
        storage.upsert_articles([test_article])
        print("✅ Successfully upserted article to Supabase")
    except Exception as exc:
        pytest.fail(f"Failed to upsert article: {exc}")


@pytest.mark.asyncio
async def test_supabase_event_upsert():
    """Test upserting events to Supabase."""
    storage = StorageService()
    
    test_event = EventRecord(
        article_url="https://example.com/test-article-1",
        about_ticker=True,
        sentiment=0.5,
        stance="bullish",
        event_type="earnings",
        summary="Positive earnings report",
        user_id=1,
    )
    
    try:
        storage.upsert_events([test_event])
        print("✅ Successfully upserted event to Supabase")
    except Exception as exc:
        pytest.fail(f"Failed to upsert event: {exc}")


@pytest.mark.asyncio
async def test_supabase_score_upsert():
    """Test upserting scores to Supabase."""
    storage = StorageService()
    
    test_score = ScoreRecord(
        article_url="https://example.com/test-article-1",
        score=7,
        rationale="Positive sentiment and strong fundamentals",
        user_id=1,
    )
    
    try:
        storage.upsert_scores([test_score])
        print("✅ Successfully upserted score to Supabase")
    except Exception as exc:
        pytest.fail(f"Failed to upsert score: {exc}")


@pytest.mark.asyncio
async def test_supabase_full_workflow():
    """Test complete workflow with all three record types."""
    storage = StorageService()
    
    article = ArticleRecord(
        ticker="TSLA",
        url="https://example.com/test-workflow-article",
        title="Full Workflow Test Article",
        text="Testing the complete storage workflow.",
        source="test",
        published_at=datetime.now(timezone.utc),
        canonical_hash="workflow-hash-456",
        user_id=1,
    )
    
    event = EventRecord(
        article_url="https://example.com/test-workflow-article",
        about_ticker=True,
        sentiment=-0.3,
        stance="bearish",
        event_type="recall",
        summary="Test recall event",
        user_id=1,
    )
    
    score = ScoreRecord(
        article_url="https://example.com/test-workflow-article",
        score=3,
        rationale="Negative sentiment due to recall",
        user_id=1,
    )
    
    try:
        storage.upsert_articles([article])
        storage.upsert_events([event])
        storage.upsert_scores([score])
        print("✅ Successfully completed full workflow upsert")
    except Exception as exc:
        pytest.fail(f"Full workflow failed: {exc}")

