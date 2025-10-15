from __future__ import annotations

from typing import Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.domain.taxonomy import (
    CATEGORY_KEYWORDS,
    NewsCategory,
    get_all_categories,
    get_category_description,
)
from app.infra import get_logger, get_settings


class ClassificationError(RuntimeError):
    pass


class ClassificationResult(BaseModel):
    """Structured output for news classification."""

    category: str
    confidence: float  # 0-1
    rationale: str


class NewsClassifier:
    """Hybrid classifier using keyword matching + LLM fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.llm = None

    async def classify(
        self, title: str, text: str
    ) -> Tuple[NewsCategory, float, str]:
        """
        Classify news article into one of 7 categories.

        Returns:
            (category, confidence, rationale)
        """
        # Try keyword-based classification first
        keyword_result = self._classify_by_keywords(title, text)

        if keyword_result[1] >= 0.7:  # High confidence from keywords
            return keyword_result

        # Fall back to LLM for ambiguous cases
        return await self._classify_by_llm(title, text)

    def _classify_by_keywords(
        self, title: str, text: str
    ) -> Tuple[NewsCategory, float, str]:
        """Rule-based classification using keyword matching."""
        combined_text = f"{title} {text}".lower()

        category_scores: Dict[NewsCategory, int] = {cat: 0 for cat in get_all_categories()}

        # Count keyword matches per category
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    category_scores[category] += 1

        # Find best match
        best_category = max(category_scores, key=category_scores.get)
        best_score = category_scores[best_category]

        if best_score == 0:
            # No keywords matched
            return (
                NewsCategory.MARKET_SENTIMENT,
                0.3,
                "No clear keywords; defaulting to Market & Sentiment",
            )

        # Calculate confidence based on match strength
        total_matches = sum(category_scores.values())
        confidence = min(best_score / max(total_matches, 1), 0.95)

        rationale = f"Keyword matching: {best_score} relevant terms found"

        return (best_category, confidence, rationale)

    async def _classify_by_llm(
        self, title: str, text: str
    ) -> Tuple[NewsCategory, float, str]:
        """LLM-based classification for ambiguous cases."""
        if not self.llm:
            if not self.settings.openai_api_key:
                self.logger.warning(
                    "OpenAI key not configured; using low-confidence default"
                )
                return (NewsCategory.MARKET_SENTIMENT, 0.3, "LLM unavailable")

            self.llm = ChatOpenAI(
                model=self.settings.planner_llm_model,
                api_key=self.settings.openai_api_key,
                temperature=0.0,
            ).with_structured_output(ClassificationResult)

        categories_list = "\n".join(
            [
                f"- {cat.value}: {get_category_description(cat)}"
                for cat in get_all_categories()
            ]
        )

        system_prompt = f"""You are a financial news classifier. Classify Tesla news articles into one of these categories:

{categories_list}

Return JSON with: category (exact name from list), confidence (0-1), and rationale (brief explanation)."""

        user_prompt = f"""Classify this Tesla news article:

Title: {title}

Content (first 500 chars):
{text[:500]}...

Which category best fits this article?"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            result: ClassificationResult = await self.llm.ainvoke(messages)

            # Map LLM category string back to enum
            try:
                category = NewsCategory(result.category)
            except ValueError:
                # LLM returned invalid category, use keyword fallback
                self.logger.warning(
                    "LLM returned invalid category: %s", result.category
                )
                return self._classify_by_keywords(title, text)

            return (category, result.confidence, result.rationale)

        except Exception as exc:
            self.logger.error("LLM classification failed: %s", exc)
            raise ClassificationError(f"Classification failed: {exc}") from exc


__all__ = ["ClassificationError", "ClassificationResult", "NewsClassifier"]

