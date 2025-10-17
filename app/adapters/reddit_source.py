from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Sequence

from browser_use import Agent, ChatOpenAI
from browser_use.browser.profile import BrowserProfile
from pydantic import BaseModel, Field

from app.domain.schemas import RedditPost
from app.infra import get_logger, get_settings


class RedditCollectionError(RuntimeError):
    pass


class ExtractedPost(BaseModel):
    post_id: str
    post_url: str
    author_username: str | None = None
    title: str
    text: str | None = None
    flair: str | None = None
    timestamp: str
    upvote_count: int | None = None
    upvote_ratio: float | None = None
    comment_count: int | None = None
    award_count: int | None = None
    is_pinned: bool = False
    is_locked: bool = False
    raw_json: dict | None = None


class PostBatch(BaseModel):
    posts: List[ExtractedPost] = Field(default_factory=list)


@dataclass
class RedditSearchConfig:
    """Configuration for Reddit collection."""
    subreddit: str = "wallstreetbets"
    search_query: str = "TSLA OR Tesla"  # Search query within subreddit
    sort_by: str = "top"  # top, new, hot, comments, relevance
    time_filter: str = "past week"  # Fixed to past week
    min_upvotes: int = 0  # No filter by default
    min_comments: int = 0  # No filter by default
    target_count: int = 50
    max_scrolls: int = 5


