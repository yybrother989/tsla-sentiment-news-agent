from __future__ import annotations

from statistics import mean
from typing import Iterable, List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from app.domain.schemas import CollectorDocument, FearGreedAggregate, ReasoningResult
from app.domain.taxonomy import NewsCategory
from app.infra import get_logger, get_settings


class ScoringError(RuntimeError):
    pass


class SentimentResult(BaseModel):
    """Comprehensive sentiment analysis result."""
    
    sentiment: float = Field(ge=-1.0, le=1.0, description="Sentiment score from -1 (negative) to +1 (positive)")
    impact: int = Field(ge=1, le=5, description="Market impact score from 1 (low) to 5 (high)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the analysis from 0 to 1")
    rationale: str = Field(description="Brief explanation for the scores")
    key_factors: List[str] = Field(description="Key factors that influenced the scoring")
    summary: str = Field(description="One-sentence summary of the article")
    stance: str = Field(description="Overall stance: 'bullish', 'bearish', or 'neutral'")


class ImpactScore(BaseModel):
    """Legacy structured output for LLM impact scoring."""

    sentiment: float  # -1 to +1
    impact: int  # 1-5
    rationale: str


class SentimentAnalyzer:
    """Enhanced LLM-based sentiment analyzer with category-aware scoring."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0.0,
        ).with_structured_output(SentimentResult)
        self.logger = get_logger(__name__)

    def _get_category_context(self, category: str | None) -> str:
        """Get category-specific context for scoring."""
        if not category:
            return ""
        
        category_contexts = {
            "Financial & Operational": """
Focus on: Earnings, revenue, margins, deliveries, production numbers, financial performance
High impact factors: Quarterly results, delivery numbers, profit/loss, cost reductions
Sentiment indicators: Growth, profitability, operational efficiency, market share""",
            
            "Management & Governance": """
Focus on: Leadership changes, legal issues, board decisions, executive actions
High impact factors: CEO actions, lawsuits, governance changes, shareholder votes
Sentiment indicators: Leadership stability, legal outcomes, corporate governance""",
            
            "Product & Technology": """
Focus on: New features, software updates, product launches, technical innovations
High impact factors: Major product releases, technology breakthroughs, recalls
Sentiment indicators: Innovation, customer satisfaction, product quality, safety""",
            
            "Policy & Regulatory": """
Focus on: Government policies, regulations, subsidies, compliance issues
High impact factors: Regulatory changes, policy shifts, government support
Sentiment indicators: Regulatory support, compliance, policy benefits""",
            
            "Market & Sentiment": """
Focus on: Analyst ratings, investor sentiment, brand perception, market trends
High impact factors: Analyst upgrades/downgrades, market sentiment shifts
Sentiment indicators: Market confidence, brand value, investor perception""",
            
            "Strategic & Expansion": """
Focus on: Market expansion, partnerships, acquisitions, strategic initiatives
High impact factors: New markets, major partnerships, strategic pivots
Sentiment indicators: Growth opportunities, market expansion, strategic value""",
            
            "Macro & External": """
Focus on: Economic conditions, industry trends, external market factors
High impact factors: Economic indicators, industry disruptions, market conditions
Sentiment indicators: Economic environment, industry health, external factors"""
        }
        
        return category_contexts.get(category, "")

    async def analyze_article(
        self, document: CollectorDocument, category: str | None = None
    ) -> SentimentResult:
        """
        Perform comprehensive sentiment analysis on a Tesla news article.
        
        Returns:
            SentimentResult with sentiment, impact, confidence, rationale, and key factors
        """
        category_context = self._get_category_context(category)
        
        system_prompt = f"""You are an expert financial analyst specializing in Tesla stock analysis. 
Analyze Tesla news articles with precision and provide comprehensive sentiment scoring.

SCORING DIMENSIONS:

1. **Sentiment Score** (-1.0 to +1.0):
   - -1.0 to -0.6: Strongly negative (major threats, significant losses)
   - -0.6 to -0.3: Negative (concerns, risks, challenges)
   - -0.3 to +0.3: Neutral (mixed signals, routine updates)
   - +0.3 to +0.6: Positive (good news, improvements)
   - +0.6 to +1.0: Strongly positive (exceptional news, major wins)

2. **Market Impact Score** (1-5):
   - 1: Minimal impact (routine updates, minor mentions)
   - 2: Low impact (small operational changes, minor news)
   - 3: Moderate impact (quarterly results, product updates)
   - 4: High impact (major announcements, significant events)
   - 5: Critical impact (game-changing news, market-moving events)

