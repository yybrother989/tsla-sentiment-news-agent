# Browser-Use Code Patterns Reference

> **For AI Assistants**: This file contains complete, copy-paste-ready code patterns for browser-use development. Reference these when generating code.

## Table of Contents
1. [Complete Adapter Template](#complete-adapter-template)
2. [Task Prompt Patterns](#task-prompt-patterns)
3. [Session Management](#session-management)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)

---

## Complete Adapter Template

```python
"""
{Platform} adapter for collecting posts/content.

This module provides functionality to:
- Authenticate and cache sessions
- Collect posts matching search criteria
- Extract structured data into domain models
"""

from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Sequence

from browser_use import Agent, ChatOpenAI
from browser_use.browser.profile import BrowserProfile
from pydantic import BaseModel, Field

from app.domain.schemas import {DomainModel}
from app.infra import get_logger, get_settings


class {Platform}CollectionError(RuntimeError):
    """Raised when {platform} collection fails."""
    pass


@dataclass
class {Platform}SearchConfig:
    """Configuration for {platform} search."""
    query: str
    since: str | None = None
    until: str | None = None
    min_engagement: int = 100
    lang: str = "en"
    target_count: int = 50
    max_scrolls: int = 5


class Extracted{Platform}Post(BaseModel):
    """Raw post data extracted from {platform}."""
    post_id: str
    post_url: str
    author_handle: str | None = None
    author_name: str | None = None
    text: str
    timestamp: str
    language: str | None = None
    like_count: int | None = None
    comment_count: int | None = None
    share_count: int | None = None
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    raw_json: dict | None = None


class {Platform}PostBatch(BaseModel):
    """Batch of posts from {platform}."""
    posts: List[Extracted{Platform}Post]


class {Platform}Collector:
    """Collects posts from {platform} using browser automation."""
    
    def __init__(self, config: {Platform}SearchConfig) -> None:
        self.config = config
        self.settings = get_settings()
        self.logger = get_logger(self.__class__.__name__)
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.session_cache = self.cache_dir / "{platform}_session.json"
    
    async def collect(self) -> Sequence[{DomainModel}]:
        """
        Collect posts from {platform}.
        
        Returns:
            Sequence of domain model objects
            
        Raises:
            {Platform}CollectionError: If collection fails
        """
        task = self._build_task_prompt()
        
        try:
            # Load cached session
            storage_state = self._load_session_cache()
            has_cache = storage_state is not None
            
            # Configure browser profile
            profile = BrowserProfile(
                headless=False,
                disable_security=True,
                deterministic_rendering=False,
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                minimum_wait_page_load_time=2.0,
                wait_between_actions=1.0,
                storage_state=storage_state,
                extra_chromium_args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                ],
            )
            
            # Initialize LLM
            llm = ChatOpenAI(
                model=self.settings.planner_llm_model,
                api_key=self.settings.openai_api_key,
                temperature=0.0,
            )
            
            # Adjust parameters based on cache
            max_steps = 15 if has_cache else 25
            max_actions = 12 if has_cache else 18
            use_vision = not has_cache
            
            # Create agent
            agent = Agent(
                task=task,
                llm=llm,
                browser_profile=profile,
                max_actions_per_step=max_actions,
                output_model_schema={Platform}PostBatch,
                use_vision=use_vision,
                max_failures=3,
            )
            
            self.logger.info("Starting {platform} collection (cached: %s)", has_cache)
            result = await agent.run(max_steps=max_steps)
            
            # Save session state
            await self._save_session_cache(profile)
            
            # Parse results
            posts = self._parse_result(result)
            self.logger.info("Collected %d posts from {platform}", len(posts))
            return posts
            
        except Exception as exc:
            self.logger.error("{Platform} collection failed: %s", exc, exc_info=True)
            raise {Platform}CollectionError(
                f"Failed to collect {platform} posts: {exc}\n"
                f"Tip: Ensure Chrome is installed and path is correct.\n"
                f"Tip: Try with --clear-cache if session is corrupted."
            ) from exc
    
    def _build_task_prompt(self) -> str:
        """Build structured task prompt for the agent."""
        has_cache = self._load_session_cache() is not None
        
        # Conditional login instructions
        if has_cache:
            login_block = """
STEP 1: Check Authentication
- Go to https://{platform}.com/
- Check if already logged in (look for profile icon)
- If logged in, proceed to STEP 2
- If not logged in, authentication required
"""
        else:
            # Add actual login instructions if needed
            login_block = """
STEP 1: Navigate to Platform
- Go to https://{platform}.com/
- You may need to login (handle as needed)
- Wait for main interface to load
"""
        
        # Build search URL
        query_encoded = urllib.parse.quote(self.config.query)
        search_url = f"https://{platform}.com/search?q={query_encoded}"
        
        return f"""
You are a {platform} data collector. Collect posts about "{self.config.query}".

CRITICAL RULES:
- Stay on {platform}.com ONLY - do NOT use search engines
- Verify URL contains "{platform}.com" before proceeding
- If page is empty, WAIT 10 seconds and retry - do NOT navigate away
- Stop after {self.config.max_scrolls} scrolls OR {self.config.target_count} posts

{login_block}

STEP 2: Navigate to Search
- Go DIRECTLY to: {search_url}
- This URL has the search query pre-filled
- Wait 5 seconds for results to load
- Verify you see search results

STEP 3: Verify Correct Page
- Check URL contains "{platform}.com"
- Confirm you see post results (not error page)

STEP 4: Collect Posts
- Scroll down slowly {self.config.max_scrolls} times
- Wait 4 seconds between each scroll for content to load
- Stop early if you have {self.config.target_count} unique posts

STEP 5: Extract Post Data
For each post visible on the page, extract:
- post_id: Unique identifier (from URL or generate one)
- post_url: Full URL (MUST start with https://{platform}.com/)
- author_handle: Username/handle
- author_name: Display name
- text: Full post content
- timestamp: When posted (e.g., "2h ago", "Yesterday")
- language: "{self.config.lang}" for English posts
- like_count: Number of likes/reactions
- comment_count: Number of comments
- share_count: Number of shares/reposts
- hashtags: Array of hashtag texts (without #)
- mentions: Array of @mentioned usernames (without @)

WHAT TO SKIP:
- Promoted/sponsored posts
- Posts you already collected (deduplicate by URL)
- Posts without valid URLs
- Advertisements

FINAL OUTPUT:
Return JSON in this exact format: {{"posts": [...]}}
Each post must have at minimum: post_id, post_url, text, timestamp
"""
    
    def _parse_result(self, result) -> Sequence[{DomainModel}]:
        """Parse agent result into domain models."""
        raw_batch: {Platform}PostBatch | None = None
        
        # Try multiple extraction methods
        if hasattr(result, 'history') and getattr(result.history, 'structured_output', None):
            candidate = result.history.structured_output
            if isinstance(candidate, {Platform}PostBatch):
                raw_batch = candidate
        
        if raw_batch is None and hasattr(result, 'final_result'):
            final_value = result.final_result() if callable(result.final_result) else result.final_result
            if isinstance(final_value, {Platform}PostBatch):
                raw_batch = final_value
            elif isinstance(final_value, dict) and 'posts' in final_value:
                raw_batch = {Platform}PostBatch(**final_value)
        
        if raw_batch is None:
            self.logger.warning("No structured posts returned from agent")
            return []
        
        # Parse and validate
        parsed: list[{DomainModel}] = []
        seen_ids: set[str] = set()
        
        for idx, post in enumerate(raw_batch.posts, start=1):
            try:
                # Validate required fields
                if not post.post_url or not post.post_url.startswith("http"):
                    self.logger.debug("Skipping post %d: invalid URL", idx)
                    continue
                
                if post.post_id in seen_ids:
                    self.logger.debug("Skipping post %s: duplicate", post.post_id)
                    continue
                
                # Parse timestamp
                posted_at = self._parse_timestamp(post.timestamp)
                if posted_at is None:
                    self.logger.debug("Skipping post %s: invalid timestamp", post.post_id)
                    continue
                
                # Create domain model
                parsed.append(
                    {DomainModel}(
                        post_id=post.post_id,
                        post_url=post.post_url,
                        author_handle=post.author_handle,
                        author_name=post.author_name,
                        text=post.text,
                        language=post.language,
                        hashtags=post.hashtags,
                        mentions=post.mentions,
                        like_count=post.like_count,
                        comment_count=post.comment_count,
                        share_count=post.share_count,
                        posted_at=posted_at,
                        collected_at=datetime.now(timezone.utc),
                        raw_payload=post.raw_json,
                    )
                )
                seen_ids.add(post.post_id)
                
            except Exception as exc:
                self.logger.debug("Failed to parse post %s: %s", post.post_id, exc)
                continue
        
        self.logger.info("Parsed %d/%d posts", len(parsed), len(raw_batch.posts))
        return parsed
    
    def _parse_timestamp(self, timestamp: str | None) -> datetime | None:
        """Parse relative timestamps into datetime objects."""
        if not timestamp:
            return None
        
        ts = timestamp.strip().lower()
        now = datetime.now(timezone.utc)
        
        try:
            # Handle relative times
            if 's' in ts and any(ch.isdigit() for ch in ts):
                seconds = int(''.join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(seconds=seconds)
            if 'min' in ts or ('m' in ts and 'mo' not in ts):
                minutes = int(''.join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(minutes=minutes)
            if 'hour' in ts or 'hr' in ts or 'h' in ts:
                hours = int(''.join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(hours=hours)
            if 'day' in ts or 'd' in ts:
                days = int(''.join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(days=days)
            if 'week' in ts or 'wk' in ts or 'w' in ts:
                weeks = int(''.join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(weeks=weeks)
            
            # Try ISO format
            from dateutil import parser
            parsed = parser.parse(ts)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
            
        except Exception:
            return None
    
    def _load_session_cache(self) -> dict | None:
        """Load cached session state if available and not expired."""
        if not self.session_cache.exists():
            self.logger.info("No cached session found")
            return None
        
        try:
            with open(self.session_cache, 'r') as f:
                cache_data = json.load(f)
            
            # Check expiration (24 hours)
            cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
            if datetime.now() - cache_time > timedelta(hours=24):
                self.logger.info("Session cache expired (>24 hours)")
                self.session_cache.unlink()
                return None
            
            # Validate structure
            storage_state = cache_data.get('storage_state')
            if not storage_state or not isinstance(storage_state, dict):
                self.logger.warning("Invalid session cache structure")
                self.session_cache.unlink()
                return None
            
            expires_in = cache_time + timedelta(hours=24) - datetime.now()
            self.logger.info("Loaded cached session (expires in %s)", expires_in)
            return storage_state
            
        except Exception as exc:
            self.logger.warning("Failed to load session cache: %s", exc)
            if self.session_cache.exists():
                self.session_cache.unlink()
            return None
    
    async def _save_session_cache(self, profile: BrowserProfile) -> None:
        """Save current session state to cache."""
        try:
            if hasattr(profile, 'browser') and profile.browser:
                context = profile.browser.contexts[0] if profile.browser.contexts else None
                if context:
                    storage_state = await context.storage_state()
                    
                    cache_data = {
                        'timestamp': datetime.now().isoformat(),
                        'storage_state': storage_state
                    }
                    
                    with open(self.session_cache, 'w') as f:
                        json.dump(cache_data, f, indent=2)
                    
                    self.logger.info("Saved session cache to %s", self.session_cache)
                    
        except Exception as exc:
            self.logger.warning("Failed to save session cache: %s", exc)


async def fetch_{platform}_posts(config: {Platform}SearchConfig) -> Sequence[{DomainModel}]:
    """
    Convenience function to fetch {platform} posts.
    
    Args:
        config: Search configuration
        
    Returns:
        Sequence of domain model objects
    """
    collector = {Platform}Collector(config)
    return await collector.collect()


__all__ = [
    "{Platform}CollectionError",
    "{Platform}SearchConfig",
    "{Platform}Collector",
    "fetch_{platform}_posts",
]
```

---

## Task Prompt Patterns

### Pattern 1: Authenticated Social Media
```python
task = f"""
You are a {platform} data collector. Collect posts about "{query}".

CRITICAL RULES:
- Stay on {platform}.com ONLY
- Do NOT use search engines like Google or DuckDuckGo
- If you see an empty page, WAIT 10 seconds and retry
- You have authenticated cookies loaded
- Stop after {max_scrolls} scrolls OR {target_count} items

STEP 1: Navigate to Search
- Go DIRECTLY to: https://{platform}.com/search?q={query_encoded}&filters=...
- This URL has the query pre-filled
- Wait 10 seconds for page to load
- If page is empty, wait another 10 seconds and refresh

STEP 2: Verify Correct Page
- Check URL contains "{platform}.com"
- If you're on ANY other domain, STOP and navigate back
- Confirm you see post results

STEP 3: Collect Posts
- Scroll down {max_scrolls} times
- Wait 4 seconds between each scroll
- Stop early if you have {target_count} unique posts

STEP 4: Extract Data
[Detailed extraction instructions matching Pydantic schema]

FINAL OUTPUT:
JSON format: {{"posts": [...]}}
"""
```

### Pattern 2: Guest-Accessible Site (No Login)
```python
task = f"""
You are a {platform} data collector. Collect posts about "{query}".

NO LOGIN REQUIRED - {platform} allows guest browsing.

CRITICAL RULES:
- Go DIRECTLY to {platform}.com (no login needed)
- Do NOT navigate away from {platform}.com
- Stop after {max_scrolls} scrolls

STEP 1: Navigate to Subreddit/Category
- Go to: https://{platform}.com/{category}?sort={sort}&t={time_filter}
- Wait for posts to load

STEP 2: Filter Content
- Look for posts mentioning "{query}" in title or body
- Posts must have:
  - At least {min_upvotes} upvotes
  - At least {min_comments} comments

STEP 3: Scroll and Collect
- Scroll {max_scrolls} times
- Wait 3 seconds between scrolls

STEP 4: Extract Data
[Extraction instructions]

FINAL OUTPUT:
{{"posts": [...]}}
"""
```

### Pattern 3: E-commerce / Product Sites
```python
task = f"""
Search for "{product_query}" on {site}.com and extract product data.

STEP 1: Navigate to Search
- Go to: https://{site}.com/s?k={query_encoded}
- Wait for search results

STEP 2: Filter Results
- Look for products with:
  - Rating >= {min_rating} stars
  - Price between ${min_price} and ${max_price}
  - In stock status

STEP 3: Collect Products
- Extract first {target_count} products

STEP 4: Extract Product Data
For each product:
- product_id: Unique identifier
- title: Product name
- price: Current price (float)
- original_price: Original price if on sale
- rating: Average rating (float)
- review_count: Number of reviews
- availability: "in stock" | "out of stock"
- url: Product page URL

FINAL OUTPUT:
{{"products": [...]}}
"""
```

---

## Data Models

### Social Media Post Model
```python
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class ExtractedPost(BaseModel):
    """Raw post data from browser extraction."""
    post_id: str = Field(description="Unique post identifier")
    post_url: str = Field(description="Full URL to post")
    author_handle: str | None = Field(None, description="Username/handle")
    author_name: str | None = Field(None, description="Display name")
    text: str = Field(description="Post content")
    timestamp: str = Field(description="When posted (e.g., '2h ago')")
    language: str | None = Field(None, description="Post language code")
    like_count: int | None = Field(None, description="Number of likes")
    comment_count: int | None = Field(None, description="Number of comments")
    share_count: int | None = Field(None, description="Number of shares")
    hashtags: List[str] = Field(default_factory=list, description="Hashtags without #")
    mentions: List[str] = Field(default_factory=list, description="Mentions without @")
    raw_json: dict | None = Field(None, description="Raw platform data if available")

class PostBatch(BaseModel):
    """Container for multiple posts."""
    posts: List[ExtractedPost] = Field(description="List of extracted posts")
```

### News Article Model
```python
class ExtractedArticle(BaseModel):
    """News article extraction schema."""
    article_id: str = Field(description="Unique identifier")
    title: str = Field(description="Article headline")
    url: str = Field(description="Full article URL")
    source: str = Field(description="Publisher name")
    author: str | None = Field(None, description="Article author")
    published_date: str = Field(description="Publication date")
    summary: str | None = Field(None, description="Article summary/excerpt")
    category: str | None = Field(None, description="Article category")
    image_url: str | None = Field(None, description="Main image URL")

class ArticleBatch(BaseModel):
    """Container for multiple articles."""
    articles: List[ExtractedArticle]
```

### Product Model
```python
class ExtractedProduct(BaseModel):
    """E-commerce product schema."""
    product_id: str
    title: str
    url: str
    price: float = Field(description="Current price in USD")
    original_price: float | None = Field(None, description="Original price if on sale")
    rating: float | None = Field(None, description="Average rating 0-5")
    review_count: int | None = Field(None, description="Number of reviews")
    availability: str = Field(description="Stock status")
    brand: str | None = None
    category: str | None = None
    image_url: str | None = None
    description: str | None = None

class ProductBatch(BaseModel):
    """Container for multiple products."""
    products: List[ExtractedProduct]
```

---

## Error Handling

### Custom Error Classes
```python
class {Platform}CollectionError(RuntimeError):
    """Raised when {platform} collection fails."""
    pass

class {Platform}AuthenticationError({Platform}CollectionError):
    """Raised when authentication fails."""
    pass

class {Platform}RateLimitError({Platform}CollectionError):
    """Raised when rate limited."""
    pass
```

### Error Handling Pattern
```python
try:
    result = await agent.run(max_steps=max_steps)
    posts = self._parse_result(result)
    return posts
    
except TimeoutError as exc:
    self.logger.error("Collection timeout after %d seconds", timeout)
    raise {Platform}CollectionError(
        f"Collection timed out. Try reducing target_count or increasing timeout."
    ) from exc
    
except Exception as exc:
    self.logger.error("Collection failed: %s", exc, exc_info=True)
    raise {Platform}CollectionError(
        f"Failed to collect posts: {exc}\n"
        f"Troubleshooting:\n"
        f"  - Ensure Chrome is installed at the correct path\n"
        f"  - Try clearing cache with --clear-cache\n"
        f"  - Check internet connection\n"
        f"  - Some sites may require manual login on first run"
    ) from exc
```

---

## CLI Integration Pattern

```python
"""CLI commands for {platform} sentiment analysis."""

import asyncio
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from app.adapters.{platform}_source import (
    {Platform}Collector,
    {Platform}SearchConfig,
)
from app.infra import get_logger

app = typer.Typer(help="{Platform} sentiment analysis commands")
console = Console()
logger = get_logger(__name__)


@app.command()
def {platform}-sentiment(
    query: str = typer.Option("Tesla", "--query", "-q", help="Search query"),
    target: int = typer.Option(50, "--target", "-t", help="Target post count"),
    max_scrolls: int = typer.Option(5, "--max-scrolls", help="Maximum scrolls"),
    min_engagement: int = typer.Option(100, "--min-engagement", help="Minimum likes"),
    check_cache: bool = typer.Option(False, "--check-cache", help="Check cache status"),
    clear_cache: bool = typer.Option(False, "--clear-cache", help="Clear session cache"),
):
    """
    Collect {platform} posts and analyze sentiment.
    
    Example:
        python -m app.cli.{platform}_sentiment {platform}-sentiment --query "Tesla stock" --target 30
    """
    asyncio.run(_collect_{platform}_posts(
        query=query,
        target=target,
        max_scrolls=max_scrolls,
        min_engagement=min_engagement,
        check_cache=check_cache,
        clear_cache=clear_cache,
    ))


async def _collect_{platform}_posts(
    query: str,
    target: int,
    max_scrolls: int,
    min_engagement: int,
    check_cache: bool,
    clear_cache: bool,
):
    """Internal async function to collect posts."""
    cache_file = Path("cache/{platform}_session.json")
    
    # Handle cache operations
    if check_cache:
        if cache_file.exists():
            console.print(f"[green]✓[/green] Cache exists at {cache_file}")
        else:
            console.print(f"[yellow]✗[/yellow] No cache found")
        return
    
    if clear_cache:
        if cache_file.exists():
            cache_file.unlink()
            console.print(f"[green]✓[/green] Cleared cache at {cache_file}")
        return
    
    # Create config
    config = {Platform}SearchConfig(
        query=query,
        target_count=target,
        max_scrolls=max_scrolls,
        min_engagement=min_engagement,
    )
    
    # Collect posts
    console.print(f"[bold]Collecting {target} posts from {Platform}...[/bold]")
    console.print(f"Query: {query}")
    console.print(f"Min engagement: {min_engagement}")
    
    try:
        collector = {Platform}Collector(config)
        posts = await collector.collect()
        
        # Display results
        table = Table(title=f"{Platform} Posts")
        table.add_column("ID", style="cyan")
        table.add_column("Author", style="magenta")
        table.add_column("Text", style="white", max_width=60)
        table.add_column("Likes", style="green", justify="right")
        
        for post in posts[:10]:  # Show first 10
            table.add_row(
                post.post_id[:8],
                post.author_handle or "N/A",
                post.text[:60] + "..." if len(post.text) > 60 else post.text,
                str(post.like_count or 0),
            )
        
        console.print(table)
        console.print(f"\n[green]✓[/green] Collected {len(posts)} posts")
        
        # TODO: Store in database
        # storage = StorageService()
        # for post in posts:
        #     await storage.save_{platform}_post(post)
        
    except Exception as exc:
        console.print(f"[red]✗ Error:[/red] {exc}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
```

---

## Quick Reference

### When to Use Vision Mode
```python
use_vision = not has_cache  # Use for first-time login
use_vision = True  # Always use for complex/dynamic UIs
use_vision = False  # Don't use if page is simple/stable
```

### Scroll Count Guidelines
- Simple list: 3-5 scrolls
- Social media feed: 5-10 scrolls
- Search results: 3-7 scrolls
- Infinite scroll: Cap at 10-15 max

### Max Steps Guidelines
- Cached session: 10-15 steps
- First-time auth: 20-30 steps
- Complex workflow: 30-50 steps

### Model Selection
- `gpt-4o-mini`: Fast, cheap, good for simple extraction
- `gpt-4o`: Balanced speed and accuracy
- `gpt-4`: Maximum accuracy for complex pages

---

**End of Reference Document**

