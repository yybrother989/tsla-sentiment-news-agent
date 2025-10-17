from __future__ import annotations

from datetime import datetime
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.domain.schemas import SentimentAnalysisRecord, RedditSentimentRecord
from app.infra import get_logger, get_settings


class EmailContent(BaseModel):
    """LLM-generated email content."""
    
    subject: str = Field(description="Email subject line")
    executive_summary: str = Field(description="2-3 paragraph executive summary of the day's news")
    market_outlook: str = Field(description="Overall market sentiment and outlook paragraph")
    key_takeaways: List[str] = Field(description="3-5 bullet point key takeaways")
    action_items: List[str] = Field(description="2-3 suggested action items or insights")
    reddit_section: str = Field(description="Summary of top Reddit posts (if any)")


class EmailContentGenerator:
    """Generate dynamic, LLM-powered email content from news data."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            model=self.settings.planner_llm_model,
            api_key=self.settings.openai_api_key,
            temperature=0.7,  # More creative for email writing
        ).with_structured_output(EmailContent)

    async def generate_email_content(
        self,
        records: List[SentimentAnalysisRecord],
        reddit_posts: List[RedditSentimentRecord] = None,
        time_period: str = "24 hours"
    ) -> EmailContent:
        """Generate dynamic email content using LLM."""
        self.logger.info("Generating email content for %d articles", len(records))
        
        # Calculate statistics
        total = len(records)
        bullish_count = sum(1 for r in records if r.stance == 'bullish')
        bearish_count = sum(1 for r in records if r.stance == 'bearish')
        
        sentiment_scores = [r.sentiment_score for r in records if r.sentiment_score is not None]
        impact_scores = [r.impact_score for r in records if r.impact_score is not None]
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0.0
        
        # Get high impact articles
        high_impact = sorted(
            [r for r in records if r.impact_score and r.impact_score >= 4],
            key=lambda r: (r.impact_score or 0, abs(r.sentiment_score or 0)),
            reverse=True
        )[:5]
        
        # Prepare article summaries for LLM
        article_summaries = []
        for i, record in enumerate(records[:10], 1):  # Top 10 articles
            article_summaries.append(
                f"{i}. [{record.stance.upper() if record.stance else 'NEUTRAL'}] {record.title}\n"
                f"   Sentiment: {record.sentiment_score:+.2f} | Impact: {record.impact_score}/5\n"
                f"   Summary: {record.summary or 'N/A'}\n"
                f"   Analysis: {record.sentiment_rationale or 'N/A'}\n"
            )
        
        high_impact_summaries = []
        for i, record in enumerate(high_impact, 1):
            high_impact_summaries.append(
                f"{i}. {record.title} ({record.stance.upper() if record.stance else 'NEUTRAL'})\n"
                f"   Impact: {record.impact_score}/5 | Sentiment: {record.sentiment_score:+.2f}\n"
                f"   Summary: {record.summary or 'N/A'}\n"
            )
        
        # Prepare Reddit posts for LLM (if any)
        reddit_summaries = []
        if reddit_posts:
            for i, post in enumerate(reddit_posts[:5], 1):  # Top 5 Reddit posts
                reddit_summaries.append(
                    f"{i}. {post.title}\n"
                    f"   Author: u/{post.author_username or 'Unknown'} | "
                    f"Upvotes: {post.upvote_count or 0} | "
                    f"Comments: {post.comment_count or 0}\n"
                    f"   Posted: {post.posted_at.strftime('%Y-%m-%d %H:%M') if post.posted_at else 'Unknown'}\n"
                )
        
        # Create comprehensive prompt for LLM
        system_prompt = """You are a senior financial analyst writing a daily Tesla news briefing email for investors and executives.

Your task is to analyze the day's Tesla news and create a compelling, professional email that:
1. Provides clear, actionable insights
2. Highlights the most important developments
3. Explains market sentiment and potential impacts
4. Offers strategic recommendations

Write in a professional yet accessible tone. Be direct and fact-based, but engaging.
Focus on what matters most to Tesla investors and stakeholders."""

        user_prompt = f"""Create a daily Tesla news briefing email based on the following data:

**TIME PERIOD:** {time_period}
**TOTAL ARTICLES:** {total}

**MARKET SENTIMENT:**
- Bullish Articles: {bullish_count} ({bullish_count/total*100:.0f}%)
- Bearish Articles: {bearish_count} ({bearish_count/total*100:.0f}%)
- Average Sentiment: {avg_sentiment:+.2f} (scale: -1 to +1)
- Average Impact: {avg_impact:.1f}/5

**TOP ARTICLES:**
{"".join(article_summaries)}

**HIGH-IMPACT NEWS:**
{"".join(high_impact_summaries) if high_impact_summaries else "None"}

**REDDIT COMMUNITY BUZZ (Top Posts from Past Week by Upvotes):**
{"".join(reddit_summaries) if reddit_summaries else "No recent Reddit posts available"}

Generate:
1. **subject**: Catchy, informative subject line (60 chars max)
2. **executive_summary**: 2-3 paragraph executive summary covering:
   - Overall market sentiment and why
   - Key developments and their significance
   - Potential implications for Tesla's stock and business
3. **market_outlook**: One paragraph on the overall market outlook and sentiment direction
4. **key_takeaways**: 3-5 bullet points of the most important insights
5. **action_items**: 2-3 specific, actionable recommendations or insights for investors
6. **reddit_section**: Brief summary of what the Reddit community is discussing about Tesla (top posts from past week, if available)

Make it dynamic, context-aware, and tailored to the specific news of this period."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            content: EmailContent = await self.llm.ainvoke(messages)
            self.logger.info("Generated email content: %s", content.subject)
            return content
        except Exception as exc:
            self.logger.error("Failed to generate email content: %s", exc)
            # Return fallback content
            return EmailContent(
                subject=f"Tesla News Update - {datetime.now().strftime('%B %d, %Y')}",
                executive_summary=f"Daily update covering {total} Tesla news articles from the past {time_period}.",
                market_outlook="Market sentiment analysis unavailable.",
                key_takeaways=["News summary generation failed", "Please check the detailed report"],
                action_items=["Review the full report for details"]
            )


__all__ = ['EmailContentGenerator', 'EmailContent']

