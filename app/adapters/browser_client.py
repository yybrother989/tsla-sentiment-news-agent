from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from browser_use import Agent, ChatOpenAI
from browser_use.browser.profile import BrowserProfile

from app.domain.schemas import CollectorDocument
from app.domain.validators import ensure_timezone
from app.infra import get_logger, get_settings


class BrowserClientError(RuntimeError):
    pass


class BrowserClient:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.settings = get_settings()

    async def fetch_documents(self, plan: Dict[str, Any]) -> List[CollectorDocument]:
        """Use Browser-Use Agent to fetch documents based on the plan."""
        ticker = plan.get("ticker", "UNKNOWN")
        sources = plan.get("sources", {})
        query_terms = plan.get("query_terms", [])

        # Build a simple task for the agent
        task = self._build_task(ticker, sources, query_terms)

        self.logger.info("Starting Browser-Use agent for ticker %s", ticker)

        try:
            # Create browser profile with stealth settings to evade bot detection
            profile = BrowserProfile(
                headless=False,  # Visible browser - harder to detect as bot
                disable_security=True,  # Disable security features that leak automation
                deterministic_rendering=False,  # Randomize rendering fingerprint
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            )

            # Use Browser-Use's native ChatOpenAI wrapper
            llm = ChatOpenAI(
                model=self.settings.planner_llm_model,
                api_key=self.settings.openai_api_key,
                temperature=0.0,
            )

            agent = Agent(
                task=task,
                llm=llm,
                browser_profile=profile,
                max_actions_per_step=10,
                max_failures=2,
            )

            # Run the agent
            result = await agent.run()

            # Parse result into documents
            documents = self._parse_agent_result(result, ticker)

            self.logger.info("Browser-Use agent collected %d documents", len(documents))
            return documents

        except Exception as exc:
            self.logger.error("Browser-Use agent failed: %s", exc, exc_info=True)
            # Fallback to stub mode
            self.logger.warning("Falling back to stub mode due to Browser-Use failure")
            return self._stub_documents(ticker)

    def _build_task(
        self, ticker: str, sources: Dict[str, Any], query_terms: List[str]
    ) -> str:
        """Construct a natural language task for the Browser-Use agent."""
        queries = ", ".join(query_terms[:3]) if query_terms else f"{ticker} news"
        return (
            f"Go to Google and search for '{ticker} news latest'. "
            f"Find the top 3 recent news articles about {ticker}. "
            f"For each article, extract: title, URL, and a brief summary. "
            f"Return the results."
        )

    def _parse_agent_result(
        self, result: Any, ticker: str
    ) -> List[CollectorDocument]:
        """Parse the agent's output into CollectorDocument objects."""
        documents: List[CollectorDocument] = []
        now = datetime.now(timezone.utc)

        # Browser-Use agent returns a history; extract final output
        if hasattr(result, "final_result") and callable(result.final_result):
            content = str(result.final_result())
        elif hasattr(result, "final_result"):
            content = str(result.final_result)
        else:
            content = str(result)

        # For now, create a single document from the agent's output
        # In production, you'd parse structured data or multiple results
        documents.append(
            CollectorDocument(
                url=f"https://browser-use-result.local/{ticker}",
                title=f"{ticker} Browser-Use Agent Result",
                text=content[:5000],  # Truncate to reasonable length
                source="browser-use-agent",
                published_at=ensure_timezone(now),
            )
        )

        return documents

    def _stub_documents(self, ticker: str) -> List[CollectorDocument]:
        """Return stub documents when Browser-Use fails."""
        now = datetime.now(timezone.utc)
        return [
            CollectorDocument(
                url=f"https://example.com/{ticker.lower()}-stub",
                title=f"{ticker} stub article",
                text=f"Stub content for {ticker} - Browser-Use integration pending.",
                source="stub-fallback",
                published_at=ensure_timezone(now),
            )
        ]


__all__ = ["BrowserClient", "BrowserClientError"]
