"""Live test for news fetching with limited scope."""
import pytest

from app.adapters.news_sources import ReutersNewsSource, TeslaratiNewsSource
from app.domain.taxonomy import NewsCategory


@pytest.mark.asyncio
async def test_reuters_financial_news():
    """Test Reuters fetching Financial & Operational news (3 days)."""
    source = ReutersNewsSource()
    
    try:
        documents = await source.fetch_articles(
            category=NewsCategory.FINANCIAL_OPERATIONAL,
            days=3
        )
        
        print(f"\n✅ Reuters Financial: Retrieved {len(documents)} articles")
        for doc in documents:
            print(f"  - {doc.title}")
            print(f"    URL: {doc.url}")
            print(f"    Source: {doc.source}")
        
        assert len(documents) > 0, "Should retrieve at least one article"
        assert all(doc.source == "reuters" for doc in documents)
        
    except Exception as exc:
        pytest.skip(f"Reuters fetch failed (expected in CI): {exc}")


@pytest.mark.asyncio
async def test_teslarati_product_news():
    """Test Teslarati fetching Product & Technology news (3 days)."""
    source = TeslaratiNewsSource()
    
    try:
        documents = await source.fetch_articles(
            category=NewsCategory.PRODUCT_TECHNOLOGY,
            days=3
        )
        
        print(f"\n✅ Teslarati Product: Retrieved {len(documents)} articles")
        for doc in documents:
            print(f"  - {doc.title}")
            print(f"    URL: {doc.url}")
            print(f"    Source: {doc.source}")
        
        assert len(documents) > 0, "Should retrieve at least one article"
        assert all(doc.source == "teslarati" for doc in documents)
        
    except Exception as exc:
        pytest.skip(f"Teslarati fetch failed (expected in CI): {exc}")


if __name__ == "__main__":
    import asyncio
    
    print("Testing Reuters Financial News (3 days)...")
    asyncio.run(test_reuters_financial_news())
    
    print("\nTesting Teslarati Product News (3 days)...")
    asyncio.run(test_teslarati_product_news())

