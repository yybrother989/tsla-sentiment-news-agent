from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from app.domain.schemas import SentimentAnalysisRecord, RedditSentimentRecord, TwitterSentimentRecord
from app.infra import get_logger, get_settings, setup_logging
from app.services.email_service import EmailService

app = typer.Typer(add_completion=False)


@app.command()
def send(
    days: int = typer.Option(1, help="Number of days to include in email"),
    recipient: Optional[str] = typer.Option(None, help="Recipient email (overrides env setting)"),
    generate_only: bool = typer.Option(False, help="Generate email preview without sending"),
) -> None:
    """Send Tesla news email notification with AI-generated summary."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger = get_logger(__name__)
    
    async def _send() -> None:
        console = Console()
        
        console.print(
            f"\n[bold cyan]📧 Preparing Tesla News Email Notification...[/bold cyan]\n"
        )
        
        # Determine recipient
        recipient_email = recipient or settings.recipient_emails
        if not recipient_email and not generate_only:
            console.print("[red]✗ No recipient email specified.[/red]")
            console.print("[yellow]Use --recipient or set RECIPIENT_EMAILS in .env[/yellow]")
            return
        
        # Fetch data from database
        if not settings.supabase_credentials:
            console.print("[red]✗ Supabase not configured.[/red]")
            return
        
        try:
            console.print(f"[cyan]→ Fetching articles from past {days} day(s)...[/cyan]")
            
            # Query articles from database
            from app.adapters.supabase_client import SupabaseAdapter
            adapter = SupabaseAdapter.default_adapter()
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            response = adapter.client.table('sentiment_analysis').select('*').gte(
                'published_at', start_date.isoformat()
            ).lte(
                'published_at', end_date.isoformat()
            ).eq(
                'user_id', settings.user_id
            ).order('published_at', desc=True).execute()
            
            if not response.data:
                console.print(f"[yellow]⚠ No articles found in the past {days} day(s).[/yellow]")
                console.print(f"[yellow]Run: python -m app.cli.fetch_news --days {days}[/yellow]")
                return
            
            records = [SentimentAnalysisRecord(**row) for row in response.data]
            console.print(f"[green]✓ Retrieved {len(records)} articles[/green]")
            
            # Fetch Reddit posts from database (top posts from past week by upvotes)
            console.print(f"[cyan]→ Fetching top Reddit posts from past week...[/cyan]")
            from datetime import timezone as tz
            end_date_utc = datetime.now(tz.utc)
            reddit_start = end_date_utc - timedelta(days=7)  # Always fetch from past week
            reddit_response = adapter.client.table('reddit_sentiment').select('*').gte(
                'collected_at', reddit_start.isoformat()
            ).lte(
                'collected_at', end_date_utc.isoformat()
            ).eq(
                'user_id', settings.user_id
            ).order('upvote_count', desc=True).limit(10).execute()
            
            reddit_posts = [RedditSentimentRecord(**row) for row in reddit_response.data] if reddit_response.data else []
            if reddit_posts:
                console.print(f"[green]✓ Retrieved {len(reddit_posts)} top Reddit posts (sorted by upvotes)[/green]")
            else:
                console.print(f"[yellow]⚠ No Reddit posts found in the past week.[/yellow]")
                console.print(f"[yellow]Run: python -m app.cli.reddit_sentiment reddit-sentiment[/yellow]")
            
            # Fetch Twitter posts from database (top posts from past week by engagement)
            console.print(f"[cyan]→ Fetching top Twitter posts from past week...[/cyan]")
            twitter_response = adapter.client.table('twitter_sentiment').select('*').gte(
                'collected_at', reddit_start.isoformat()
            ).lte(
                'collected_at', end_date_utc.isoformat()
            ).eq(
                'user_id', settings.user_id
            ).order('like_count', desc=True).limit(10).execute()
            
            twitter_posts = [TwitterSentimentRecord(**row) for row in twitter_response.data] if twitter_response.data else []
            if twitter_posts:
                console.print(f"[green]✓ Retrieved {len(twitter_posts)} top Twitter posts (sorted by likes)[/green]")
            else:
                console.print(f"[yellow]⚠ No Twitter posts found in the past week.[/yellow]")
                console.print(f"[yellow]Run: python -m app.cli.twitter_sentiment twitter-sentiment[/yellow]")
            
            console.print()
            
            # Calculate statistics for display
            bullish = sum(1 for r in records if r.stance == 'bullish')
            bearish = sum(1 for r in records if r.stance == 'bearish')
            neutral = sum(1 for r in records if r.stance == 'neutral')
            
            sentiment_scores = [r.sentiment_score for r in records if r.sentiment_score is not None]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            
            console.print(f"[bold]Quick Stats:[/bold]")
            console.print(f"  • 🐂 Bullish: {bullish}")
            console.print(f"  • 🐻 Bearish: {bearish}")
            console.print(f"  • ➖ Neutral: {neutral}")
            console.print(f"  • 📊 Avg Sentiment: {avg_sentiment:+.2f}\n")
            
            # Generate and send email
            email_service = EmailService()
            time_period = f"Past {days} day(s)" if days > 1 else "Past 24 hours"
            
            if generate_only:
                console.print("[cyan]→ Generating email preview (not sending)...[/cyan]")
                
                # Generate preview HTML
                from app.services.email_generator import EmailContentGenerator
                content_gen = EmailContentGenerator()
                llm_content = await content_gen.generate_email_content(records, reddit_posts, twitter_posts, time_period)
                
                # Save preview
                preview_dir = Path("email_previews")
                preview_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                preview_file = preview_dir / f"email_preview_{timestamp}.txt"
                
                preview_text = f"""
