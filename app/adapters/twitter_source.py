from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Sequence

from browser_use import Agent, ChatOpenAI
from browser_use.browser.profile import BrowserProfile
from pydantic import BaseModel, Field

from app.domain.schemas import TwitterTweet
from app.infra import get_logger, get_settings


class TwitterCollectionError(RuntimeError):
    pass


class ExtractedTweet(BaseModel):
    tweet_id: str
    tweet_url: str
    author_handle: str | None = None
    author_name: str | None = None
    author_username: str | None = None
    text: str
    timestamp: str
    language: str | None = None
    like_count: int | None = None
    reply_count: int | None = None
    retweet_count: int | None = None
    quote_count: int | None = None
    bookmark_count: int | None = None
    view_count: int | None = None
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    raw_json: dict | None = None


class TweetBatch(BaseModel):
    tweets: List[ExtractedTweet]


@dataclass
class TwitterSearchConfig:
    query: str
    since: str
    until: str
    min_replies: int
    min_faves: int
    min_retweets: int
    lang: str = "en"
    target_count: int = 75
    max_scrolls: int = 6

    @property
    def combined_query(self) -> str:
        return (
            f"({self.query}) min_replies:{self.min_replies} min_faves:{self.min_faves} "
            f"min_retweets:{self.min_retweets} lang:{self.lang} since:{self.since} until:{self.until}"
        )


