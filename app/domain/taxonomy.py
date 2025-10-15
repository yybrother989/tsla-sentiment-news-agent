from __future__ import annotations

from enum import Enum
from typing import Dict, List, Set


class NewsCategory(str, Enum):
    """Tesla news taxonomy with 7 primary categories."""

    FINANCIAL_OPERATIONAL = "Financial & Operational"
    PRODUCT_TECHNOLOGY = "Product & Technology"
    STRATEGIC_EXPANSION = "Strategic & Expansion"
    MANAGEMENT_GOVERNANCE = "Management & Governance"
    POLICY_REGULATORY = "Policy & Regulatory"
    MARKET_SENTIMENT = "Market & Sentiment"
    MACRO_EXTERNAL = "Macro & External"


# Keyword mapping for rule-based classification
CATEGORY_KEYWORDS: Dict[NewsCategory, Set[str]] = {
    NewsCategory.FINANCIAL_OPERATIONAL: {
        "earnings",
        "revenue",
        "profit",
        "margin",
        "delivery",
        "deliveries",
        "production",
        "sales",
        "pricing",
        "price cut",
        "cost",
        "capex",
        "cash flow",
        "guidance",
        "forecast",
        "q1",
        "q2",
        "q3",
        "q4",
        "quarterly",
        "annual",
    },
    NewsCategory.PRODUCT_TECHNOLOGY: {
        "model 3",
        "model y",
        "model s",
        "model x",
        "cybertruck",
        "roadster",
        "semi",
        "fsd",
        "autopilot",
        "autonomous",
        "self-driving",
        "battery",
        "4680",
        "powerwall",
        "megapack",
        "solar",
        "energy storage",
        "ai",
        "dojo",
        "optimus",
        "robot",
        "software",
        "update",
        "v12",
    },
    NewsCategory.STRATEGIC_EXPANSION: {
        "gigafactory",
        "factory",
        "plant",
        "expansion",
        "construction",
        "partnership",
        "deal",
        "agreement",
        "collaboration",
        "supply chain",
        "supplier",
        "market entry",
        "china",
        "europe",
        "india",
        "mexico",
        "texas",
        "berlin",
        "shanghai",
        "fremont",
    },
    NewsCategory.MANAGEMENT_GOVERNANCE: {
        "elon musk",
        "musk",
        "ceo",
        "cfo",
        "executive",
        "board",
        "director",
        "compensation",
        "lawsuit",
        "sec",
        "shareholder",
        "vote",
        "proxy",
        "stock split",
        "buyback",
        "dividend",
        "twitter",
        "x corp",
    },
    NewsCategory.POLICY_REGULATORY: {
        "recall",
        "investigation",
        "nhtsa",
        "safety",
        "crash",
        "accident",
        "regulation",
        "subsidy",
        "tax credit",
        "ira",
        "inflation reduction act",
        "environmental",
        "emissions",
        "carbon",
        "tariff",
        "trade",
        "policy",
        "government",
    },
    NewsCategory.MARKET_SENTIMENT: {
        "analyst",
        "rating",
        "upgrade",
        "downgrade",
        "price target",
        "buy",
        "sell",
        "hold",
        "outperform",
        "underperform",
        "investor",
        "institutional",
        "hedge fund",
        "short",
        "short interest",
        "options",
        "volatility",
        "momentum",
        "peer",
        "competitor",
        "vs",
        "comparison",
    },
    NewsCategory.MACRO_EXTERNAL: {
        "interest rate",
        "fed",
        "federal reserve",
        "inflation",
        "recession",
        "gdp",
        "unemployment",
        "commodity",
        "lithium",
        "nickel",
        "copper",
        "oil",
        "currency",
        "dollar",
        "yuan",
        "euro",
        "ev market",
        "electric vehicle",
        "ev sales",
        "global",
        "worldwide",
    },
}


def get_category_description(category: NewsCategory) -> str:
    """Get detailed description for each category."""
    descriptions = {
        NewsCategory.FINANCIAL_OPERATIONAL: "Earnings reports, delivery numbers, margins, pricing strategies, production costs, and financial guidance.",
        NewsCategory.PRODUCT_TECHNOLOGY: "New vehicle models, FSD/Autopilot updates, battery technology, energy products, AI/robotics, and software releases.",
        NewsCategory.STRATEGIC_EXPANSION: "Factory expansion, new market entry, partnerships, supply chain developments, and geographic growth.",
        NewsCategory.MANAGEMENT_GOVERNANCE: "Executive changes, Elon Musk statements, board decisions, lawsuits, shareholder actions, and corporate structure.",
        NewsCategory.POLICY_REGULATORY: "Vehicle recalls, safety investigations, government subsidies, environmental regulations, and trade policies.",
        NewsCategory.MARKET_SENTIMENT: "Analyst ratings, investor behavior, institutional holdings, short interest, and peer comparisons.",
        NewsCategory.MACRO_EXTERNAL: "Interest rates, commodity prices, currency movements, global EV trends, and macroeconomic factors.",
    }
    return descriptions.get(category, "")


def get_all_categories() -> List[NewsCategory]:
    """Return all available news categories."""
    return list(NewsCategory)


__all__ = [
    "CATEGORY_KEYWORDS",
    "NewsCategory",
    "get_all_categories",
    "get_category_description",
]

