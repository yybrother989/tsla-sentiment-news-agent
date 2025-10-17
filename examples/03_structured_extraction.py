"""
Example 3: Structured Data Extraction with Pydantic
===================================================

This example demonstrates:
- Defining Pydantic models for data validation
- Using output_model_schema for structured extraction
- Parsing and validating extracted data
- The EXACT pattern used in twitter_source.py

This is how we extract tweets, Reddit posts, and other structured data.
"""

import asyncio
from typing import List

from browser_use import Agent, ChatOpenAI
from browser_use.browser.profile import BrowserProfile
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


# Define the structure of data you want to extract
class NewsArticle(BaseModel):
    """Schema for a news article - defines what fields to extract."""
    title: str
    url: str
    source: str | None = None
    summary: str | None = None
    published_date: str | None = None


class NewsCollection(BaseModel):
    """Container for multiple articles - this is the output_model_schema."""
    articles: List[NewsArticle]


async def extract_tesla_news():
    """Extract structured Tesla news using Pydantic models."""
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    
    # Define a clear, structured task
    task = """
    Go to Google News and search for 'Tesla stock'.
    
    Extract the TOP 5 news articles. For each article, collect:
    - title: The headline text
    - url: The full URL to the article
    - source: The publisher name (e.g., Reuters, Bloomberg)
    - summary: Brief description if available
    - published_date: When it was published (e.g., "2 hours ago")
    
    Skip any promoted or sponsored content.
    """
    
    profile = BrowserProfile(
        headless=False,
        minimum_wait_page_load_time=2.0
    )
    
    # The magic: output_model_schema tells the agent EXACTLY what structure to return
    agent = Agent(
        task=task,
        llm=llm,
        browser_profile=profile,
        output_model_schema=NewsCollection,  # ← This enforces structure!
        max_actions_per_step=10
    )
    
    print("🚀 Extracting Tesla news with structured output...")
    result = await agent.run(max_steps=15)
    
    # Parse the structured result
    news_data: NewsCollection | None = None
    
    # Try to get structured output from the result
    if hasattr(result, 'history') and hasattr(result.history, 'structured_output'):
        news_data = result.history.structured_output
    elif hasattr(result, 'final_result'):
        final = result.final_result() if callable(result.final_result) else result.final_result
        if isinstance(final, NewsCollection):
            news_data = final
        elif isinstance(final, dict) and 'articles' in final:
            news_data = NewsCollection(**final)
    
    if news_data is None:
        print("❌ No structured data returned")
        return
    
    # Display the extracted data
    print(f"\n✅ Extracted {len(news_data.articles)} articles:\n")
    
    for idx, article in enumerate(news_data.articles, 1):
        print(f"{idx}. {article.title}")
        print(f"   Source: {article.source or 'Unknown'}")
        print(f"   URL: {article.url}")
        if article.summary:
            print(f"   Summary: {article.summary[:100]}...")
        if article.published_date:
            print(f"   Published: {article.published_date}")
        print()
    
    # The data is already validated by Pydantic!
    # You can now store it in a database, process it, etc.
    return news_data


async def extract_reddit_posts():
    """Extract structured Reddit posts (similar to reddit_source.py)."""
    
    class RedditPost(BaseModel):
        """Schema for a Reddit post."""
        post_id: str = Field(description="Reddit post ID from URL")
        title: str
        author: str | None = None
        upvotes: int | None = None
        comments: int | None = None
        url: str
    
    class RedditCollection(BaseModel):
        """Container for multiple posts."""
        posts: List[RedditPost]
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    
    task = """
    Go to https://reddit.com/r/wallstreetbets
    
    Find the top 5 posts that mention TSLA or Tesla in the title.
    For each post, extract:
    - post_id: Extract from the URL (e.g., /comments/ABC123/... → "ABC123")
    - title: The post title
    - author: Username who posted it
    - upvotes: Number of upvotes
    - comments: Number of comments
    - url: Full URL to the post
    
    Skip pinned posts and stickied announcements.
    """
    
    profile = BrowserProfile(headless=False, minimum_wait_page_load_time=2.0)
    
    agent = Agent(
        task=task,
        llm=llm,
        browser_profile=profile,
        output_model_schema=RedditCollection,
        max_actions_per_step=10
    )
    
    print("\n🚀 Extracting Reddit posts with structured output...")
    result = await agent.run(max_steps=15)
    
    # Parse result (same pattern as above)
    reddit_data: RedditCollection | None = None
    
    if hasattr(result, 'history') and hasattr(result.history, 'structured_output'):
        reddit_data = result.history.structured_output
    
    if reddit_data:
        print(f"\n✅ Extracted {len(reddit_data.posts)} posts:\n")
        for idx, post in enumerate(reddit_data.posts, 1):
            print(f"{idx}. {post.title}")
            print(f"   Author: u/{post.author} | ⬆️  {post.upvotes} | 💬 {post.comments}")
            print(f"   {post.url}\n")
    else:
        print("❌ No structured data returned")


async def main():
    """Run structured extraction examples."""
    print("=" * 70)
    print("Structured Data Extraction Example")
    print("=" * 70)
    print("\n📚 This demonstrates:")
    print("  1. Pydantic model definition for type safety")
    print("  2. output_model_schema parameter for structured extraction")
    print("  3. Automatic data validation and parsing")
    print("\n💡 This is the CORE pattern in twitter_source.py and reddit_source.py\n")
    
    print("\nChoose an example:")
    print("1. Extract Tesla news articles")
    print("2. Extract Reddit posts about TSLA")
    print("3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        await extract_tesla_news()
    elif choice == "2":
        await extract_reddit_posts()
    elif choice == "3":
        await extract_tesla_news()
        await extract_reddit_posts()
    else:
        print("Invalid choice, running news extraction...")
        await extract_tesla_news()


if __name__ == "__main__":
    asyncio.run(main())

