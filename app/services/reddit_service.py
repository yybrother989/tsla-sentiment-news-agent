"""Reddit service for fetching top posts for email reports."""

from typing import List
from datetime import datetime, timedelta
from app.services.storage import StorageService
from app.domain.schemas import RedditSentimentRecord
from app.infra import get_logger


class RedditService:
    """Service for fetching Reddit posts for email reports."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.storage = StorageService()  # Uses default adapter
    
    async def get_top_reddit_posts(
        self, 
        ticker: str = "TSLA",
        limit: int = 5,
        days_back: int = 7
    ) -> List[RedditSentimentRecord]:
        """Fetch top Reddit posts for a ticker from the last N days."""
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            # Query top posts by upvotes from the specified date range
            posts = self.storage.adapter.table("reddit_sentiment").select("*").eq(
                "ticker", ticker
            ).gte(
                "posted_at", start_date.isoformat()
            ).lte(
                "posted_at", end_date.isoformat()
            ).order(
                "upvote_count", desc=True
            ).limit(limit).execute()
            
            if posts.data:
                return [
                    RedditSentimentRecord(**post) 
                    for post in posts.data
                ]
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching Reddit posts: {e}")
            return []
    
    async def get_latest_reddit_posts(
        self,
        ticker: str = "TSLA", 
        limit: int = 5
    ) -> List[RedditSentimentRecord]:
        """Fetch latest Reddit posts for a ticker."""
        
        try:
            posts = self.storage.adapter.table("reddit_sentiment").select("*").eq(
                "ticker", ticker
            ).order(
                "collected_at", desc=True
            ).limit(limit).execute()
            
            if posts.data:
                return [
                    RedditSentimentRecord(**post) 
                    for post in posts.data
                ]
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching latest Reddit posts: {e}")
            return []