3. **Confidence Score** (0.0 to 1.0):
   - 0.9-1.0: Very high confidence (clear, unambiguous news)
   - 0.7-0.9: High confidence (mostly clear with minor ambiguity)
   - 0.5-0.7: Moderate confidence (some uncertainty or mixed signals)
   - 0.3-0.5: Low confidence (unclear or conflicting information)
   - 0.0-0.3: Very low confidence (highly ambiguous or speculative)

ANALYSIS CONSIDERATIONS:
- Event significance and novelty
- Potential effect on Tesla's stock price and operations
- Market attention and media coverage level
- Historical precedent and comparable events
- Timing and market conditions
- Source credibility and reporting quality

{category_context}

Return a JSON object with:
- sentiment: float (-1.0 to +1.0)
- impact: integer (1-5)
- confidence: float (0.0 to 1.0)
- rationale: string (brief explanation of the sentiment and impact scores)
- key_factors: array of strings (3-5 key factors that influenced the scoring)
- summary: string (one-sentence summary of the article)
- stance: string ('bullish', 'bearish', or 'neutral' - overall market stance)"""

        user_prompt = f"""Analyze this Tesla news article:

**Title:** {document.title}
**Source:** {document.source}
**Published:** {document.published_at}
**Category:** {category or "Uncategorized"}

**Content:**
{document.text[:1000]}{"..." if len(document.text) > 1000 else ""}

Provide comprehensive analysis including:
1. Sentiment score (-1.0 to +1.0)
2. Market impact score (1-5)
3. Confidence level (0.0 to 1.0)
4. Rationale explaining both sentiment and impact
5. Key factors (3-5 items)
6. One-sentence summary of the article
7. Overall stance (bullish/bearish/neutral) for Tesla stock"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            result: SentimentResult = await self.llm.ainvoke(messages)
            
            # Validate and clamp values
            result.sentiment = max(-1.0, min(1.0, result.sentiment))
            result.impact = max(1, min(5, result.impact))
            result.confidence = max(0.0, min(1.0, result.confidence))
            
            self.logger.info(
                "Analyzed article '%s': sentiment=%.2f, impact=%d, confidence=%.2f",
                document.title[:50],
                result.sentiment,
                result.impact,
                result.confidence
            )
            
            return result

        except Exception as exc:
            self.logger.error("Sentiment analysis failed for '%s': %s", document.title, exc)
            raise ScoringError(f"Sentiment analysis failed: {exc}") from exc


class ImpactScorer:
    """Legacy LLM-based sentiment and impact scorer."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0.0,
        ).with_structured_output(ImpactScore)
        self.logger = get_logger(__name__)

    async def score(
        self, document: CollectorDocument, category: str | None = None
    ) -> Tuple[float, int, str]:
        """
        Score article sentiment and market impact.

        Returns:
            (sentiment, impact, rationale)
        """
        system_prompt = """You are a financial analyst scoring Tesla news articles.

Assess TWO dimensions:

1. **Sentiment** (-1 to +1):
   - -1.0 to -0.5: Strongly negative (major threats)
   - -0.5 to -0.2: Negative (concerns, risks)
   - -0.2 to +0.2: Neutral (mixed or routine)
   - +0.2 to +0.5: Positive (good news)
   - +0.5 to +1.0: Strongly positive (exceptional)

2. **Impact** (1-5):
   - 1: Minimal (routine updates, minor mentions)
   - 2: Low (small operational changes)
   - 3: Moderate (quarterly results, product updates)
   - 4: High (major announcements, significant events)
   - 5: Critical (game-changing news, market-moving events)

Consider:
- Event significance and novelty
- Potential effect on stock price
- Market attention and media coverage
- Historical precedent

Return JSON with sentiment (float), impact (1-5 integer), and rationale (brief explanation)."""

        category_context = f"\nCategory: {category}" if category else ""

        user_prompt = f"""Score this Tesla news article:

Title: {document.title}
Source: {document.source}
Published: {document.published_at}{category_context}

Content (first 800 chars):
{document.text[:800]}...

Provide sentiment score (-1 to +1) and impact score (1-5) with rationale."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            result: ImpactScore = await self.llm.ainvoke(messages)

            # Clamp values to valid ranges
            sentiment = max(-1.0, min(1.0, result.sentiment))
            impact = max(1, min(5, result.impact))

            return (sentiment, impact, result.rationale)

        except Exception as exc:
            self.logger.error("LLM impact scoring failed: %s", exc)
            raise ScoringError(f"Failed to generate impact score: {exc}") from exc