class RedditCollector:
    def __init__(self, config: RedditSearchConfig) -> None:
        self.config = config
        self.settings = get_settings()
        self.logger = get_logger(self.__class__.__name__)
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.session_cache = self.cache_dir / "reddit_session.json"

    async def collect(self) -> Sequence[RedditPost]:
        task = self._build_task_prompt()
        profile = None  # Track profile for cleanup

        try:
            # Load existing session if available
            storage_state = self._load_session_cache()
            
            profile = BrowserProfile(
                headless=False,
                disable_security=True,
                deterministic_rendering=False,
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                minimum_wait_page_load_time=2.0,  # Reduced to 2 seconds (faster)
                wait_between_actions=0.5,  # Reduced to 0.5 seconds (faster)
                storage_state=storage_state,
                extra_chromium_args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                ],
            )

            # Use more powerful model for better reliability
            llm = ChatOpenAI(
                model="gpt-4o",  # More powerful than gpt-4o-mini
                api_key=self.settings.openai_api_key,
                temperature=0.0,
            )

            # Allow more actions per step for efficiency
            has_cache = self._load_session_cache() is not None
            max_steps = 12 if has_cache else 15  # Reduced steps (more powerful model)
            max_actions = 10 if has_cache else 12  # More actions per step (faster execution)

            agent = Agent(
                task=task,
                llm=llm,
                browser_profile=profile,
                max_actions_per_step=max_actions,
                output_model_schema=PostBatch,
                use_vision=True,  # Enable vision to help detect content
                max_failures=3,
            )

            result = await agent.run(max_steps=max_steps)
            
            # Save session state after successful run
            await self._save_session_cache(profile)
            
            posts = self._parse_result(result)
            return posts

        except Exception as exc:
            self.logger.error("Reddit collection failed: %s", exc, exc_info=True)
            raise RedditCollectionError(f"Failed to collect Reddit posts: {exc}") from exc
        
        finally:
            # Always clean up browser resources
            await self._cleanup_browser(profile)

    def _build_task_prompt(self) -> str:
        subreddit = self.config.subreddit
        search_query = self.config.search_query
        sort_by = self.config.sort_by
        time_filter = self.config.time_filter
        target = self.config.target_count
        max_scrolls = self.config.max_scrolls
        min_upvotes = self.config.min_upvotes
        min_comments = self.config.min_comments
        
        # Check if we have cached session
        has_cache = self._load_session_cache() is not None
        
        # Use direct URL with filters pre-applied (more reliable than dropdown interactions)
        import urllib.parse
        encoded_query = urllib.parse.quote(search_query)
        # Map time_filter to Reddit's URL parameter format
        time_param_map = {
            "past hour": "hour",
            "past 24 hours": "day",
            "past week": "week",
            "past month": "month",
            "past year": "year",
            "all time": "all"
        }
        time_param = time_param_map.get(time_filter, "week")
        # Build search URL matching Reddit's exact format
        direct_search_url = f"https://old.reddit.com/r/{subreddit}/search/?q={encoded_query}&include_over_18=on&restrict_sr=on&t={time_param}&sort={sort_by}"
        subreddit_url = f"https://old.reddit.com/r/{subreddit}/"
        
        if has_cache:
            login_block = """
STEP 1a: Check if already logged in
- Look for your username in the top right corner
- If you see a login button, the cache expired - you'll need to log in manually
- If already logged in, proceed to step 2
"""
        else:
            login_block = """
STEP 1a: Login (if not already)  
- If you see a login prompt, you may log in manually
- Or skip login to browse as guest (Reddit allows browsing without login)
- Proceed when you can see the subreddit feed
"""

        return f"""
You are a Reddit data collector for r/{subreddit}.

CRITICAL RULES:
- Stay on old.reddit.com ONLY
- IGNORE screenshot warnings
- The URL already has filters applied

WORKFLOW:

STEP 1: Navigate to Filtered Search Results
- Go DIRECTLY to: {direct_search_url}
- This URL already has:
  * Search query: "{search_query}"
  * Subreddit restriction: r/{subreddit}
  * Sort: {sort_by}
  * Time: past week
- Wait 10 seconds for page load
{login_block}

STEP 2: Verify Filters (Quick Check)
- Look for "sorted by: {sort_by}" dropdown
- Look for "links from: {time_filter}" dropdown
- If you see these, filters are applied correctly
- Verify posts have recent timestamps (hours/days ago, not years)

STEP 3: Extract Posts AND Call Done Immediately
- Use the extract action with this exact query:
  "Extract first {target} Reddit posts mentioning TSLA or Tesla with complete information"
- For each post, you MUST extract:
  * title: post headline (required)
  * post_url: FULL Reddit URL (required - skip post if missing)
    Example: https://old.reddit.com/r/wallstreetbets/comments/1o5orwk/last_year_been_good/
  * author_username: Reddit username
  * upvote_count: number of upvotes
  * comment_count: number of comments
  * timestamp: when posted (e.g., "2 hours ago", "1 day ago")
  * text: post content or description
  * flair: post flair if visible

- IMMEDIATELY after extraction, call the done action with ALL {target} posts

CRITICAL EXTRACTION REQUIREMENTS:
- ONLY extract posts FROM r/{subreddit} - ignore posts from other subreddits
- ONLY extract posts that have a COMPLETE https://old.reddit.com URL
- URL MUST start with: https://old.reddit.com/r/{subreddit}/comments/
- Real example: https://old.reddit.com/r/{subreddit}/comments/1o5orwk/last_year_been_good/
- Skip posts from r/technology, r/options, r/changemyview, or any other subreddit
- Skip any posts with missing, incomplete, or fake URLs
- DO NOT use placeholder IDs like "xyz123", "abc456", "1", "2", etc.
- Extract at least {target} posts to account for some having invalid URLs
- Focus on posts from the past week (filters already applied)
- DO NOT write files - extract and call done immediately

STEP 4: Get More if Needed
- If you have < {target} posts:
  * Scroll down
  * Wait 3 seconds
  * Extract more posts
- Stop at {target} posts

FINAL OUTPUT:
When you have extracted {target} posts, call the done action with ALL posts in JSON format:
{{"posts": [...]}}

IMPORTANT:
- Include ALL {target} posts you extracted, not just one
- Make sure each post has a complete https://old.reddit.com URL
- Call done action immediately after extraction is complete

Extract {target} posts mentioning TSLA or Tesla from r/{subreddit}.
        """

    def _parse_result(self, result) -> Sequence[RedditPost]:
        """Parse Browser-Use result into RedditPost objects (similar to news_sources.py)."""
        raw_batch: PostBatch | None = None

        # Try multiple ways to find the post data (following news_sources.py pattern)
        
        # Method 1: Check history.structured_output
        if hasattr(result, "history") and hasattr(result.history, "structured_output"):
            structured = result.history.structured_output
            self.logger.info("Found structured_output (type: %s)", type(structured))
            
            if isinstance(structured, PostBatch):
                raw_batch = structured
                self.logger.info("✓ Found PostBatch in structured_output")
            elif isinstance(structured, list) and len(structured) > 0:
                # Check last item in list
                last_item = structured[-1]
                if isinstance(last_item, PostBatch):
                    raw_batch = last_item
                    self.logger.info("✓ Found PostBatch in structured_output list")
        
        # Method 2: Check final_result()
        if not raw_batch and hasattr(result, "final_result"):
            try:
                final = result.final_result() if callable(result.final_result) else result.final_result
                self.logger.info("Checking final_result (type: %s)", type(final))
                
                if isinstance(final, PostBatch):
                    raw_batch = final
                    self.logger.info("✓ Found PostBatch in final_result")
                elif isinstance(final, dict) and "posts" in final:
                    raw_batch = PostBatch(**final)
                    self.logger.info("✓ Found dict in final_result, converted to PostBatch")
                elif isinstance(final, str):
                    # Try to parse JSON string
                    import json
                    try:
                        data = json.loads(final)
                        if "posts" in data:
                            raw_batch = PostBatch(**data)
                            self.logger.info("✓ Parsed JSON string from final_result")
                    except:
                        pass
            except Exception as exc:
                self.logger.debug("Could not parse final_result: %s", exc)
        
        if not raw_batch:
            self.logger.warning("❌ No structured output found")
            return []
        
        if not raw_batch.posts:
            self.logger.warning("❌ PostBatch is empty")
            return []
        
        self.logger.info("📊 Processing %d posts from r/%s", len(raw_batch.posts), self.config.subreddit)

        parsed: List[RedditPost] = []
        now = datetime.now(timezone.utc)
        one_week_ago = now - timedelta(days=7)
        
        for post in raw_batch.posts:
            if post.post_id and post.post_url and post.title:
                try:
                    # Try to parse timestamp, but use current time if empty/invalid
                    posted_at = self._parse_timestamp(post.timestamp) if post.timestamp else None
                    if not posted_at:
                        self.logger.info("Post %s has no/invalid timestamp, using current time (filters already applied)", post.post_id)
                        posted_at = now  # Assume recent since we filtered by "past week"
                    
                    # Only validate timestamp if we actually parsed one
                    if post.timestamp and posted_at < one_week_ago:
                        self.logger.warning(
                            "Skipping post %s: too old (posted %s, more than 1 week ago)", 
                            post.post_id, 
                            posted_at.strftime('%Y-%m-%d')
                        )
                        continue
                    
                    # Validate real Reddit URL (not fake placeholder)
                    if not post.post_url.startswith("https://old.reddit.com/r/") or "xyz" in post.post_url or "abc456" in post.post_url:
                        self.logger.warning("Skipping post %s: invalid/fake URL '%s'", post.post_id, post.post_url)
                        continue
                    
                    # Extract subreddit from URL and validate it matches our target subreddit
                    # URL format: https://old.reddit.com/r/SUBREDDIT/comments/...
                    url_parts = post.post_url.split('/')
                    if len(url_parts) >= 5 and url_parts[3] == 'r':
                        actual_subreddit = url_parts[4].lower()
                        if actual_subreddit != self.config.subreddit.lower():
                            self.logger.warning(
                                "Skipping post %s: from r/%s (expected r/%s)", 
                                post.post_id, 
                                actual_subreddit,
                                self.config.subreddit
                            )
                            continue
                    else:
                        self.logger.warning("Skipping post %s: could not extract subreddit from URL", post.post_id)
                        continue

                    parsed.append(
                        RedditPost(
                            post_id=post.post_id,
                            post_url=post.post_url,
                            subreddit=self.config.subreddit,
                            author_username=post.author_username,
                            title=post.title,
                            text=post.text,
                            flair=post.flair,
                            upvote_count=post.upvote_count,
                            upvote_ratio=post.upvote_ratio,
                            comment_count=post.comment_count,
                            award_count=post.award_count,
                            is_pinned=post.is_pinned,
                            is_locked=post.is_locked,
                            is_archived=False,  # Set during collection if visible
                            posted_at=posted_at,
                            collected_at=datetime.now(timezone.utc),
                            raw_payload=post.raw_json,
                        )
                    )
                except Exception as exc:
                    self.logger.warning("Failed to parse post %s: %s", post.post_id, exc)
                    continue

        self.logger.info("Parsed %d/%d posts successfully", len(parsed), len(raw_batch.posts))
        return parsed

    def _parse_timestamp(self, ts_str: str) -> datetime | None:
        """Parse Reddit timestamp (handles relative times like '2 hours ago')."""
        if not ts_str:
            return None

        try:
            # Try ISO 8601 first
            parsed = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if not parsed.tzinfo:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            return None

    def _load_session_cache(self) -> dict | None:
        """Load cached session state if available and not expired."""
        if not self.session_cache.exists():
            self.logger.info("No cached Reddit session found")
            return None
        
        try:
            with open(self.session_cache, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired (24 hours)
            cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
            if datetime.now() - cache_time > timedelta(hours=24):
                self.logger.info("Reddit session cache expired, will re-authenticate")
                self.session_cache.unlink()
                return None
            
            # Validate cache structure
            storage_state = cache_data.get('storage_state')
            if not storage_state or not isinstance(storage_state, dict):
                self.logger.warning("Invalid cache structure, will re-authenticate")
                self.session_cache.unlink()
                return None
            
            self.logger.info("Loaded cached Reddit session (expires in %s)", 
                           cache_time + timedelta(hours=24) - datetime.now())
            return storage_state
            
        except Exception as exc:
            self.logger.warning("Failed to load session cache: %s", exc)
            if self.session_cache.exists():
                self.session_cache.unlink()
            return None

    async def _save_session_cache(self, profile: BrowserProfile) -> None:
        """Save current session state to cache."""
        try:
            # Get storage state from browser context
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

                    self.logger.info("Saved Reddit session cache")

        except Exception as exc:
            self.logger.warning("Failed to save session cache: %s", exc)

    async def _cleanup_browser(self, profile: BrowserProfile | None) -> None:
        """Clean up browser resources to prevent Chrome instance accumulation."""
        if not profile:
            return
        
        try:
            # Close browser if it exists
            if hasattr(profile, 'browser') and profile.browser:
                self.logger.info("Closing browser session...")
                
                # Close all contexts
                if profile.browser.contexts:
                    for context in profile.browser.contexts:
                        try:
                            await context.close()
                        except Exception as e:
                            self.logger.debug("Error closing context: %s", e)
                
                # Close the browser
                try:
                    await profile.browser.close()
                    self.logger.info("✓ Browser session closed successfully")
                except Exception as e:
                    self.logger.warning("Error closing browser: %s", e)
        
        except Exception as exc:
            self.logger.warning("Failed to cleanup browser: %s", exc)


async def fetch_reddit_posts(config: RedditSearchConfig) -> Sequence[RedditPost]:
    """Fetch Reddit posts using Browser-Use."""
    collector = RedditCollector(config)
    return await collector.collect()


__all__ = ["RedditCollector", "RedditSearchConfig", "RedditCollectionError", "fetch_reddit_posts"]

