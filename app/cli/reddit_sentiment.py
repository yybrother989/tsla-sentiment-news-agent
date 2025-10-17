from __future__ import annotations

import asyncio
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Sequence

import typer
from rich.console import Console
from rich.table import Table

from app.adapters.reddit_source import (
    RedditCollectionError,
    RedditSearchConfig,
    fetch_reddit_posts,
)
from app.domain.schemas import RedditSentimentRecord, RedditPost
from app.infra import get_logger, get_settings, setup_logging
from app.infra.telemetry import timed_span
from app.services.scorer import SentimentAnalyzer
from app.services.storage import StorageService

app = typer.Typer(add_completion=False)


async def _analyze_posts(
    posts: Sequence[RedditPost],
    analyzer: SentimentAnalyzer | None,
) -> List[RedditSentimentRecord]:
    """Analyze sentiment for collected Reddit posts."""
    enriched: List[RedditSentimentRecord] = []

    for post in posts:
        if analyzer:
            doc = post.to_collector_document()
            result = await analyzer.score(doc)
            
            enriched.append(
                RedditSentimentRecord.from_post(
                    post=post,
                    ticker="TSLA",
                    sentiment_score=result.score,
                    sentiment_label=result.label,
                    sentiment_confidence=result.confidence,
                    sentiment_rationale=result.rationale,
                    key_themes=result.themes or [],
                )
            )
        else:
            # No analyzer - just store the post data
            enriched.append(
                RedditSentimentRecord.from_post(
                    post=post,
                    ticker="TSLA",
                )
            )

    return enriched


def _label_from_score(score: float | None) -> str:
    """Backfill sentiment label from score."""
    if score is None:
        return "neutral"
    if score > 0.2:
        return "bullish"
    elif score < -0.2:
        return "bearish"
    return "neutral"


def _compute_sentiment_index(records: Sequence[RedditSentimentRecord]) -> float:
    """Compute weighted sentiment index from Reddit posts."""
    if not records:
        return 0.0

    weighted_sum = 0.0
    total_weight = 0.0

    for record in records:
        if record.sentiment_score is not None:
            # Weight by engagement (upvotes + comments)
            engagement = (record.upvote_count or 0) + (record.comment_count or 0) * 2
            weight = max(1.0, engagement / 100.0)
            
            weighted_sum += record.sentiment_score * weight
            total_weight += weight

    return weighted_sum / total_weight if total_weight > 0 else 0.0


def _build_console_table(records: Sequence[RedditSentimentRecord]) -> Table:
    """Build a rich console table for display."""
    table = Table(title="Reddit Sentiment Analysis (r/wallstreetbets)", show_lines=True)

    table.add_column("Author", style="cyan", no_wrap=True)
    table.add_column("Engagement", style="magenta")
    table.add_column("Sentiment", style="green", justify="center")
    table.add_column("Title", style="white")

    for record in records:
        engagement = (
            f"⬆️ {record.upvote_count or 0} "
            f"💬 {record.comment_count or 0}"
        )
        sentiment = record.sentiment_score
        sentiment_display = f"{sentiment:+.2f}" if sentiment is not None else "N/A"

        author_display = f"u/{record.author_username}" if record.author_username else "Unknown"
        
        table.add_row(
            author_display,
            engagement,
            sentiment_display,
            record.title[:100] + ("…" if len(record.title) > 100 else ""),
        )

    return table


