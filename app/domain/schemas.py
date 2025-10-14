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


class ArticleRecord(SupabaseRecord):
    ticker: str
    url: str
    title: str
    text: str
    source: str
    published_at: datetime
    canonical_hash: str


class EventRecord(SupabaseRecord):
    article_url: str
    about_ticker: bool
    sentiment: float
    stance: str
    event_type: Optional[str]
    summary: str


class ScoreRecord(SupabaseRecord):
    article_url: str
    score: int
    rationale: str


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
    "Score",
    "ScoreRecord",
    "ScoringRequest",
    "ScoringResponse",
    "SupabaseRecord",
    "canonical_hash",
]
