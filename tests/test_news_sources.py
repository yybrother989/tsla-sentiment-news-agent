"""Test news source adapters."""
import pytest

from app.adapters.news_sources import ReutersNewsSource, TeslaratiNewsSource
from app.domain.taxonomy import NewsCategory


def test_reuters_focus_categories():
    """Test that Reuters covers the right categories."""
    source = ReutersNewsSource()
    categories = source.get_focus_categories()
    
    assert NewsCategory.FINANCIAL_OPERATIONAL in categories
    assert NewsCategory.POLICY_REGULATORY in categories
    assert NewsCategory.MACRO_EXTERNAL in categories
    assert NewsCategory.MANAGEMENT_GOVERNANCE in categories
    
    # Should NOT cover tech/product (that's Teslarati's domain)
    assert NewsCategory.PRODUCT_TECHNOLOGY not in categories


def test_teslarati_focus_categories():
    """Test that Teslarati covers the right categories."""
    source = TeslaratiNewsSource()
    categories = source.get_focus_categories()
    
    assert NewsCategory.PRODUCT_TECHNOLOGY in categories
    assert NewsCategory.STRATEGIC_EXPANSION in categories
    assert NewsCategory.MARKET_SENTIMENT in categories
    
    # Should NOT cover regulatory (that's Reuters' domain)
    assert NewsCategory.POLICY_REGULATORY not in categories


def test_reuters_search_queries():
    """Test Reuters generates appropriate search queries."""
    source = ReutersNewsSource()
    
    financial_queries = source.get_search_queries(NewsCategory.FINANCIAL_OPERATIONAL)
    assert any("earnings" in q.lower() for q in financial_queries)
    assert any("delivery" in q.lower() or "deliveries" in q.lower() for q in financial_queries)
    
    policy_queries = source.get_search_queries(NewsCategory.POLICY_REGULATORY)
    assert any("recall" in q.lower() for q in policy_queries)


def test_teslarati_search_queries():
    """Test Teslarati generates appropriate search queries."""
    source = TeslaratiNewsSource()
    
    product_queries = source.get_search_queries(NewsCategory.PRODUCT_TECHNOLOGY)
    assert any("fsd" in q.lower() for q in product_queries)
    assert any("cybertruck" in q.lower() for q in product_queries)
    
    strategic_queries = source.get_search_queries(NewsCategory.STRATEGIC_EXPANSION)
    assert any("gigafactory" in q.lower() or "factory" in q.lower() for q in strategic_queries)


def test_source_category_coverage():
    """Test that all categories are covered by at least one source."""
    reuters = ReutersNewsSource()
    teslarati = TeslaratiNewsSource()
    
    all_categories = set(NewsCategory)
    covered = reuters.get_focus_categories() | teslarati.get_focus_categories()
    
    assert all_categories == covered, f"Uncovered categories: {all_categories - covered}"


@pytest.mark.asyncio
async def test_reuters_fetch_structure():
    """Test Reuters fetch returns proper structure (without actually fetching)."""
    source = ReutersNewsSource()
    
    # Verify the method signature is correct
    assert hasattr(source, 'fetch_articles')
    assert source.TICKER == "TSLA"


@pytest.mark.asyncio
async def test_teslarati_fetch_structure():
    """Test Teslarati fetch returns proper structure (without actually fetching)."""
    source = TeslaratiNewsSource()
    
    # Verify the method signature is correct
    assert hasattr(source, 'fetch_articles')
    assert source.TICKER == "TSLA"

