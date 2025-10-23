from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence

import httpx

from app.domain.schemas import TwitterTweet
from app.infra import get_logger, get_settings


class N8nCollectionError(RuntimeError):
    """Raised when n8n workflow execution fails."""
    pass


@dataclass
class TwitterSearchConfig:
    """Configuration for Twitter search via n8n + Apify."""
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


class N8nTwitterCollector:
    """
    Twitter collector that uses n8n workflow + Apify Twitter scraper.
    Replaces browser-use automation with API-based collection.
    """

    def __init__(self, config: TwitterSearchConfig) -> None:
        self.config = config
        self.settings = get_settings()
        self.logger = get_logger(self.__class__.__name__)

        # Validate n8n configuration
        if not self.settings.n8n_base_url:
            raise N8nCollectionError("N8N_BASE_URL is not configured - add to .env file")

    async def collect(self) -> Sequence[TwitterTweet]:
        """
        Execute n8n workflow to collect tweets via Apify.
        
        Returns:
            Sequence of TwitterTweet domain models
            
        Raises:
            N8nCollectionError: If workflow execution or data transformation fails
        """
        self.logger.info("Starting n8n Twitter collection for query: %s", self.config.query)

        try:
            # Call n8n workflow
            raw_data = await self._call_n8n_workflow()
            
            # Transform Apify data to TwitterTweet models
            tweets = self._transform_apify_to_tweets(raw_data)
            
            self.logger.info("Successfully collected %d tweets via n8n", len(tweets))
            return tweets

        except Exception as exc:
            self.logger.error("n8n Twitter collection failed: %s", exc, exc_info=True)
            raise N8nCollectionError(f"Failed to collect tweets via n8n: {exc}") from exc

    async def _call_n8n_workflow(self) -> Dict[str, Any]:
        """
        Execute n8n workflow via REST API.
        
        Returns:
            Raw JSON response from n8n workflow
            
        Raises:
            N8nCollectionError: If API call fails or returns invalid data
        """
        # Use production webhook URL (not /webhook-test/)
        base_url = self.settings.n8n_base_url.rstrip('/')
        url = f"{base_url}/webhook/twitter-scraper"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        # Format dates for Twitter advanced search (YYYY-MM-DD format)
        # Twitter expects: since:2021-12-31 until:2021-12-31
        since_formatted = self.config.since  # Already in YYYY-MM-DD format
        until_formatted = self.config.until   # Already in YYYY-MM-DD format
        
        # Payload matches Apify Twitter Scraper actor input schema
        # Use "Top" search type to get more popular tweets (better engagement)
        payload = {
            "author": "tesla",  # Add author field for n8n mapping
            "searchTerms": [self.config.query],  # Array of search terms
            "since": since_formatted,
            "until": until_formatted,
            "lang": self.config.lang or "en",
            "queryType": "Top",  # Changed from "Latest" to "Top" for better engagement
            "min_replies": self.config.min_replies or 0,  # Correct Apify field name
            "min_faves": self.config.min_faves or 0,      # Correct Apify field name
            "min_retweets": self.config.min_retweets or 0, # Correct Apify field name
            "maxItems": self.config.target_count,        # Apify field name for tweet count
        }
        
        self.logger.info("Calling n8n webhook with payload: %s", payload)
        
        self.logger.info("Calling n8n workflow: %s", url)
        self.logger.debug("Request payload: %s", payload)
        
        try:
            async with httpx.AsyncClient(timeout=self.settings.n8n_timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                # Log response details
                self.logger.info("n8n response status: %d", response.status_code)
                
                if response.status_code == 401:
                    raise N8nCollectionError(
                        "Authentication failed. Webhooks don't need API keys, check if webhook is active."
                    )
                elif response.status_code == 404:
                    raise N8nCollectionError(
                        f"Webhook not found. Check webhook URL: {url}"
                    )
                elif response.status_code >= 500:
                    raise N8nCollectionError(
                        f"n8n server error (status {response.status_code}). Try again later."
                    )
                elif response.status_code != 200:
                    raise N8nCollectionError(
                        f"Unexpected response status: {response.status_code}"
                    )
                
                # Log raw response for debugging
                response_text = response.text
                self.logger.info("n8n raw response: %s", response_text[:1000])
                
                if not response_text.strip():
                    raise N8nCollectionError("n8n returned empty response")
                
                try:
                    data = response.json()
                    self.logger.debug("n8n response data keys: %s", list(data.keys()) if isinstance(data, dict) else type(data))
                    self.logger.debug("n8n response preview: %s", str(data)[:500])
                    return data
                except Exception as json_exc:
                    self.logger.error("Failed to parse n8n response as JSON: %s", json_exc)
                    self.logger.error("Raw response: %s", response_text)
                    raise N8nCollectionError(f"Invalid JSON response from n8n: {json_exc}")
                
        except httpx.TimeoutException as exc:
            raise N8nCollectionError(
                f"n8n workflow timed out after {self.settings.n8n_timeout_seconds} seconds"
            ) from exc
        except httpx.RequestError as exc:
            raise N8nCollectionError(
                f"Network error calling n8n API: {exc}"
            ) from exc

    def _transform_apify_to_tweets(self, raw_data: Dict[str, Any]) -> Sequence[TwitterTweet]:
        """
        Transform Apify Twitter scraper output to TwitterTweet domain models.
        
        Args:
            raw_data: Raw JSON response from n8n workflow containing Apify data
            
        Returns:
            List of TwitterTweet models
            
        Raises:
            N8nCollectionError: If data structure is invalid or transformation fails
        """
        tweets: List[TwitterTweet] = []
        seen_ids: set[str] = set()
        
        # Extract tweets from n8n response
        # Expected format: {"data": {"tweets": [...]}} or {"tweets": [...]} or direct array
        tweet_list = self._extract_tweet_list(raw_data)
        
        if not tweet_list:
            self.logger.warning("No tweets found in n8n response")
            return []
        
        self.logger.info("Processing %d tweets from Apify", len(tweet_list))
        
        for idx, raw_tweet in enumerate(tweet_list, start=1):
            try:
                tweet = self._parse_single_tweet(raw_tweet)
                
                # Skip duplicates
                if tweet.tweet_id in seen_ids:
                    self.logger.debug("Skipping duplicate tweet: %s", tweet.tweet_id)
                    continue
                
                tweets.append(tweet)
                seen_ids.add(tweet.tweet_id)
                
            except Exception as exc:
                self.logger.warning(
                    "Failed to parse tweet #%d: %s (raw: %s)",
                    idx,
                    exc,
                    str(raw_tweet)[:200]
                )
                continue
        
        self.logger.info("Successfully transformed %d/%d tweets", len(tweets), len(tweet_list))
        return tweets

    def _extract_tweet_list(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tweet list from various possible n8n response formats."""
        
        # Try multiple extraction paths
        if isinstance(raw_data, list):
            # Direct array of tweets
            tweet_list = raw_data
        elif isinstance(raw_data, dict):
            # Try nested paths
            if "data" in raw_data:
                data = raw_data["data"]
                if isinstance(data, dict) and "tweets" in data:
                    tweet_list = data["tweets"]
                elif isinstance(data, list):
                    tweet_list = data
                else:
                    tweet_list = []
            elif "tweets" in raw_data:
                tweet_list = raw_data["tweets"]
            else:
                tweet_list = []
        else:
            tweet_list = []
        
        if not tweet_list:
            return []
        
        # CRITICAL FIX: Apply client-side filtering since Apify actor ignores filters
        filtered_tweets = self._apply_engagement_filters(tweet_list)
        
        # Limit results since maxItems doesn't work with this actor
        if filtered_tweets:
            original_count = len(tweet_list)
            filtered_count = len(filtered_tweets)
            limited_list = filtered_tweets[:self.config.target_count]
            
            self.logger.info(
                "Apify returned %d tweets, %d met engagement criteria, limiting to %d as requested", 
                original_count, filtered_count, len(limited_list)
            )
            return limited_list
        
        return filtered_tweets
    
    def _apply_engagement_filters(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply engagement filters client-side since Apify actor ignores them."""
        
        filtered_tweets = []
        
        for tweet in tweets:
            # Extract engagement metrics
            replies = tweet.get('replyCount', 0)
            likes = tweet.get('likeCount', 0) 
            retweets = tweet.get('retweetCount', 0)
            
            # Apply filters
            meets_replies = replies >= (self.config.min_replies or 0)
            meets_likes = likes >= (self.config.min_faves or 0)
            meets_retweets = retweets >= (self.config.min_retweets or 0)
            
            if meets_replies and meets_likes and meets_retweets:
                filtered_tweets.append(tweet)
                self.logger.debug(
                    "Tweet meets criteria: replies=%d (>=%d), likes=%d (>=%d), retweets=%d (>=%d)",
                    replies, self.config.min_replies or 0,
                    likes, self.config.min_faves or 0, 
                    retweets, self.config.min_retweets or 0
                )
            else:
                self.logger.debug(
                    "Tweet filtered out: replies=%d (need>=%d), likes=%d (need>=%d), retweets=%d (need>=%d)",
                    replies, self.config.min_replies or 0,
                    likes, self.config.min_faves or 0,
                    retweets, self.config.min_retweets or 0
                )
        
        return filtered_tweets

    def _parse_single_tweet(self, raw_tweet: Dict[str, Any]) -> TwitterTweet:
        """
        Parse a single Apify tweet into TwitterTweet model.
        
        Apify Twitter Scraper typically returns:
        {
            "id": "tweet_id",
            "url": "https://twitter.com/...",
            "conversationId": "...",
            "author": {
                "id": "...",
                "userName": "handle",
                "name": "Display Name"
            },
            "text": "...",
            "lang": "en",
            "createdAt": "2025-10-16T12:00:00.000Z",
            "replyCount": 10,
            "retweetCount": 20,
            "likeCount": 100,
            "quoteCount": 5,
            "bookmarkCount": 2,
            "viewCount": 1000,
            "hashtags": ["tag1", "tag2"],
            "mentions": [{"username": "user1"}]
        }
        """
        
        # Extract tweet ID (required)
        tweet_id = self._extract_field(raw_tweet, ["id", "tweetId", "tweet_id"], required=True)
        
        # Extract URL (required, must be valid)
        tweet_url = self._extract_field(raw_tweet, ["url", "tweetUrl", "tweet_url"], required=True)
        if not tweet_url.startswith("http"):
            raise ValueError(f"Invalid tweet URL: {tweet_url}")
        
        # Extract author information
        author_data = raw_tweet.get("author", {})
        if isinstance(author_data, dict):
            author_id = author_data.get("id") or author_data.get("userId")
            author_handle = author_data.get("userName") or author_data.get("username")
            author_name = author_data.get("name") or author_data.get("displayName")
            author_username = author_handle  # Use handle as username
        else:
            author_id = self._extract_field(raw_tweet, ["authorId", "author_id"])
            author_handle = self._extract_field(raw_tweet, ["authorHandle", "author_handle", "username"])
            author_name = self._extract_field(raw_tweet, ["authorName", "author_name", "displayName"])
            author_username = author_handle
        
        # Extract text (required)
        text = self._extract_field(raw_tweet, ["text", "fullText", "full_text"], required=True)
        
        # Extract timestamp (required)
        timestamp_str = self._extract_field(raw_tweet, ["createdAt", "created_at", "timestamp"], required=True)
        posted_at = self._parse_timestamp(timestamp_str)
        
        # Extract engagement metrics
        like_count = self._extract_int(raw_tweet, ["likeCount", "like_count", "favoriteCount"])
        reply_count = self._extract_int(raw_tweet, ["replyCount", "reply_count"])
        retweet_count = self._extract_int(raw_tweet, ["retweetCount", "retweet_count"])
        quote_count = self._extract_int(raw_tweet, ["quoteCount", "quote_count"])
        bookmark_count = self._extract_int(raw_tweet, ["bookmarkCount", "bookmark_count"])
        view_count = self._extract_int(raw_tweet, ["viewCount", "view_count", "impressionCount"])
        
        # Extract hashtags and mentions
        hashtags = self._extract_hashtags(raw_tweet)
        mentions = self._extract_mentions(raw_tweet)
        
        # Extract language
        language = self._extract_field(raw_tweet, ["lang", "language"])
        
        # Extract conversation ID
        conversation_id = self._extract_field(raw_tweet, ["conversationId", "conversation_id"])
        
        return TwitterTweet(
            tweet_id=tweet_id,
            tweet_url=tweet_url,
            conversation_id=conversation_id,
            author_id=author_id,
            author_handle=author_handle,
            author_name=author_name,
            author_username=author_username,
            text=text,
            language=language,
            hashtags=hashtags,
            mentions=mentions,
            like_count=like_count,
            reply_count=reply_count,
            retweet_count=retweet_count,
            quote_count=quote_count,
            bookmark_count=bookmark_count,
            view_count=view_count,
            posted_at=posted_at,
            collected_at=datetime.now(timezone.utc),
            raw_payload=raw_tweet,
        )

    def _extract_field(
        self,
        data: Dict[str, Any],
        keys: List[str],
        required: bool = False
    ) -> str | None:
        """Extract field from dict trying multiple possible key names."""
        for key in keys:
            if key in data and data[key]:
                return str(data[key])
        
        if required:
            raise ValueError(f"Required field not found. Tried keys: {keys}")
        return None

    def _extract_int(self, data: Dict[str, Any], keys: List[str]) -> int | None:
        """Extract integer field from dict trying multiple possible key names."""
        for key in keys:
            if key in data:
                try:
                    return int(data[key])
                except (ValueError, TypeError):
                    continue
        return None

    def _extract_hashtags(self, raw_tweet: Dict[str, Any]) -> List[str]:
        """Extract hashtags from various possible formats."""
        hashtags_raw = raw_tweet.get("hashtags", [])
        
        if isinstance(hashtags_raw, list):
            # Could be list of strings or list of dicts
            result = []
            for item in hashtags_raw:
                if isinstance(item, str):
                    result.append(item.lstrip("#"))
                elif isinstance(item, dict) and "text" in item:
                    result.append(item["text"].lstrip("#"))
            return result
        
        # Try extracting from text as fallback
        text = raw_tweet.get("text", "")
        if text:
            return [tag.lstrip("#") for tag in re.findall(r"#(\w+)", text)]
        
        return []

    def _extract_mentions(self, raw_tweet: Dict[str, Any]) -> List[str]:
        """Extract mentions from various possible formats."""
        mentions_raw = raw_tweet.get("mentions", [])
        
        if isinstance(mentions_raw, list):
            # Could be list of strings or list of dicts
            result = []
            for item in mentions_raw:
                if isinstance(item, str):
                    result.append(item.lstrip("@"))
                elif isinstance(item, dict):
                    username = item.get("username") or item.get("userName") or item.get("screen_name")
                    if username:
                        result.append(username.lstrip("@"))
            return result
        
        # Try extracting from text as fallback
        text = raw_tweet.get("text", "")
        if text:
            return [mention.lstrip("@") for mention in re.findall(r"@(\w+)", text)]
        
        return []

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse timestamp from Apify format.
        
        Apify returns various formats:
        - ISO 8601: "2025-10-16T12:00:00.000Z"
        - Twitter format: "Tue Oct 21 19:08:05 +0000 2025"
        """
        try:
            # Try Twitter format first (most common from this actor)
            # Format: "Tue Oct 21 19:08:05 +0000 2025"
            if " +0000 " in timestamp_str and len(timestamp_str.split()) == 6:
                dt = datetime.strptime(timestamp_str, "%a %b %d %H:%M:%S %z %Y")
                return dt.astimezone(timezone.utc)
            
            # Try ISO 8601 format
            if timestamp_str.endswith("Z"):
                # Replace Z with +00:00 for Python parsing
                timestamp_str = timestamp_str[:-1] + "+00:00"
            
            dt = datetime.fromisoformat(timestamp_str)
            
            # Ensure timezone is UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            
            return dt
            
        except Exception as exc:
            self.logger.warning("Failed to parse timestamp '%s': %s", timestamp_str, exc)
            # Fallback to current time
            return datetime.now(timezone.utc)


async def fetch_tweets(config: TwitterSearchConfig) -> Sequence[TwitterTweet]:
    """
    Fetch tweets via n8n + Apify integration.
    
    This is the main entry point that maintains compatibility with the existing
    sentiment analysis pipeline.
    """
    collector = N8nTwitterCollector(config)
    return await collector.collect()


__all__ = [
    "N8nCollectionError",
    "TwitterSearchConfig",
    "N8nTwitterCollector",
    "fetch_tweets",
]

