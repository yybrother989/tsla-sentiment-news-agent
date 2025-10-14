from datetime import datetime, timezone

from app.domain.schemas import Article, canonical_hash


def test_canonical_hash_consistency() -> None:
    url = "https://example.com/article"
    assert canonical_hash(url) == canonical_hash(url.upper())


def test_article_from_raw_sets_hash() -> None:
    article = Article.from_raw(
        ticker="TSLA",
        url="https://example.com/article",
        title="Tesla news",
        text="Sample content",
        source="Example",
        published_at=datetime.now(timezone.utc),
    )
    assert article.canonical_hash == canonical_hash("https://example.com/article")