═══════════════════════════════════════════════════════════════
EMAIL PREVIEW
═══════════════════════════════════════════════════════════════

SUBJECT: {llm_content.subject}

EXECUTIVE SUMMARY:
{llm_content.executive_summary}

MARKET OUTLOOK:
{llm_content.market_outlook}

KEY TAKEAWAYS:
""" + "\n".join([f"  • {t}" for t in llm_content.key_takeaways]) + f"""

ACTION ITEMS:
""" + "\n".join([f"  • {a}" for a in llm_content.action_items]) + """

═══════════════════════════════════════════════════════════════
"""
                
                preview_file.write_text(preview_text)
                
                console.print(Panel(
                    f"[green]✅ Email preview generated![/green]\n\n"
                    f"[bold]Subject:[/bold] {llm_content.subject}\n\n"
                    f"[bold]Preview saved to:[/bold] {preview_file}\n\n"
                    f"Run without --generate-only to send the email.",
                    title="📧 Email Preview",
                    border_style="green"
                ))
                
            else:
                console.print(f"[cyan]→ Generating AI-powered email content...[/cyan]")
                
                # Split recipient emails if comma-separated
                recipients = [r.strip() for r in recipient_email.split(',')]
                
                for email in recipients:
                    console.print(f"[cyan]→ Sending email to {email}...[/cyan]")
                    
                    success = await email_service.send_email_notification(
                        records=records,
                        recipient_email=email,
                        reddit_posts=reddit_posts,
                        twitter_posts=twitter_posts,
                        time_period=time_period,
                        report_url=""
                    )
                    
                    if success:
                        console.print(f"[green]✓ Email sent successfully to {email}[/green]")
                    else:
                        console.print(f"[red]✗ Failed to send email to {email}[/red]")
                
                console.print()
                console.print(Panel.fit(
                    f"[green]✅ Email notification complete![/green]\n\n"
                    f"[bold]Recipients:[/bold] {', '.join(recipients)}\n"
                    f"[bold]Articles:[/bold] {len(records)}\n"
                    f"[bold]Time Period:[/bold] {time_period}",
                    title="📧 Email Sent",
                    border_style="green"
                ))
        
        except Exception as exc:
            logger.error("Failed to send email: %s", exc, exc_info=True)
            console.print(f"[red]✗ Error: {exc}[/red]")
    
    asyncio.run(_send())


if __name__ == "__main__":
    app()

