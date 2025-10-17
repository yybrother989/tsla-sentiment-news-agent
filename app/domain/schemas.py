from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, PositiveInt


def canonical_hash(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


class PlannerBudget(BaseModel):
    max_runtime_minutes: PositiveInt = Field(default=8)
    max_documents: PositiveInt = Field(default=60)


class PlannerSource(BaseModel):
    kind: str
    url: Optional[HttpUrl] = None
    query: Optional[str] = None


class PlannerSources(BaseModel):
    filings: List[PlannerSource] = Field(default_factory=list)
    news: List[PlannerSource] = Field(default_factory=list)
    social: List[PlannerSource] = Field(default_factory=list)
    official: List[PlannerSource] = Field(default_factory=list)
    alternative: List[PlannerSource] = Field(default_factory=list)


class PlannerStopConditions(BaseModel):
    no_new_docs_after_sources: PositiveInt = Field(default=5)
    hard_time_cap_minutes: PositiveInt = Field(default=8)


class PlannerPlan(BaseModel):
    version: str
    ticker: str
    budget: PlannerBudget
    sources: PlannerSources
    query_terms: List[str]
    stop_conditions: PlannerStopConditions


class Article(BaseModel):
    ticker: str
    url: HttpUrl
    title: str
    text: str
    source: str
    published_at: datetime
    canonical_hash: str

    @classmethod
    def from_raw(
        cls,
        *,
        ticker: str,
        url: HttpUrl,
        title: str,
        text: str,
        source: str,
        published_at: datetime,
    ) -> "Article":
        return cls(
            ticker=ticker,
            url=url,
            title=title,
            text=text,
            source=source,
            published_at=published_at,
            canonical_hash=canonical_hash(str(url)),
        )


class ReasoningResult(BaseModel):
    about_ticker: bool = Field(default=True)
    sentiment: float = Field(ge=-1.0, le=1.0)
    stance: str
    event_type: Optional[str] = None
    summary_1liner: str


class Event(BaseModel):
    article_url: HttpUrl
    about_ticker: bool
    sentiment: float
    stance: str
    event_type: Optional[str]
    summary: str


class Score(BaseModel):
    article_url: HttpUrl
    score: PositiveInt = Field(ge=1, le=10)
    rationale: str


class FearGreedAggregate(BaseModel):
    ticker: str
    scores: List[int]

    def median(self) -> float:
        if not self.scores:
            raise ValueError("No scores to aggregate")
        sorted_scores = sorted(self.scores)
        length = len(sorted_scores)
        midpoint = length // 2
        if length % 2 == 0:
            return (sorted_scores[midpoint - 1] + sorted_scores[midpoint]) / 2
        return float(sorted_scores[midpoint])


class CollectorDocument(BaseModel):
    url: HttpUrl
    title: str
    text: str
    source: str
    published_at: datetime


class CollectorResult(BaseModel):
    documents: List[CollectorDocument]
    fetched_at: datetime
    errors: List[str] = Field(default_factory=list)


class ReasoningRequest(BaseModel):
    ticker: str
    documents: List[CollectorDocument]


class ReasoningResponse(BaseModel):
    document: CollectorDocument
    result: ReasoningResult


class ScoringRequest(BaseModel):
    ticker: str
    document: CollectorDocument
    reasoning: ReasoningResult


class ScoringResponse(BaseModel):
    document: CollectorDocument
    score: Score


class SupabaseRecord(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: int = Field(default=1)


class SentimentAnalysisRecord(SupabaseRecord):
    """Unified record combining article content and sentiment analysis."""
    
    # Article fields
    ticker: str
    url: str
    title: str
    text: str
    source: str
    published_at: datetime
    canonical_hash: str
    
    # Classification fields (optional until classified)
    category: Optional[str] = None
    classification_confidence: Optional[float] = None
    classification_rationale: Optional[str] = None
    
    # Enhanced sentiment analysis fields (optional until analysis is performed)
    sentiment_score: Optional[float] = None  # -1.0 to +1.0
    impact_score: Optional[int] = None  # 1-5
    sentiment_confidence: Optional[float] = None  # 0.0 to 1.0
    sentiment_rationale: Optional[str] = None
    key_factors: Optional[str] = None  # Comma-separated key factors
    
    # Legacy sentiment fields (for backward compatibility)
    sentiment: Optional[float] = None
    stance: Optional[str] = None
    event_type: Optional[str] = None
    summary: Optional[str] = None
    impact: Optional[int] = None
    impact_rationale: Optional[str] = None


# Legacy aliases for backward compatibility
ArticleRecord = SentimentAnalysisRecord
EventRecord = SentimentAnalysisRecord
ScoreRecord = SentimentAnalysisRecord


class TwitterTweet(BaseModel):
    """Normalized tweet payload returned by the Twitter adapter."""

    tweet_id: str
    tweet_url: HttpUrl
    conversation_id: str | None = None

    author_id: str | None = None
    author_handle: str | None = None
    author_name: str | None = None
    author_username: str | None = None

    text: str
    language: str | None = None
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)

    like_count: int | None = None
    reply_count: int | None = None
    retweet_count: int | None = None
    quote_count: int | None = None
    bookmark_count: int | None = None
    view_count: int | None = None

    posted_at: datetime
    collected_at: datetime

    raw_payload: Dict[str, Any] | None = None

    def to_collector_document(self) -> CollectorDocument:
        return CollectorDocument(
            url=self.tweet_url,
            title=f"Tweet by {self.author_handle or self.author_name or 'unknown'}",
            text=self.text,
            source="twitter",
            published_at=self.posted_at,
        )


class TwitterSentimentRecord(SupabaseRecord):
    """Database record for high-engagement Twitter sentiment analysis."""

    ticker: str
    tweet_id: str
    tweet_url: str
    conversation_id: str | None = None

    author_id: str | None = None
    author_handle: str | None = None
    author_name: str | None = None
    author_username: str | None = None

    text: str
    language: str | None = None
    hashtags: str | None = None
    mentions: str | None = None

    like_count: int | None = None
    reply_count: int | None = None
    retweet_count: int | None = None
    quote_count: int | None = None
    bookmark_count: int | None = None
    view_count: int | None = None

    posted_at: datetime
    collected_at: datetime | None = None

    sentiment_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    sentiment_label: str | None = None
    sentiment_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    sentiment_rationale: str | None = None
    key_themes: str | None = None
    sentiment_index: float | None = None
    notes: str | None = None

    raw_payload: Dict[str, Any] | None = None

    @classmethod
    def from_tweet(
        cls,
        *,
        tweet: TwitterTweet,
        ticker: str,
        sentiment_score: float | None = None,
        sentiment_label: str | None = None,
        sentiment_confidence: float | None = None,
        sentiment_rationale: str | None = None,
        key_themes: List[str] | None = None,
        sentiment_index: float | None = None,
        notes: str | None = None,
        user_id: int = 1,
    ) -> "TwitterSentimentRecord":
        return cls(
            ticker=ticker,
            user_id=user_id,
            tweet_id=tweet.tweet_id,
            tweet_url=str(tweet.tweet_url),
            conversation_id=tweet.conversation_id,
            author_id=tweet.author_id,
            author_handle=tweet.author_handle,
            author_name=tweet.author_name,
            author_username=tweet.author_username,
            text=tweet.text,
            language=tweet.language,
            hashtags=", ".join(tweet.hashtags) if tweet.hashtags else None,
            mentions=", ".join(tweet.mentions) if tweet.mentions else None,
            like_count=tweet.like_count,
            reply_count=tweet.reply_count,
            retweet_count=tweet.retweet_count,
            quote_count=tweet.quote_count,
            bookmark_count=tweet.bookmark_count,
            view_count=tweet.view_count,
            posted_at=tweet.posted_at,
            collected_at=tweet.collected_at,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            sentiment_confidence=sentiment_confidence,
            sentiment_rationale=sentiment_rationale,
            key_themes=", ".join(key_themes) if key_themes else None,
            sentiment_index=sentiment_index,
            notes=notes,
            raw_payload=tweet.raw_payload,
        )


class RedditPost(BaseModel):
    """Normalized Reddit post payload returned by the Reddit adapter."""

    post_id: str
    post_url: HttpUrl
    subreddit: str = "wallstreetbets"
    
    author_username: str | None = None
    title: str
    text: str | None = None
    flair: str | None = None
    
    upvote_count: int | None = None
    upvote_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    comment_count: int | None = None
    award_count: int | None = None
    
    is_pinned: bool = False
    is_locked: bool = False
    is_archived: bool = False
    
    posted_at: datetime
    collected_at: datetime
    raw_payload: Dict[str, Any] | None = None

    def to_collector_document(self) -> CollectorDocument:
        """Convert to CollectorDocument for sentiment analysis."""
        combined_text = self.title
        if self.text:
            combined_text += f"\n\n{self.text}"
        
        return CollectorDocument(
            url=self.post_url,
            title=self.title,
            text=combined_text,
            source="reddit",
            published_at=self.posted_at,
        )


class RedditSentimentRecord(SupabaseRecord):
    """Database record for high-engagement Reddit sentiment analysis."""
    
    ticker: str
    post_id: str
    post_url: str
    subreddit: str = "wallstreetbets"
    
    author_username: str | None = None
    title: str
    text: str | None = None
    flair: str | None = None
    
    upvote_count: int | None = None
    upvote_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    comment_count: int | None = None
    award_count: int | None = None
    
    is_pinned: bool = False
    is_locked: bool = False
    is_archived: bool = False
    
    posted_at: datetime
    collected_at: datetime | None = None
    
    sentiment_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    sentiment_label: str | None = None
    sentiment_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    sentiment_rationale: str | None = None
    key_themes: str | None = None
    sentiment_index: float | None = None
    
    notes: str | None = None
    raw_payload: Dict[str, Any] | None = None

    @classmethod
    def from_post(
        cls,
        *,
        post: RedditPost,
        ticker: str,
        sentiment_score: float | None = None,
        sentiment_label: str | None = None,
        sentiment_confidence: float | None = None,
        sentiment_rationale: str | None = None,
        key_themes: List[str] | None = None,
        sentiment_index: float | None = None,
        notes: str | None = None,
        user_id: int = 1,
    ) -> "RedditSentimentRecord":
        """Create a RedditSentimentRecord from a RedditPost and sentiment data."""
        return cls(
            ticker=ticker,
            user_id=user_id,
            post_id=post.post_id,
            post_url=str(post.post_url),
            subreddit=post.subreddit,
            author_username=post.author_username,
            title=post.title,
            text=post.text,
            flair=post.flair,
            upvote_count=post.upvote_count,
            upvote_ratio=post.upvote_ratio,
            comment_count=post.comment_count,
            award_count=post.award_count,
            is_pinned=post.is_pinned,
            is_locked=post.is_locked,
            is_archived=post.is_archived,
            posted_at=post.posted_at,
            collected_at=post.collected_at,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            sentiment_confidence=sentiment_confidence,
            sentiment_rationale=sentiment_rationale,
            key_themes=", ".join(key_themes) if key_themes else None,
            sentiment_index=sentiment_index,
            notes=notes,
            raw_payload=post.raw_payload,
        )


class LLMError(BaseModel):
    message: str
    payload: Optional[Dict[str, str]] = None


__all__ = [
    "Article",
    "ArticleRecord",
    "CollectorDocument",
    "CollectorResult",
    "Event",
    "EventRecord",
    "FearGreedAggregate",
    "LLMError",
    "PlannerBudget",
    "PlannerPlan",
    "PlannerSource",
    "PlannerSources",
    "PlannerStopConditions",
    "ReasoningRequest",
    "ReasoningResponse",
    "ReasoningResult",
    "RedditPost",
    "RedditSentimentRecord",
    "Score",
    "ScoreRecord",
    "ScoringRequest",
    "ScoringResponse",
    "SentimentAnalysisRecord",
    "SupabaseRecord",
    "TwitterTweet",
    "TwitterSentimentRecord",
    "canonical_hash",
]
