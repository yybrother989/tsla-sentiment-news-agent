from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader

from app.domain.schemas import SentimentAnalysisRecord, RedditSentimentRecord
from app.infra import get_logger, get_settings
from app.services.email_generator import EmailContent, EmailContentGenerator


class EmailService:
    """Service for sending Tesla news email notifications."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        
        # Setup Jinja2 for email templates
        template_dir = Path(__file__).parent.parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def _calculate_stats(self, records: List[SentimentAnalysisRecord]) -> dict:
        """Calculate statistics for email."""
        total = len(records)
        
        bullish_count = sum(1 for r in records if r.stance == 'bullish')
        bearish_count = sum(1 for r in records if r.stance == 'bearish')
        neutral_count = sum(1 for r in records if r.stance == 'neutral')
        
        sentiment_scores = [r.sentiment_score for r in records if r.sentiment_score is not None]
        impact_scores = [r.impact_score for r in records if r.impact_score is not None]
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0.0
        
        return {
            'total_articles': total,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': neutral_count,
            'avg_sentiment': avg_sentiment,  # Keep as float for template comparisons
            'avg_sentiment_display': f"{avg_sentiment:+.2f}",  # Formatted string for display
            'avg_impact': avg_impact,  # Keep as float
            'avg_impact_display': f"{avg_impact:.1f}",  # Formatted string for display
        }

    async def send_email_notification(
        self,
        records: List[SentimentAnalysisRecord],
        recipient_email: str,
        reddit_posts: List[RedditSentimentRecord] = None,
        time_period: str = "24 hours",
        report_url: str = ""
    ) -> bool:
        """Send email notification with Tesla news summary."""
        try:
            self.logger.info("Generating email content for %d articles", len(records))
            
            # Generate LLM-powered content
            content_generator = EmailContentGenerator()
            llm_content: EmailContent = await content_generator.generate_email_content(
                records, reddit_posts, time_period
            )
            
            # Calculate statistics
            stats = self._calculate_stats(records)
            
            # Get top 5 articles by impact
            top_articles = sorted(
                records,
                key=lambda r: (r.impact_score or 0, abs(r.sentiment_score or 0)),
                reverse=True
            )[:5]
            
            # Render HTML email
            template = self.env.get_template('email_notification.html')
            
            # Convert newlines to <br> for HTML
            executive_summary_html = llm_content.executive_summary.replace('\n\n', '</p><p>').replace('\n', '<br>')
            market_outlook_html = llm_content.market_outlook.replace('\n', '<br>')
            
            # Convert Reddit section to HTML
            reddit_section_html = llm_content.reddit_section.replace('\n', '<br>') if llm_content.reddit_section else ""
            
            # Get top 3 Reddit posts for direct display
            top_reddit_posts = reddit_posts[:3] if reddit_posts else []
            
            html_content = template.render(
                subject=llm_content.subject,
                report_date=Path(__file__).parent.parent.parent.name,
                time_period=time_period,
                executive_summary=f"<p>{executive_summary_html}</p>",
                market_outlook=market_outlook_html,
                reddit_section=reddit_section_html,
                top_reddit_posts=top_reddit_posts,
                key_takeaways=llm_content.key_takeaways,
                action_items=llm_content.action_items,
                top_articles=top_articles,
                report_url=report_url or "#",
                **stats
            )
            
            # Create plain text version
            plain_text = self._create_plain_text_email(llm_content, stats, top_articles)
            
            # Send email
            success = self._send_smtp_email(
                recipient_email=recipient_email,
                subject=llm_content.subject,
                html_content=html_content,
                plain_text=plain_text
            )
            
            if success:
                self.logger.info("Email sent successfully to %s", recipient_email)
            else:
                self.logger.error("Failed to send email to %s", recipient_email)
            
            return success
            
        except Exception as exc:
            self.logger.error("Failed to send email notification: %s", exc, exc_info=True)
            return False

    def _create_plain_text_email(
        self,
        content: EmailContent,
        stats: dict,
        top_articles: List[SentimentAnalysisRecord]
    ) -> str:
        """Create plain text version of email."""
        text_parts = [
            "=" * 60,
            "TESLA NEWS BRIEFING",
            "=" * 60,
            "",
            f"📊 STATISTICS",
            f"Total Articles: {stats['total_articles']}",
            f"Bullish: {stats['bullish_count']} | Bearish: {stats['bearish_count']} | Neutral: {stats['neutral_count']}",
            f"Avg Sentiment: {stats['avg_sentiment_display']} | Avg Impact: {stats['avg_impact_display']}/5",
            "",
            "📝 EXECUTIVE SUMMARY",
            "-" * 60,
            content.executive_summary,
            "",
            "📈 MARKET OUTLOOK",
            "-" * 60,
            content.market_outlook,
            "",
            "💡 KEY TAKEAWAYS",
            "-" * 60,
        ]
        
        for i, takeaway in enumerate(content.key_takeaways, 1):
            text_parts.append(f"{i}. {takeaway}")
        
        text_parts.extend([
            "",
            "🔥 TOP STORIES",
            "-" * 60,
        ])
        
        for i, article in enumerate(top_articles, 1):
            stance = article.stance.upper() if article.stance else "NEUTRAL"
            text_parts.extend([
                f"{i}. [{stance}] {article.title}",
                f"   Impact: {article.impact_score}/5 | Sentiment: {article.sentiment_score:+.2f}",
                f"   {article.summary or 'No summary'}",
                ""
            ])
        
        text_parts.extend([
            "🎯 ACTION ITEMS",
            "-" * 60,
        ])
        
        for i, action in enumerate(content.action_items, 1):
            text_parts.append(f"{i}. {action}")
        
        text_parts.extend([
            "",
            "=" * 60,
            "Tesla Sentiment News Agent | Powered by AI",
            "=" * 60,
        ])
        
        return "\n".join(text_parts)

    def _send_smtp_email(
        self,
        recipient_email: str,
        subject: str,
        html_content: str,
        plain_text: str
    ) -> bool:
        """Send email via SMTP."""
        try:
            # Get email configuration from settings
            smtp_host = self.settings.smtp_host if hasattr(self.settings, 'smtp_host') else 'smtp.gmail.com'
            smtp_port = self.settings.smtp_port if hasattr(self.settings, 'smtp_port') else 587
            smtp_user = self.settings.smtp_user if hasattr(self.settings, 'smtp_user') else None
            smtp_password = self.settings.smtp_password if hasattr(self.settings, 'smtp_password') else None
            sender_email = self.settings.sender_email if hasattr(self.settings, 'sender_email') else smtp_user
            
            if not smtp_user or not smtp_password:
                self.logger.error("SMTP credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"Tesla News Agent <{sender_email}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(plain_text, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as exc:
            self.logger.error("SMTP send failed: %s", exc)
            return False


__all__ = ['EmailService']