def _save_markdown_report(
    *,
    records: Sequence[RedditSentimentRecord],
    sentiment_index: float,
    output_dir: Path,
    config: RedditSearchConfig,
) -> Path:
    """Generate and save a Markdown summary of Reddit sentiment results."""
    output_dir.mkdir(exist_ok=True, parents=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"reddit_sentiment_{timestamp}.md"

    counts = Counter(r.sentiment_label or "unknown" for r in records)

    template = f"""# Reddit Sentiment Report - r/{config.subreddit}

**Generated:** {datetime.now().isoformat()}  
**Subreddit:** r/{config.subreddit}  
**Sort:** {config.sort_by} ({config.time_filter})  
**Posts Analyzed:** {len(records)}  
**Sentiment Index:** {sentiment_index:+.2f}

## Sentiment Breakdown
- **Bullish:** {counts.get('bullish', 0)} posts
- **Bearish:** {counts.get('bearish', 0)} posts  
- **Neutral:** {counts.get('neutral', 0)} posts

## Top Posts by Sentiment

### Bullish Examples
"""

    bullish_examples = [r for r in records if r.sentiment_label == "bullish"][:3]
    bearish_examples = [r for r in records if r.sentiment_label == "bearish"][:3]
    neutral_examples = [r for r in records if r.sentiment_label == "neutral"][:3]

    def format_section(items: Sequence[RedditSentimentRecord]) -> str:
        lines = []
        for record in items:
            author_display = f"u/{record.author_username}" if record.author_username else 'unknown'
            lines.append(
                f"- **{record.title}** by {author_display} ({record.posted_at.isoformat()}):\n"
                f"  ⬆️ {record.upvote_count or 0} upvotes | 💬 {record.comment_count or 0} comments | URL: {record.post_url}\n"
                f"  {record.text[:200] + '...' if record.text and len(record.text) > 200 else record.text or '_No body text_'}"
            )
        if not lines:
            lines.append("- _None available_")
        return "\n".join(lines)

    template += format_section(bullish_examples)
    template += "\n\n### Bearish Examples\n"
    template += format_section(bearish_examples)
    template += "\n\n### Neutral Examples\n"
    template += format_section(neutral_examples)

    template += f"""

## Summary
The sentiment index of {sentiment_index:+.2f} indicates a {"bullish" if sentiment_index > 0.3 else "bearish" if sentiment_index < -0.3 else "neutral or mixed"} tone in r/{config.subreddit} discussions about Tesla/TSLA.

---
*Report generated by TSLA Sentiment News Agent*
"""

    filename.write_text(template.strip() + "\n", encoding="utf-8")
    return filename


@app.command()
def reddit_login_simple() -> None:
    """Simple cookie-based login for Reddit - paste cookies from your browser (RECOMMENDED)."""
    
    from pathlib import Path
    import json
    from datetime import datetime, timedelta
    
    console = Console()
    
    console.print("\n[bold cyan]🍪 Simple Reddit Cookie Setup (Recommended)[/bold cyan]\n")
    console.print("[yellow]Instructions:[/yellow]")
    console.print("  1. Open Reddit in your regular browser and log in")
    console.print("  2. Install Cookie-Editor extension (same as Twitter)")
    console.print("  3. Export cookies for reddit.com")
    console.print("  4. Paste the cookie content below\n")
    
    console.print("[cyan]Paste your cookies (JSON format from extension), then press Enter twice:[/cyan]\n")
    
    lines = []
    try:
        while True:
            line = input()
            if not line and lines:
                break
            lines.append(line)
    except EOFError:
        pass
    
    cookie_text = '\n'.join(lines)
    
    if not cookie_text.strip():
        console.print("[red]✗ No cookies provided[/red]")
        return
    
    try:
        # Try to parse as JSON
        cookie_data = json.loads(cookie_text)
        
        # Convert to Playwright storage format
        if isinstance(cookie_data, list):
            cookies = cookie_data
        elif isinstance(cookie_data, dict) and 'cookies' in cookie_data:
            cookies = cookie_data['cookies']
        else:
            console.print("[red]✗ Invalid cookie format[/red]")
            return
        
        # Create storage state
        storage_state = {
            'cookies': cookies,
            'origins': []
        }
        
        cache_dir = Path("cache")
        cache_dir.mkdir(exist_ok=True)
        session_cache = cache_dir / "reddit_session.json"
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'storage_state': storage_state
        }
        
        with open(session_cache, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        console.print(f"\n[green]✓ Session saved to {session_cache}[/green]")
        console.print(f"[dim]Saved {len(cookies)} cookies[/dim]")
        console.print(f"[dim]Valid for 24 hours (expires: {(datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M')})[/dim]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  • Verify: [cyan]python -m app.cli.reddit_sentiment reddit-sentiment --check-cache[/cyan]")
        console.print("  • Collect: [cyan]python -m app.cli.reddit_sentiment reddit-sentiment[/cyan]\n")
        
    except json.JSONDecodeError as e:
        console.print(f"[red]✗ Invalid JSON format: {e}[/red]")
        console.print("[yellow]💡 Make sure to export cookies in JSON format from the browser extension[/yellow]")


@app.command()
def reddit_sentiment(
    query: str = typer.Option("TSLA OR Tesla", help="Search query for Reddit"),
    subreddit: str = typer.Option("wallstreetbets", help="Subreddit to search in (without r/)"),
    sort: str = typer.Option("top", help="Sort by: top, new, hot, comments, relevance"),
    min_upvotes: int = typer.Option(0, help="Minimum upvotes filter (0 = no filter)"),
    min_comments: int = typer.Option(0, help="Minimum comments filter (0 = no filter)"),
    target: int = typer.Option(50, help="Target post count"),
    scrolls: int = typer.Option(5, help="Maximum scroll attempts"),
    save_markdown: bool = typer.Option(True, help="Persist Markdown report to reports/"),
    clear_cache: bool = typer.Option(False, help="Clear cached Reddit session"),
    check_cache: bool = typer.Option(False, help="Check cache status and exit")
) -> None:
    """Search r/wallstreetbets for Tesla posts and analyze sentiment."""

    settings = get_settings()
    setup_logging(settings.log_level)
    logger = get_logger(__name__)
    console = Console()

    async def _run() -> None:
        # Check cache status if requested
        if check_cache:
            cache_file = Path("cache/reddit_session.json")
            if cache_file.exists():
                try:
                    import json
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
                    expires_at = cache_time + timedelta(hours=24)
                    time_left = expires_at - datetime.now()
                    
                    if time_left.total_seconds() > 0:
                        console.print(f"[green]✓ Reddit session cache is valid[/green]")
                        console.print(f"[cyan]  Expires in: {time_left}[/cyan]")
                        console.print(f"[cyan]  Created: {cache_time.strftime('%Y-%m-%d %H:%M:%S')}[/cyan]")
                    else:
                        console.print(f"[yellow]⚠ Reddit session cache is expired[/yellow]")
                        console.print(f"[cyan]  Expired: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}[/cyan]")
                except Exception as exc:
                    console.print(f"[red]✗ Cache file is corrupted: {exc}[/red]")
            else:
                console.print("[yellow]⚠ No Reddit session cache found (browsing as guest is OK for Reddit)[/yellow]")
            return

        # Clear cache if requested
        if clear_cache:
            cache_file = Path("cache/reddit_session.json")
            if cache_file.exists():
                cache_file.unlink()
                console.print("[yellow]✓ Cleared Reddit session cache[/yellow]\n")
        
        config = RedditSearchConfig(
            subreddit=subreddit,
            search_query=query,
            sort_by=sort,
            time_filter="past week",  # Fixed to past week
            min_upvotes=min_upvotes,
            min_comments=min_comments,
            target_count=target,
            max_scrolls=scrolls,
        )

        # Check cache status
        cache_file = Path("cache/reddit_session.json")
        has_cache = cache_file.exists()
        
        if has_cache:
            console.print(f"\n[bold cyan]🔍 Searching r/{subreddit} for '{query}' via Browser-Use (using cached session)...[/bold cyan]\n")
        else:
            console.print(f"\n[bold cyan]🔍 Searching r/{subreddit} for '{query}' via Browser-Use (guest mode)...[/bold cyan]\n")
            console.print("[dim]💡 Reddit allows browsing without login. For voting/commenting, use reddit-login-simple[/dim]\n")

        try:
            with timed_span("reddit-collection"):
                posts = await fetch_reddit_posts(config)
            
            if not posts:
                console.print("[yellow]⚠️ No posts collected. Try adjusting filters or search query.[/yellow]")
                return
            
            console.print(f"[green]✅ Collected {len(posts)} Reddit posts[/green]")
            
            # Save to Supabase
            from app.services.storage import StorageService
            from app.domain.schemas import RedditSentimentRecord
            
            storage = StorageService()  # Uses default adapter
            
            # Convert posts to RedditSentimentRecord (without sentiment analysis)
            reddit_records = []
            for post in posts:
                reddit_record = RedditSentimentRecord.from_post(
                    post=post,
                    ticker="TSLA",
                    user_id=1,  # Default user ID
                )
                reddit_records.append(reddit_record)
            
            # Save to database
            storage.upsert_reddit_posts(reddit_records)
            console.print(f"[green]💾 Saved {len(reddit_records)} posts to Supabase[/green]")
            
        except RedditCollectionError as exc:
            console.print(f"[red]✗ Collection failed: {exc}[/red]")
            return

        # Display results in a simple table (no sentiment analysis)
        console.print(f"\n[bold green]📊 Top Reddit Posts (r/{subreddit})[/bold green]")
        
        from rich.table import Table
        table = Table(title=f"Top TSLA Posts - Sorted by {sort}")
        table.add_column("Title", style="cyan", no_wrap=False, max_width=60)
        table.add_column("Author", style="magenta")
        table.add_column("Upvotes", justify="right", style="green")
        table.add_column("Comments", justify="right", style="blue")
        table.add_column("Posted", style="yellow")
        
        for post in posts[:10]:  # Show top 10
            # Format posted_at datetime
            posted_str = post.posted_at.strftime("%Y-%m-%d %H:%M") if post.posted_at else "Unknown"
            
            table.add_row(
                post.title[:57] + "..." if len(post.title) > 60 else post.title,
                post.author_username or "Unknown",
                str(post.upvote_count or 0),
                str(post.comment_count or 0),
                posted_str
            )
        
        console.print(table)

        console.print(f"\n[bold green]✅ Reddit collection completed![/bold green]")

    asyncio.run(_run())


if __name__ == "__main__":
    app()

