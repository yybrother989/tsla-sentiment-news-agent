from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import List

from browser_use import Agent, ChatOpenAI
from browser_use.browser.profile import BrowserProfile
from pydantic import BaseModel, Field

from app.domain.schemas import CollectorDocument, canonical_hash
from app.domain.validators import ensure_timezone
from app.infra import get_logger, get_settings


class NewsSourceError(RuntimeError):
    pass


class ExtractedArticle(BaseModel):
    """Structured output model for individual article extraction."""

    title: str = Field(description="Article headline")
    url: str = Field(description="Full article URL (https://...)")
    date_text: str = Field(description="Publication date or relative time (e.g., '2 hours ago')")
    summary: str = Field(description="Brief summary or excerpt")


class ArticleList(BaseModel):
    """Structured output model for multiple articles."""

    articles: List[ExtractedArticle] = Field(description="List of extracted articles")


class DuckDuckGoNewsSource:
    """DuckDuckGo search for Tesla news (bot-friendly aggregator)."""

    TICKER = "TSLA"

    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.settings = get_settings()

    def _get_time_filter_option(self, days: int) -> str:
        """Map days to DuckDuckGo time filter options."""
        if days <= 1:
            return "Past day"
        elif days <= 7:
            return "Past week"
        elif days <= 30:
            return "Past month"
        elif days <= 365:
            return "Past year"
        else:
            return "Any time"

    async def fetch_all_tesla_news(self, days: int = 7) -> List[CollectorDocument]:
        """Fetch all Tesla news via DuckDuckGo search."""
        
        time_filter = self._get_time_filter_option(days)
        
        task = f"""Search for "Tesla news" on DuckDuckGo and extract recent articles.

STEPS:
1. Use search action with query: "Tesla news"
2. Wait 3 seconds for results to load
3. Click on the "News" tab to filter to news results only
4. Click on "Any time" dropdown to open the time filter menu
5. Wait 1 second for dropdown to fully open
6. Click on "{time_filter}" option from the dropdown menu
7. Wait 2 seconds for time filter to apply
8. Use evaluate action to extract article URLs directly from DOM:
   ```javascript
   () => {{
     const articles = [];
     const results = document.querySelectorAll('article, .result');
     results.forEach((result, i) => {{
       if (i < 15) {{
         const link = result.querySelector('a[href*="http"]');
         const titleEl = result.querySelector('h2, h3, .result__title');
         const timeEl = result.querySelector('time, .result__timestamp');
         const snippetEl = result.querySelector('.result__snippet, p');
         
         if (link && titleEl) {{
           let url = link.getAttribute('href');
           // DuckDuckGo sometimes uses uddg= parameter with encoded URL
           if (url && url.includes('uddg=')) {{
             const match = url.match(/uddg=([^&]+)/);
             if (match) {{
               url = decodeURIComponent(match[1]);
             }}
           }}
           
           if (url && url.startsWith('http')) {{
             articles.push({{
               title: titleEl.textContent.trim(),
               url: url,
               date_text: timeEl?.textContent?.trim() || 'recent',
               summary: snippetEl?.textContent?.trim() || titleEl.textContent.trim()
             }});
           }}
         }}
       }}
     }});
     return JSON.stringify(articles);
   }}
   ```
9. If JavaScript extraction returns valid results, use those. Otherwise fall back to extract action.

CRITICAL EXTRACTION REQUIREMENTS:
- Use JavaScript evaluate to extract href attributes directly from DOM
- Parse DuckDuckGo's uddg= parameter to get real URLs
- ONLY include articles with valid http/https URLs
- Skip any DuckDuckGo redirect URLs
- For each valid article, extract:
  * title: article headline (required)
  * url: Direct article URL (required - must start with http)
  * date_text: publication date like "7 hours ago" or "recent"
  * summary: article excerpt or title

IMPORTANT:
- Extract at least 15 articles to account for some having invalid URLs
- The URL must be the ACTUAL destination URL, not a DuckDuckGo redirect
- Focus on articles from past {days} days
- Prefer credible news sources"""

        self.logger.info("Fetching Tesla news via DuckDuckGo (past %d days, using '%s' filter)", days, time_filter)

        try:
            profile = BrowserProfile(
                headless=False,
                disable_security=True,
                deterministic_rendering=False,
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                minimum_wait_page_load_time=0.5,
                wait_between_actions=0.3,
            )

            llm = ChatOpenAI(
                model=self.settings.planner_llm_model,
                api_key=self.settings.openai_api_key,
                temperature=0.0,
            )

            agent = Agent(
                task=task,
                llm=llm,
                browser_profile=profile,
                max_actions_per_step=15,
                output_model_schema=ArticleList,
                use_vision=False,
                max_failures=2,
            )

            result = await agent.run(max_steps=16)

            # Parse structured output
            documents = self._parse_result(result, days)

            self.logger.info("Retrieved %d articles via DuckDuckGo", len(documents))
            return documents

        except Exception as exc:
            self.logger.error("DuckDuckGo fetch failed: %s", exc, exc_info=True)
            raise NewsSourceError(f"Failed to fetch via DuckDuckGo: {exc}") from exc

    def _parse_result(self, result, days: int) -> List[CollectorDocument]:
        """Parse Browser-Use result into CollectorDocument objects."""
        documents: List[CollectorDocument] = []

        # Try multiple ways to find the article data
        article_list = None
        
        # Method 1: Check history.structured_output
        if hasattr(result, "history") and hasattr(result.history, "structured_output"):
            article_list = result.history.structured_output
            self.logger.info("✓ Found structured output in history")
        
        # Method 2: Check final_result()
        if not article_list and hasattr(result, "final_result"):
            try:
                final = result.final_result() if callable(result.final_result) else result.final_result
                if isinstance(final, ArticleList):
                    article_list = final
                    self.logger.info("✓ Found ArticleList in final_result")
                elif isinstance(final, dict) and "articles" in final:
                    article_list = ArticleList(**final)
                    self.logger.info("✓ Found dict in final_result, converted to ArticleList")
                elif isinstance(final, str):
                    # Try to parse JSON string
                    import json
                    try:
                        data = json.loads(final)
                        if "articles" in data:
                            article_list = ArticleList(**data)
                            self.logger.info("✓ Parsed JSON string from final_result")
                    except:
                        pass
            except Exception as exc:
                self.logger.debug("Could not parse final_result: %s", exc)
        
        if not article_list:
            self.logger.warning("❌ No structured output found")
            return documents
        
        if not article_list.articles:
            self.logger.warning("❌ ArticleList is empty")
            return documents
            
        self.logger.info("📰 Processing %d articles from DuckDuckGo", len(article_list.articles))
        
        for idx, article in enumerate(article_list.articles, 1):
            try:
                # Parse date
                published_at = self._parse_date(article.date_text)
                
                # Validate URL - skip if empty or invalid
                url = str(article.url).strip()
                if not url or not url.startswith("http") or len(url) < 10:
                    self.logger.debug("  [%d] Skipping article with invalid/empty URL: '%s'", idx, article.title[:40] if article.title else "No title")
                    continue
                
                # Skip if title is missing or placeholder
                if not article.title or article.title.strip() in ["", "N/A", "Not provided", "Not provided."]:
                    self.logger.debug("  [%d] Skipping article with missing title", idx)
                    continue
                
                # Use title as summary if missing
                summary = article.summary
                if not summary or summary in ["Not provided", "Not provided.", "N/A", ""]:
                    summary = article.title
                
                documents.append(
                    CollectorDocument(
                        url=url,
                        title=article.title,
                        text=summary,
                        source="duckduckgo",
                        published_at=ensure_timezone(published_at),
                    )
                )
                self.logger.info("  [%d] ✓ %s", idx, article.title[:60])
                
            except Exception as exc:
                self.logger.warning("  [%d] Failed to parse article: %s", idx, exc)
                continue
        
        return documents

    def _parse_date(self, date_text: str) -> datetime:
        """Parse date strings (relative or absolute) to datetime."""
        now = datetime.now(timezone.utc)
        date_lower = date_text.lower().strip()
        
        try:
            # Relative time
            if "hour" in date_lower or "hr" in date_lower:
                hours = int(''.join(filter(str.isdigit, date_text)))
                return now - timedelta(hours=hours)
            elif "day" in date_lower:
                days = int(''.join(filter(str.isdigit, date_text)))
                return now - timedelta(days=days)
            elif "week" in date_lower:
                weeks = int(''.join(filter(str.isdigit, date_text)))
                return now - timedelta(weeks=weeks)
            
            # Full date parsing
            try:
                from dateutil import parser
                parsed = parser.parse(date_text, fuzzy=True)
                return parsed.replace(tzinfo=timezone.utc)
            except:
                pass
                
        except (ValueError, IndexError):
            pass
        
        # Default to now
        return now


async def fetch_tesla_news(days: int = 7) -> List[CollectorDocument]:
    """
    Fetch Tesla news articles from DuckDuckGo for the specified time window.
    
    This is the main entry point for news collection.
    
    Note: Some article URLs may redirect to homepage due to paywall, article removal,
    or geo-restrictions. This is expected behavior from news sites.
    """
    source = DuckDuckGoNewsSource()
    return await source.fetch_all_tesla_news(days)


__all__ = [
    "DuckDuckGoNewsSource",
    "NewsSourceError",
    "fetch_tesla_news",
]
