from __future__ import annotations

from typing import Iterable, List

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.domain.schemas import (
    CollectorDocument,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningResult,
)
from app.infra import get_logger, get_settings


class ReasoningError(RuntimeError):
    pass


class ReasoningProvider:
    async def reason_batch(self, request: ReasoningRequest) -> List[ReasoningResponse]:
        raise NotImplementedError


class DummyReasoningProvider(ReasoningProvider):
    async def reason_batch(self, request: ReasoningRequest) -> List[ReasoningResponse]:
        responses = []
        for document in request.documents:
            result = ReasoningResult(
                about_ticker=True,
                sentiment=0.0,
                stance="neutral",
                event_type=None,
                summary_1liner=document.title,
            )
            responses.append(ReasoningResponse(document=document, result=result))
        return responses


async def reason_documents(
    ticker: str, documents: Iterable[CollectorDocument]
) -> List[ReasoningResponse]:
    settings = get_settings()
    logger = get_logger(__name__)
    provider = DummyReasoningProvider()
    batch_size = settings.llm_batch_size

    responses: List[ReasoningResponse] = []
    docs = list(documents)

    for start in range(0, len(docs), batch_size):
        batch = docs[start : start + batch_size]
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(1),
            retry=retry_if_exception_type(ReasoningError),
            reraise=True,
        ):
            with attempt:
                request = ReasoningRequest(ticker=ticker, documents=batch)
                batch_responses = await provider.reason_batch(request)
                responses.extend(batch_responses)

    logger.info("Reasoned over %d documents", len(responses))
    return responses


__all__ = [
    "DummyReasoningProvider",
    "ReasoningError",
    "ReasoningProvider",
    "reason_documents",
]