class TwitterCollector:
    def __init__(self, config: TwitterSearchConfig) -> None:
        self.config = config
        self.settings = get_settings()
        self.logger = get_logger(self.__class__.__name__)
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.session_cache = self.cache_dir / "twitter_session.json"

    async def collect(self) -> Sequence[TwitterTweet]:
        task = self._build_task_prompt()

        try:
            # Load existing session if available
            storage_state = self._load_session_cache()
            
            profile = BrowserProfile(
                headless=False,
                disable_security=True,
                deterministic_rendering=False,
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                minimum_wait_page_load_time=2.0,  # Increased wait time for Twitter to load
                wait_between_actions=1.0,  # Slower actions to appear more human
                storage_state=storage_state,
                extra_chromium_args=[
                    '--disable-blink-features=AutomationControlled',  # Hide automation
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                ],
            )

            llm = ChatOpenAI(
                model=self.settings.planner_llm_model,
                api_key=self.settings.openai_api_key,
                temperature=0.0,
            )

            # Reduce steps for cached sessions
            has_cache = self._load_session_cache() is not None
            max_steps = 15 if has_cache else 20
            max_actions = 12 if has_cache else 18

            # Use vision mode to better detect login elements
            use_vision = not has_cache  # Use vision for first-time login only
            
            agent = Agent(
                task=task,
                llm=llm,
                browser_profile=profile,
                max_actions_per_step=max_actions,
                output_model_schema=TweetBatch,
                use_vision=use_vision,  # Enable vision for login detection
                max_failures=3,
            )

            result = await agent.run(max_steps=max_steps)
            
            # Save session state after successful run
            await self._save_session_cache(profile)
            
            tweets = self._parse_result(result)
            return tweets

        except Exception as exc:
            self.logger.error("Twitter collection failed: %s", exc, exc_info=True)
            raise TwitterCollectionError(f"Failed to collect tweets: {exc}") from exc

    def _build_task_prompt(self) -> str:
        query = self.config.combined_query
        target = self.config.target_count
        max_scrolls = self.config.max_scrolls
        
        # Check if we have cached session
        has_cache = self._load_session_cache() is not None
        
        if has_cache:
            # Optimized flow for cached sessions
            login_block = """
1a. Check if already logged in by looking for the search bar or timeline.
    - If you see a search bar or Twitter feed, you're already logged in - proceed to step 2.
    - If you see a login form, something went wrong with the cache - proceed to manual login.
"""
        else:
            # First-time login flow
            if self.settings.twitter_username and self.settings.twitter_password:
                login_block = f"""
1a. Complete Twitter login process:
    - If login form is visible, fill username: {self.settings.twitter_username}
    - Fill password: {self.settings.twitter_password}
    - Submit and handle any verification challenges (2FA, phone verification, etc.)
    - Wait until you see the main Twitter interface with search functionality
    - DO NOT navigate away from the main Twitter page after login
"""
            else:
                login_block = """
1a. Complete Twitter login manually:
    - Fill in your Twitter credentials
    - Complete any verification steps (2FA, phone verification, etc.)
    - Wait until you see the main Twitter interface with search functionality
    - DO NOT navigate away from the main Twitter page after login
"""

        return f"""
You are a Twitter data collector. Your ONLY job is to collect Tesla tweets from Twitter/X.

CRITICAL RULES - READ FIRST:
- You MUST stay on Twitter.com or X.com ONLY - do NOT use search engines like DuckDuckGo
- If you see an empty page on Twitter, WAIT and try again - do NOT give up and search elsewhere
- You have authenticated cookies loaded, so Twitter should work
- Do NOT navigate away from Twitter under any circumstances

STEP-BY-STEP WORKFLOW:

STEP 1: Navigate to Twitter Search
- Go DIRECTLY to: https://twitter.com/search?q={urllib.parse.quote(query)}&f=live
- This URL has the search query already embedded
- Wait 10 seconds for the page to load completely
- If the page appears empty, wait another 10 seconds and refresh
{login_block}

STEP 2: Verify You're on Twitter
- Check the URL - it MUST contain "twitter.com" or "x.com"
- If you're on any other domain (like duckduckgo.com), STOP and navigate back to Twitter
- The page should show tweet results

STEP 3: Collect Tweets
- Scroll down the search results slowly
- Wait 4 seconds between each scroll for new tweets to load
- Stop after {max_scrolls} scrolls OR when you have {target} unique tweets

STEP 4: Extract Tweet Data
For each tweet visible on the page, extract:
- tweet_id, tweet_url (MUST be https://twitter.com/USER/status/ID or https://x.com/USER/status/ID)
- author_handle, author_name, author_username
- text (full tweet content)
- timestamp (convert "2h ago" to ISO 8601 format like "2025-10-16T12:00:00Z")
- like_count, reply_count, retweet_count, quote_count, bookmark_count, view_count
- hashtags[] (array of hashtag texts), mentions[] (array of @usernames)
- language: "en" for English tweets

WHAT TO SKIP:
- Promoted/Sponsored tweets
- Duplicate tweets you already collected  
- Tweets without proper URLs
- Retweets (unless they have significant engagement themselves)

FINAL OUTPUT:
Return JSON in this exact format: {{"tweets": [...]}}

REMEMBER: Stay on Twitter ONLY. Never use external search engines!
        """

    def _parse_result(self, result) -> Sequence[TwitterTweet]:
        raw_batch: TweetBatch | None = None

        if hasattr(result, "history") and getattr(result.history, "structured_output", None):
            candidate = result.history.structured_output
            if isinstance(candidate, TweetBatch):
                raw_batch = candidate

        if raw_batch is None and hasattr(result, "final_result"):
            final_value = result.final_result() if callable(result.final_result) else result.final_result
            if isinstance(final_value, TweetBatch):
                raw_batch = final_value
            elif isinstance(final_value, dict) and "tweets" in final_value:
                raw_batch = TweetBatch(**final_value)

        if raw_batch is None:
            self.logger.warning("No structured tweets returned from Browser Use")
            return []

        parsed: list[TwitterTweet] = []
        seen_ids: set[str] = set()

        for idx, tweet in enumerate(raw_batch.tweets, start=1):
            try:
                if not tweet.tweet_url or not tweet.tweet_url.startswith("http"):
                    continue
                if tweet.tweet_id in seen_ids:
                    continue

                posted_at = self._parse_timestamp(tweet.timestamp)
                if posted_at is None:
                    continue

                parsed.append(
                    TwitterTweet(
                        tweet_id=tweet.tweet_id,
                        tweet_url=tweet.tweet_url,
                        conversation_id=tweet.raw_json.get("conversation_id") if tweet.raw_json else None,
                        author_id=tweet.raw_json.get("author_id") if tweet.raw_json else None,
                        author_handle=tweet.author_handle,
                        author_name=tweet.author_name,
                        author_username=tweet.author_username,
                        text=tweet.text,
                        language=tweet.language,
                        hashtags=tweet.hashtags,
                        mentions=tweet.mentions,
                        like_count=tweet.like_count,
                        reply_count=tweet.reply_count,
                        retweet_count=tweet.retweet_count,
                        quote_count=tweet.quote_count,
                        bookmark_count=tweet.bookmark_count,
                        view_count=tweet.view_count,
                        posted_at=posted_at,
                        collected_at=datetime.now(timezone.utc),
                        raw_payload=tweet.raw_json,
                    )
                )
                seen_ids.add(tweet.tweet_id)
            except Exception as exc:
                self.logger.debug("Failed to parse tweet %s: %s", tweet.tweet_id, exc)
                continue

        self.logger.info("Parsed %d tweets", len(parsed))
        return parsed

    def _parse_timestamp(self, timestamp: str | None) -> datetime | None:
        if not timestamp:
            return None

        ts = timestamp.strip()
        now = datetime.now(timezone.utc)
        lower = ts.lower()

        try:
            if "s" in lower and any(ch.isdigit() for ch in lower):
                seconds = int("".join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(seconds=seconds)
            if "min" in lower or "m" in lower:
                minutes = int("".join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(minutes=minutes)
            if "hour" in lower or "hr" in lower or "h" in lower:
                hours = int("".join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(hours=hours)
            if "day" in lower or "d" in lower:
                days = int("".join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(days=days)
            if "week" in lower or "wk" in lower or "w" in lower:
                weeks = int("".join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(weeks=weeks)

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
            import json
            with open(self.session_cache, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired (24 hours)
            cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
            if datetime.now() - cache_time > timedelta(hours=24):
                self.logger.info("Session cache expired, will re-authenticate")
                self.session_cache.unlink()  # Delete expired cache
                return None
            
            # Validate cache structure
            storage_state = cache_data.get('storage_state')
            if not storage_state or not isinstance(storage_state, dict):
                self.logger.warning("Invalid cache structure, will re-authenticate")
                self.session_cache.unlink()
                return None
            
            self.logger.info("Loaded cached Twitter session (expires in %s)", 
                           cache_time + timedelta(hours=24) - datetime.now())
            return storage_state
            
        except Exception as exc:
            self.logger.warning("Failed to load session cache: %s", exc)
            # Clean up corrupted cache
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
                    storage_state = context.storage_state()
                    
                    cache_data = {
                        'timestamp': datetime.now().isoformat(),
                        'storage_state': storage_state
                    }
                    
                    import json
                    with open(self.session_cache, 'w') as f:
                        json.dump(cache_data, f, indent=2)
                    
                    self.logger.info("Saved Twitter session cache")
                    
        except Exception as exc:
            self.logger.warning("Failed to save session cache: %s", exc)


async def fetch_tweets(config: TwitterSearchConfig) -> Sequence[TwitterTweet]:
    collector = TwitterCollector(config)
    return await collector.collect()


__all__ = [
    "TwitterCollectionError",
    "TwitterSearchConfig",
    "TwitterCollector",
    "fetch_tweets",
]