class DummyImpactScorer:
    """Fallback dummy scorer for testing."""

    async def score(
        self, document: CollectorDocument, category: str | None = None
    ) -> Tuple[float, int, str]:
        # Simple heuristic based on source
        if "reuters" in document.source.lower():
            return (0.1, 3, "Reuters article - moderate credibility")
        elif "teslarati" in document.source.lower():
            return (0.3, 2, "Teslarati article - Tesla-focused but lower impact")
        return (0.0, 2, "Unknown source - neutral assessment")


async def analyze_sentiment(
    document: CollectorDocument, category: str | None = None
) -> SentimentResult:
    """
    Perform comprehensive sentiment analysis on a Tesla news article.
    
    Returns:
        SentimentResult with sentiment, impact, confidence, rationale, and key factors
    """
    settings = get_settings()
    logger = get_logger(__name__)

    # Use enhanced sentiment analyzer if OpenAI key is configured
    if settings.openai_api_key:
        analyzer = SentimentAnalyzer(
            model=settings.planner_llm_model,
            api_key=settings.openai_api_key,
        )
    else:
        logger.warning("OpenAI API key not configured, using dummy sentiment analyzer")
        # Return dummy result
        return SentimentResult(
            sentiment=0.0,
            impact=2,
            confidence=0.3,
            rationale="Dummy analysis - OpenAI API key not configured",
            key_factors=["API key missing", "Dummy analysis", "No real scoring"],
            summary=document.title[:100],
            stance="neutral"
        )

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(ScoringError),
        reraise=True,
    ):
        with attempt:
            result = await analyzer.analyze_article(document, category)
            logger.info(
                "Analyzed document %s: sentiment=%.2f, impact=%d, confidence=%.2f",
                document.url,
                result.sentiment,
                result.impact,
                result.confidence,
            )
            return result

    raise ScoringError("Sentiment analysis failed after retries")


async def score_document_impact(
    document: CollectorDocument, category: str | None = None
) -> Tuple[float, int, str]:
    """
    Legacy function: Score document sentiment and impact.

    Returns:
        (sentiment, impact, rationale)
    """
    settings = get_settings()
    logger = get_logger(__name__)

    # Use LLM scorer if OpenAI key is configured
    if settings.openai_api_key:
        scorer = ImpactScorer(
            model=settings.planner_llm_model,
            api_key=settings.openai_api_key,
        )
    else:
        logger.warning("OpenAI API key not configured, using dummy impact scorer")
        scorer = DummyImpactScorer()

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(ScoringError),
        reraise=True,
    ):
        with attempt:
            sentiment, impact, rationale = await scorer.score(document, category)
            logger.info(
                "Scored document %s: sentiment=%.2f, impact=%d",
                document.url,
                sentiment,
                impact,
            )
            return (sentiment, impact, rationale)

    raise ScoringError("Impact scoring failed after retries")


def calculate_tsi(sentiment_scores: Iterable[float], impact_scores: Iterable[int]) -> float:
    """
    Calculate Tesla Sentiment Index (TSI).

    TSI = avg_sentiment × avg_impact

    Returns:
        TSI value (typically -5 to +5)
    """
    sentiments = list(sentiment_scores)
    impacts = list(impact_scores)

    if not sentiments or not impacts:
        return 0.0

    avg_sentiment = mean(sentiments)
    avg_impact = mean(impacts)

    return avg_sentiment * avg_impact


def aggregate_scores(ticker: str, scores: Iterable[int]) -> FearGreedAggregate:
    """Legacy function for backward compatibility."""
    return FearGreedAggregate(ticker=ticker, scores=list(scores))


async def score_document(
    document: CollectorDocument, reasoning_result: ReasoningResult
) -> FearGreedAggregate:
    """
    Legacy scoring function for backward compatibility with run_once.py.
    
    Returns FearGreedAggregate with a single score based on sentiment.
    """
    # Extract category from reasoning result if available
    category = None
    if hasattr(reasoning_result, 'event_type'):
        category = reasoning_result.event_type
    
    # Get sentiment and impact scores
    sentiment, impact, rationale = await score_document_impact(document, category)
    
    # Convert sentiment (-1 to +1) to fear-greed score (1-10)
    # -1 = 1 (extreme fear), 0 = 5.5 (neutral), +1 = 10 (extreme greed)
    fear_greed_score = int(((sentiment + 1) / 2) * 9 + 1)
    
    return FearGreedAggregate(
        ticker=document.url.split('/')[2] if '/' in document.url else "TSLA",
        scores=[fear_greed_score]
    )


__all__ = [
    "DummyImpactScorer",
    "ImpactScorer",
    "ImpactScore",
    "SentimentAnalyzer",
    "SentimentResult",
    "ScoringError",
    "aggregate_scores",
    "analyze_sentiment",
    "calculate_tsi",
    "score_document",
    "score_document_impact",
]
