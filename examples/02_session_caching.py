"""
Example 2: Session Caching and Persistence
==========================================

This example demonstrates:
- Saving browser session state (cookies, localStorage)
- Loading cached sessions to skip login
- Session expiration handling
- How twitter_source.py uses this pattern

This is CRITICAL for authenticated sites like Twitter.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

from browser_use import Agent, ChatOpenAI
from browser_use.browser.profile import BrowserProfile
from dotenv import load_dotenv

load_dotenv()


class SessionManager:
    """Manages browser session caching (same pattern as twitter_source.py)."""
    
    def __init__(self, cache_file: str = "cache/example_session.json"):
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(exist_ok=True)
    
    def load_session(self) -> dict | None:
        """Load cached session if available and not expired."""
        if not self.cache_file.exists():
            print("❌ No cached session found")
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check expiration (24 hours)
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > timedelta(hours=24):
                print("⏰ Session expired (>24 hours old)")
                self.cache_file.unlink()
                return None
            
            print(f"✅ Loaded cached session (expires in {cache_time + timedelta(hours=24) - datetime.now()})")
            return cache_data['storage_state']
            
        except Exception as e:
            print(f"⚠️  Failed to load session: {e}")
            if self.cache_file.exists():
                self.cache_file.unlink()
            return None
    
    def save_session(self, storage_state: dict) -> None:
        """Save session state to cache."""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'storage_state': storage_state
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"💾 Session saved to {self.cache_file}")
        except Exception as e:
            print(f"⚠️  Failed to save session: {e}")


async def main():
    """Demonstrate session caching with a real website."""
    
    session_manager = SessionManager()
    
    # Load existing session
    storage_state = session_manager.load_session()
    has_cache = storage_state is not None
    
    # Configure browser profile with stealth settings
    profile = BrowserProfile(
        headless=False,  # Show browser so you can see it working
        disable_security=True,  # Bypass CORS/CSP
        storage_state=storage_state,  # Load cached session
        minimum_wait_page_load_time=2.0,
        wait_between_actions=1.0,
        extra_chromium_args=[
            '--disable-blink-features=AutomationControlled',  # Hide automation
        ]
    )
    
    # Adjust task based on cache availability
    if has_cache:
        task = """
        Go to https://reddit.com
        Check if you're logged in by looking for your username in the top-right.
        If logged in, tell me your username.
        If not logged in, say "Not logged in".
        """
    else:
        task = """
        Go to https://reddit.com
        You should see the public Reddit homepage.
        Tell me what the top post on r/popular is about.
        """
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    
    agent = Agent(
        task=task,
        llm=llm,
        browser_profile=profile,
        max_actions_per_step=8,
    )
    
    print(f"\n🚀 Running agent (cached session: {has_cache})")
    result = await agent.run(max_steps=10)
    
    # Save session after successful run
    # Note: In real usage, you'd extract storage_state from the browser context
    # For this example, we demonstrate the pattern
    print(f"\n✅ Agent completed: {result}")
    
    # To actually save the session, you would do:
    # if profile.browser and profile.browser.contexts:
    #     new_state = await profile.browser.contexts[0].storage_state()
    #     session_manager.save_session(new_state)


if __name__ == "__main__":
    print("=" * 60)
    print("Session Caching Example")
    print("=" * 60)
    print("\n📚 This demonstrates:")
    print("  1. Loading cached sessions to skip login")
    print("  2. Session expiration checking")
    print("  3. Saving sessions for future use")
    print("\n💡 Used extensively in app/adapters/twitter_source.py\n")
    
    asyncio.run(main())

