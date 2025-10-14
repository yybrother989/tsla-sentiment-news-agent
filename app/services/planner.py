from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.domain.schemas import PlannerPlan
from app.infra import get_logger, get_settings


class PlannerError(RuntimeError):
    pass


@dataclass
class PlannerSourceCandidate:
    kind: str
    identifier: str
    relevance: float

    def to_dict(self) -> Dict[str, str | float]:
        return {
            "kind": self.kind,
            "identifier": self.identifier,
            "relevance": self.relevance,
        }


class HybridPlanner:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger(__name__)

    async def build_plan(self, payload: Dict[str, Any]) -> PlannerPlan:
        request = {**self.settings.planner_payload_defaults(), **payload}
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(2),
            retry=retry_if_exception_type(PlannerError),
            reraise=True,
        ):
            with attempt:
                plan_dict = await self._build_plan_dict(request)
                return PlannerPlan.model_validate(plan_dict)
        raise PlannerError("Failed to build planner plan after retries")

    async def _build_plan_dict(self, request: Dict[str, Any]) -> Dict[str, Any]:
        ticker = request["ticker"]
        curated = self._curated_sources(ticker)
        llm_queries = await self._llm_queries(request)
        search_sources = self._search_sources(llm_queries)

        sources = {
            "filings": [s.to_dict() for s in curated if s.kind == "filing"],
            "news": [s.to_dict() for s in curated if s.kind == "news"],
            "social": [s.to_dict() for s in search_sources if s.kind == "social"],
            "official": [s.to_dict() for s in curated if s.kind == "official"],
            "alternative": [s.to_dict() for s in search_sources if s.kind == "alternative"],
        }

        query_terms: List[str] = [q["query"] for q in llm_queries]

        return {
            "version": "2.0",
            "ticker": ticker,
            "budget": {
                "max_runtime_minutes": self.settings.planner_timeout_minutes,
                "max_documents": self.settings.planner_max_documents,
            },
            "sources": sources,
            "query_terms": query_terms,
            "stop_conditions": {
                "no_new_docs_after_sources": request.get("no_new_docs_after_sources", 5),
                "hard_time_cap_minutes": self.settings.planner_timeout_minutes,
            },
        }

    def _curated_sources(self, ticker: str) -> List[PlannerSourceCandidate]:
        return [
            PlannerSourceCandidate("news", "https://www.reuters.com/markets/companies/tesla", 0.95),
            PlannerSourceCandidate("news", "https://www.bloomberg.com/companies/TSLA", 0.9),
            PlannerSourceCandidate(
                "filing", "https://www.sec.gov/cgi-bin/browse-edgar?CIK=0001318605", 0.85
            ),
            PlannerSourceCandidate("official", "https://ir.tesla.com/press-releases", 0.8),
        ]

    async def _llm_queries(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Placeholder LLM logic; will integrate actual model later.
        ticker = request["ticker"]
        return [
            {
                "source": "serpapi",
                "query": f"{ticker} deliveries guidance",
                "time_filter": "24h",
                "exclude": ["rumor", "opinion"],
            },
            {
                "source": "alpha_vantage",
                "query": ticker,
                "time_filter": "30d",
                "exclude": [],
            },
        ]

    def _search_sources(self, queries: Iterable[Dict[str, Any]]) -> List[PlannerSourceCandidate]:
        results: List[PlannerSourceCandidate] = []
        for item in queries:
            source_kind = "alternative"
            if item["source"] in {"reddit", "stocktwits"}:
                source_kind = "social"
            identifier = item["source"]
            results.append(PlannerSourceCandidate(source_kind, identifier, 0.7))
        return results


async def plan_sources(payload: Dict[str, Any]) -> PlannerPlan:
    planner = HybridPlanner()
    return await planner.build_plan(payload)


__all__ = ["HybridPlanner", "PlannerError", "plan_sources"]
