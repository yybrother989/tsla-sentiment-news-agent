"""
Example 4: Adding a New Social Media Platform (LinkedIn)
=========================================================

This example demonstrates:
- How to create a complete adapter for a new social media platform
- Session management for authenticated sites
- Structured data extraction
- Integration with the existing project architecture

Use this as a template when adding Instagram, YouTube, TikTok, etc.
"""

import asyncio
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Sequence

from browser_use import Agent, ChatOpenAI
from browser_use.browser.profile import BrowserProfile
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


# Step 1: Define your data schema (similar to TwitterTweet)
class LinkedInPost(BaseModel):
    """Schema for a LinkedIn post."""
    post_id: str
    post_url: str
    author_name: str | None = None
    author_title: str | None = None  # Professional title
    text: str
    timestamp: str
    like_count: int | None = None
    comment_count: int | None = None
    repost_count: int | None = None
    hashtags: List[str] = Field(default_factory=list)
    posted_at: datetime | None = None
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LinkedInPostBatch(BaseModel):
    """Container for multiple LinkedIn posts."""
    posts: List[LinkedInPost]


# Step 2: Create a collector class (similar to TwitterCollector)
class LinkedInCollector:
    """Collects LinkedIn posts about a search query."""
    
    def __init__(self, query: str = "Tesla", target_count: int = 20):
        self.query = query
        self.target_count = target_count
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.session_cache = self.cache_dir / "linkedin_session.json"
    
    async def collect(self) -> Sequence[LinkedInPost]:
        """Main collection method."""
        task = self._build_task_prompt()
        
        try:
            # Load cached session if available
            storage_state = self._load_session_cache()
            has_cache = storage_state is not None
            
            # Configure browser profile with stealth settings
            profile = BrowserProfile(
                headless=False,
                disable_security=True,
                storage_state=storage_state,
                minimum_wait_page_load_time=2.0,
                wait_between_actions=1.0,
                extra_chromium_args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ],
            )
            
            # Initialize LLM
            from app.infra.config import get_settings
            settings = get_settings()
            
            llm = ChatOpenAI(
                model=settings.planner_llm_model,
                api_key=settings.openai_api_key,
                temperature=0.0,
            )
            
            # Adjust steps based on cache
            max_steps = 15 if has_cache else 25
            use_vision = not has_cache
            
            # Create agent with output schema
            agent = Agent(
                task=task,
                llm=llm,
                browser_profile=profile,
                output_model_schema=LinkedInPostBatch,
                use_vision=use_vision,
                max_actions_per_step=12,
                max_failures=3,
            )
            
            print(f"🚀 Collecting LinkedIn posts about '{self.query}'...")
            result = await agent.run(max_steps=max_steps)
            
            # Save session state
            await self._save_session_cache(profile)
            
            # Parse and return results
            posts = self._parse_result(result)
            print(f"✅ Collected {len(posts)} LinkedIn posts")
            return posts
            
        except Exception as exc:
            print(f"❌ LinkedIn collection failed: {exc}")
            raise
    
    def _build_task_prompt(self) -> str:
        """Build the task prompt for the agent."""
        has_cache = self._load_session_cache() is not None
        
        if has_cache:
            login_block = """
STEP 1: Check Authentication
- Go to https://www.linkedin.com/feed/
- Check if you're already logged in (see your profile icon in top-right)
- If logged in, proceed to STEP 2
- If not logged in, you'll need to authenticate
"""
        else:
            login_block = """
STEP 1: Login to LinkedIn
- Go to https://www.linkedin.com/login
- You may need to login manually
- Wait until you see your LinkedIn feed
"""
        
        query_encoded = urllib.parse.quote(self.query)
        
        return f"""
You are a LinkedIn data collector. Collect posts about {self.query}.

{login_block}

STEP 2: Search for Posts
- Go to https://www.linkedin.com/search/results/content/?keywords={query_encoded}
- This searches for LinkedIn posts containing "{self.query}"
- Wait for results to load

STEP 3: Collect Posts
- Scroll down 3-4 times to load more posts
- Wait 3 seconds between scrolls
- Stop when you have {self.target_count} unique posts

STEP 4: Extract Data
For each post, extract:
- post_id: A unique identifier (can be from the URL or generate one)
- post_url: Full URL to the post
- author_name: Person or company who posted
- author_title: Their professional title/headline
- text: Full post content
- timestamp: When it was posted (e.g., "2h", "1d ago")
- like_count: Number of reactions/likes
- comment_count: Number of comments
- repost_count: Number of reposts/shares
- hashtags: List of hashtags used in the post

WHAT TO SKIP:
- Promoted/sponsored posts
- Duplicate posts
- Posts without proper URLs

FINAL OUTPUT:
Return JSON: {{"posts": [...]}}
"""
    
    def _parse_result(self, result) -> Sequence[LinkedInPost]:
        """Parse the agent result into LinkedInPost objects."""
        raw_batch: LinkedInPostBatch | None = None
        
        # Try to extract structured output
        if hasattr(result, 'history') and getattr(result.history, 'structured_output', None):
            candidate = result.history.structured_output
            if isinstance(candidate, LinkedInPostBatch):
                raw_batch = candidate
        
        if raw_batch is None and hasattr(result, 'final_result'):
            final_value = result.final_result() if callable(result.final_result) else result.final_result
            if isinstance(final_value, LinkedInPostBatch):
                raw_batch = final_value
            elif isinstance(final_value, dict) and 'posts' in final_value:
                raw_batch = LinkedInPostBatch(**final_value)
        
        if raw_batch is None:
            print("⚠️  No structured posts returned")
            return []
        
        # Parse and validate posts
        parsed: list[LinkedInPost] = []
        seen_ids: set[str] = set()
        
        for post in raw_batch.posts:
            try:
                if not post.post_url or not post.post_url.startswith("http"):
                    continue
                if post.post_id in seen_ids:
                    continue
                
                # Parse timestamp (similar to Twitter)
                posted_at = self._parse_timestamp(post.timestamp)
                post.posted_at = posted_at
                
                parsed.append(post)
                seen_ids.add(post.post_id)
                
            except Exception as exc:
                print(f"⚠️  Failed to parse post {post.post_id}: {exc}")
                continue
        
        return parsed
    
    def _parse_timestamp(self, timestamp: str | None) -> datetime | None:
        """Parse relative timestamps like '2h ago' into datetime."""
        if not timestamp:
            return None
        
        ts = timestamp.strip().lower()
        now = datetime.now(timezone.utc)
        
        try:
            if 'h' in ts or 'hour' in ts:
                hours = int(''.join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(hours=hours)
            elif 'd' in ts or 'day' in ts:
                days = int(''.join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(days=days)
            elif 'w' in ts or 'week' in ts:
                weeks = int(''.join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(weeks=weeks)
            elif 'm' in ts and 'mo' not in ts:  # minutes, not months
                minutes = int(''.join(ch for ch in ts if ch.isdigit()))
                return now - timedelta(minutes=minutes)
            
            # Try ISO format parsing
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
            return None
        
        try:
            with open(self.session_cache, 'r') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
            if datetime.now() - cache_time > timedelta(hours=24):
                print("⏰ Session cache expired")
                self.session_cache.unlink()
                return None
            
            print("✅ Loaded cached LinkedIn session")
            return cache_data.get('storage_state')
            
        except Exception as exc:
            print(f"⚠️  Failed to load session cache: {exc}")
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
                    
                    print("💾 Saved LinkedIn session cache")
                    
        except Exception as exc:
            print(f"⚠️  Failed to save session cache: {exc}")


# Step 3: Create a simple CLI wrapper (like twitter_sentiment.py)
async def collect_linkedin_posts(query: str = "Tesla", target: int = 20):
    """Main function to collect LinkedIn posts."""
    collector = LinkedInCollector(query=query, target_count=target)
    posts = await collector.collect()
    
    # Display results
    print(f"\n📊 Collected {len(posts)} LinkedIn posts:\n")
    for idx, post in enumerate(posts[:5], 1):  # Show first 5
        print(f"{idx}. {post.text[:80]}...")
        print(f"   Author: {post.author_name} ({post.author_title})")
        print(f"   Engagement: 👍 {post.like_count} | 💬 {post.comment_count} | 🔄 {post.repost_count}")
        print(f"   Posted: {post.posted_at}")
        print(f"   URL: {post.post_url}\n")
    
    return posts


# Step 4: Integration example
async def store_in_database(posts: Sequence[LinkedInPost]):
    """
    Example of how to store collected posts in the database.
    
    You would:
    1. Create a new migration: migrations/004_create_linkedin_sentiment_table.sql
    2. Add LinkedInPost to app/domain/schemas.py
    3. Update app/services/storage.py with save_linkedin_posts()
    4. Create app/cli/linkedin_sentiment.py for the CLI
    """
    print("\n📝 To integrate with the database:")
    print("1. Create migration: migrations/004_create_linkedin_sentiment_table.sql")
    print("2. Add schema: app/domain/schemas.py")
    print("3. Add storage: app/services/storage.py")
    print("4. Create CLI: app/cli/linkedin_sentiment.py")
    print("\nSee twitter_source.py and reddit_source.py for reference!")
    
    # Example storage code (pseudo-code):
    # from app.services.storage import StorageService
    # storage = StorageService()
    # for post in posts:
    #     await storage.save_linkedin_post(post)


async def main():
    """Run the LinkedIn collector example."""
    print("=" * 70)
    print("Example: Adding a New Social Media Platform (LinkedIn)")
    print("=" * 70)
    print("\n📚 This demonstrates:")
    print("  1. Creating a complete adapter for a new platform")
    print("  2. Session management for authenticated sites")
    print("  3. Structured data extraction with Pydantic")
    print("  4. Integration patterns for the project")
    print("\n💡 Use this template to add Instagram, YouTube, TikTok, etc.\n")
    
    try:
        posts = await collect_linkedin_posts(query="Tesla stock", target=10)
        await store_in_database(posts)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: LinkedIn may require manual login on first run.")


if __name__ == "__main__":
    asyncio.run(main())

