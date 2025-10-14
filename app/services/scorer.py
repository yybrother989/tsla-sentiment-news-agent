from __future__ import annotations

from typing import Iterable

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.domain.schemas import (
    CollectorDocument,
    FearGreedAggregate,
    ReasoningResult,
    Score,
    ScoringRequest,
    ScoringResponse,
)
from app.infra import get_logger, get_settings


class ScoringError(RuntimeError):
    pass


class ScoringProvider:
    async def score(self, request: ScoringRequest) -> ScoringResponse:
        raise NotImplementedError


class DummyScoringProvider(ScoringProvider):
    async def score(self, request: ScoringRequest) -> ScoringResponse:
        base_score = 5
        if request.reasoning.sentiment > 0.2:
            base_score = 7
        elif request.reasoning.sentiment < -0.2:
            base_score = 3
        score = Score(article_url=request.document.url, score=base_score, rationale=request.reasoning.summary_1liner)
        return ScoringResponse(document=request.document, score=score)


async def score_document(document: CollectorDocument, reasoning: ReasoningResult) -> ScoringResponse:
    provider = DummyScoringProvider()
    settings = get_settings()
    logger = get_logger(__name__)

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(ScoringError),
        reraise=True,
    ):
        with attempt:
            request = ScoringRequest(ticker=settings.environment, document=document, reasoning=reasoning)
            response = await provider.score(request)
            logger.info("Scored document %s with %d", document.url, response.score.score)
            return response

    raise ScoringError("Score generation failed")


def aggregate_scores(ticker: str, scores: Iterable[int]) -> FearGreedAggregate:
    return FearGreedAggregate(ticker=ticker, scores=list(scores))


__all__ = [
    "DummyScoringProvider",
    "ScoringError",
    "ScoringProvider",
    "aggregate_scores",
    "score_document",
]

