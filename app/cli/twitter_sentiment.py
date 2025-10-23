from __future__ import annotations

import asyncio
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Sequence

import typer
from rich.console import Console
from rich.table import Table

from app.adapters.twitter_source import (
    TwitterCollectionError as BrowserCollectionError,
    TwitterSearchConfig,
)
from app.adapters.twitter_source import fetch_tweets as fetch_tweets_browser
from app.adapters.n8n_twitter_source import (
    N8nCollectionError,
    fetch_tweets as fetch_tweets_n8n,
)
from app.domain.schemas import TwitterSentimentRecord, TwitterTweet
from app.infra import get_logger, get_settings, setup_logging
from app.infra.telemetry import timed_span
from app.services.scorer import SentimentAnalyzer
from app.services.storage import StorageService


app = typer.Typer(add_completion=False)


async def _analyze_tweets(
    tweets: Sequence[TwitterTweet],
    analyzer: SentimentAnalyzer | None,
) -> Sequence[TwitterSentimentRecord]:
    settings = get_settings()
    records: list[TwitterSentimentRecord] = []

    for tweet in tweets:
        sentiment_score = None
        label = None
        confidence = None
        rationale = None
        key_themes: List[str] | None = None

        if analyzer:
            analysis = await analyzer.analyze_article(
                document=tweet.to_collector_document(),
                category="Market & Sentiment",
            )
            sentiment_score = analysis.sentiment
            confidence = analysis.confidence
            label = analysis.stance
            rationale = analysis.rationale
            key_themes = analysis.key_factors

        record = TwitterSentimentRecord.from_tweet(
            tweet=tweet,
            ticker="TSLA",
            sentiment_score=sentiment_score,
            sentiment_label=label,
            sentiment_confidence=confidence,
            sentiment_rationale=rationale,
            key_themes=key_themes,
            user_id=settings.user_id,
        )
        records.append(record)

    return records


def _compute_sentiment_index(records: Sequence[TwitterSentimentRecord]) -> float:
    positives = sum(1 for r in records if r.sentiment_label == "bullish")
    negatives = sum(1 for r in records if r.sentiment_label == "bearish")
    total = sum(1 for r in records if r.sentiment_label in {"bullish", "bearish", "neutral"})

    if total == 0:
        return 0.0

    return (positives - negatives) / total


def _label_from_score(score: float | None, default: str = "neutral") -> str:
    if score is None:
        return default
    if score > 0.3:
        return "bullish"
    if score < -0.3:
        return "bearish"
    return "neutral"


def _build_console_table(records: Sequence[TwitterSentimentRecord]) -> Table:
    table = Table(title=f"Twitter Sentiment Analysis ({len(records)} tweets)")
    table.add_column("Author", style="cyan")
    table.add_column("Engagement", style="magenta")
    table.add_column("Sentiment", style="green")
    table.add_column("Text", style="white")

    for record in records[:20]:
        engagement = (
            f"❤ {record.like_count or 0} | 💬 {record.reply_count or 0} | "
            f"🔄 {record.retweet_count or 0}"
        )
        sentiment = record.sentiment_score
        sentiment_display = f"{sentiment:+.2f}" if sentiment is not None else "N/A"

        author_display = (
            f"@{record.author_handle}" if record.author_handle 
            else f"@{record.author_username}" if record.author_username
            else record.author_name or "Unknown"
        )
        
        table.add_row(
            author_display,
            engagement,
            sentiment_display,
            record.text[:120] + ("…" if len(record.text) > 120 else ""),
        )

    return table


def _save_markdown_report(
    records: Sequence[TwitterSentimentRecord],
    sentiment_index: float,
    output_dir: Path,
    config: TwitterSearchConfig,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"twitter_sentiment_{timestamp}.md"

    positives = sum(1 for r in records if r.sentiment_label == "bullish")
    negatives = sum(1 for r in records if r.sentiment_label == "bearish")
    neutrals = sum(1 for r in records if r.sentiment_label == "neutral")

    template = f"""
# Tesla Twitter Sentiment Report

- Generated: {datetime.now().isoformat()}
- Query Window: {config.since} → {config.until}
- Total Tweets: {len(records)}
- Positive: {positives}
- Neutral: {neutrals}
- Negative: {negatives}
- Sentiment Index: {sentiment_index:+.2f}

## Representative Tweets

### Bullish

"""

    bullish_examples = [r for r in records if r.sentiment_label == "bullish"][:3]
    bearish_examples = [r for r in records if r.sentiment_label == "bearish"][:3]
    neutral_examples = [r for r in records if r.sentiment_label == "neutral"][:3]

    def format_section(items: Sequence[TwitterSentimentRecord]) -> str:
        lines = []
        for record in items:
            author_display = (
                f"@{record.author_handle}" if record.author_handle 
                else f"@{record.author_username}" if record.author_username
                else record.author_name or 'unknown'
            )
            lines.append(
                f"- {author_display} ({record.posted_at.isoformat()}):\n"
                f"  {record.text}\n"
                f"  Likes {record.like_count or 0} | Replies {record.reply_count or 0} | Retweets {record.retweet_count or 0} | URL: {record.tweet_url}"
            )
        if not lines:
            lines.append("- _None available_")
        return "\n".join(lines)

    template += format_section(bullish_examples)
    template += "\n\n### Neutral\n\n"
    template += format_section(neutral_examples)
    template += "\n\n### Bearish\n\n"
    template += format_section(bearish_examples)

    filename.write_text(template.strip() + "\n", encoding="utf-8")
    return filename


@app.command()
def twitter_login_simple() -> None:
    """Simple cookie-based login - paste cookies from your browser (RECOMMENDED)."""
    
    from pathlib import Path
    import json
    from datetime import datetime, timedelta
    
    console = Console()
    
    console.print("\n[bold cyan]🍪 Simple Twitter Cookie Setup (Recommended)[/bold cyan]\n")
    console.print("[yellow]Instructions:[/yellow]")
    console.print("  1. Open Twitter in your regular browser and log in")
    console.print("  2. Install a cookie export extension:")
    console.print("     • Chrome: [link]https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid[/link]")
    console.print("     • Firefox: [link]https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/[/link]")
    console.print("  3. Export cookies for twitter.com")
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
            # Already in cookie array format
            cookies = cookie_data
        elif isinstance(cookie_data, dict) and 'cookies' in cookie_data:
            # Already in storage_state format
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
        session_cache = cache_dir / "twitter_session.json"
        
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
        console.print("  • Verify: [cyan]python -m app.cli.twitter_sentiment twitter-sentiment --check-cache[/cyan]")
        console.print("  • Collect: [cyan]python -m app.cli.twitter_sentiment twitter-sentiment --since 2025-09-01 --until 2025-10-15[/cyan]\n")
        
    except json.JSONDecodeError as e:
        console.print(f"[red]✗ Invalid JSON format: {e}[/red]")
        console.print("[yellow]💡 Make sure to export cookies in JSON format from the browser extension[/yellow]")


@app.command()
def twitter_login(
    timeout: int = typer.Option(300, help="Timeout in seconds to wait for manual login (default: 5 minutes)"),
    use_home: bool = typer.Option(False, help="Start from twitter.com instead of /login page (may load faster)")
) -> None:
    """Interactive browser login - automated but may have issues (USE twitter-login-simple INSTEAD)."""
    
    from playwright.async_api import async_playwright
    import asyncio
    from pathlib import Path
    import json
    from datetime import datetime
    
    console = Console()
    
    async def _login() -> None:
        cache_dir = Path("cache")
        cache_dir.mkdir(exist_ok=True)
        session_cache = cache_dir / "twitter_session.json"
        
        console.print("\n[bold cyan]🔐 Twitter First-Time Login Setup[/bold cyan]\n")
        console.print("[yellow]Instructions:[/yellow]")
        console.print("  1. A Chrome browser will open")
        console.print("  2. Log in to Twitter manually")
        console.print("  3. Complete any 2FA/verification challenges")
        console.print("  4. Once logged in, return here and press [bold green]Ctrl+C[/bold green]")
        console.print(f"  5. Your session will be saved for {timeout // 60} minutes\n")
        
        input("Press [Enter] to open the browser...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                ],
                slow_mo=50,  # Slow down actions slightly to appear more human
            )
            
            # Create context with realistic browser fingerprint
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
            )
            
            # Add extra headers to appear more legitimate
            await context.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            page = await context.new_page()
            
            # Choose URL based on user preference
            url = "https://twitter.com" if use_home else "https://twitter.com/login"
            
            console.print(f"\n[cyan]→ Opening {url}...[/cyan]")
            console.print("[dim]This may take 10-15 seconds due to Twitter's security checks...[/dim]")
            
            # Go to Twitter with longer timeout and wait for network idle
            try:
                await page.goto(url, wait_until='networkidle', timeout=60000)
            except Exception as e:
                console.print(f"[yellow]⚠ Page load timed out, but you can still try to log in: {e}[/yellow]")
                # Continue anyway - page might be partially loaded
            
            console.print("[green]✓ Browser opened. Please log in manually.[/green]")
            console.print(f"\n[yellow]Waiting for you to complete login (up to {timeout} seconds)...[/yellow]")
            console.print("[bold cyan]When logged in, press Ctrl+C in this terminal to save your session.[/bold cyan]\n")
            console.print("[dim]💡 Tip: Don't close the browser window manually - just press Ctrl+C here.[/dim]\n")
            
            session_saved = False
            try:
                # Keep checking in small intervals so Ctrl+C works
                for _ in range(timeout):
                    await asyncio.sleep(1)
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass  # User pressed Ctrl+C, continue to save
            
            console.print("\n[green]→ Saving session...[/green]")
            
            try:
                # Save the session state using storage_state_path method instead
                # This is more reliable than storage_state() which sometimes fails
                temp_state_file = session_cache.with_suffix('.tmp.json')
                
                # Try multiple methods to get the session
                storage_state = None
                try:
                    # Method 1: Direct storage_state call with shorter timeout
                    storage_state = await asyncio.wait_for(
                        context.storage_state(), 
                        timeout=5.0
                    )
                except (asyncio.TimeoutError, Exception) as e1:
                    console.print(f"[dim]Method 1 failed, trying alternative...[/dim]")
                    try:
                        # Method 2: Get cookies and local storage separately
                        cookies = await context.cookies()
                        storage_state = {
                            'cookies': cookies,
                            'origins': []
                        }
                    except Exception as e2:
                        raise Exception(f"Could not retrieve session: {e1}, {e2}")
                
                if not storage_state:
                    raise Exception("Session state is empty")
                
                cache_data = {
                    'timestamp': datetime.now().isoformat(),
                    'storage_state': storage_state
                }
                
                # Write to temp file first, then rename (atomic operation)
                with open(temp_state_file, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                
                temp_state_file.rename(session_cache)
                
                console.print(f"[green]✓ Session saved to {session_cache}[/green]")
                console.print(f"[dim]Saved {len(storage_state.get('cookies', []))} cookies[/dim]")
                console.print("\n[bold]Next steps:[/bold]")
                console.print("  • Verify: [cyan]python -m app.cli.twitter_sentiment twitter-sentiment --check-cache[/cyan]")
                console.print("  • Collect: [cyan]python -m app.cli.twitter_sentiment twitter-sentiment --since 2025-09-01 --until 2025-10-15[/cyan]\n")
                session_saved = True
            except Exception as e:
                console.print(f"[red]✗ Failed to save session: {e}[/red]")
                console.print("[yellow]💡 The browser might have security restrictions. Try again or check browser console for errors.[/yellow]")
            
            # Try to close browser gracefully
            try:
                await browser.close()
            except:
                pass  # Ignore if already closed
            
            if not session_saved:
                console.print("\n[red]❌ Session was not saved. Please try again and:[/red]")
                console.print("[yellow]  1. Log in to Twitter in the browser[/yellow]")
                console.print("[yellow]  2. Press Ctrl+C in the terminal (DON'T close the browser window)[/yellow]\n")
    
    asyncio.run(_login())


@app.command()
def twitter_sentiment(
    since: str = typer.Option("2025-09-01", help="Start date (YYYY-MM-DD)"),
    until: str = typer.Option("2025-10-15", help="End date (YYYY-MM-DD)"),
    min_replies: int = typer.Option(100, help="Minimum replies filter"),
    min_likes: int = typer.Option(2000, help="Minimum likes filter"),
    min_retweets: int = typer.Option(100, help="Minimum retweets filter"),
    target: int = typer.Option(75, help="Target tweet count"),
    scrolls: int = typer.Option(8, help="Maximum scroll attempts"),
    save_markdown: bool = typer.Option(True, help="Persist Markdown report to reports/"),
    clear_cache: bool = typer.Option(False, help="Clear cached Twitter session and re-authenticate"),
    check_cache: bool = typer.Option(False, help="Check cache status and exit"),
    use_browser: bool = typer.Option(False, help="Use browser-use instead of n8n+Apify (legacy mode)")
) -> None:
    """Collect high-engagement Tesla tweets and analyze sentiment (default: n8n+Apify, or --use-browser for legacy mode)."""

    settings = get_settings()
    setup_logging(settings.log_level)
    logger = get_logger(__name__)
    console = Console()

    async def _run() -> None:
        # Check cache status if requested
        if check_cache:
            cache_file = Path("cache/twitter_session.json")
            if cache_file.exists():
                try:
                    import json
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
                    expires_at = cache_time + timedelta(hours=24)
                    time_left = expires_at - datetime.now()
                    
                    if time_left.total_seconds() > 0:
                        console.print(f"[green]✓ Twitter session cache is valid[/green]")
                        console.print(f"[cyan]  Expires in: {time_left}[/cyan]")
                        console.print(f"[cyan]  Created: {cache_time.strftime('%Y-%m-%d %H:%M:%S')}[/cyan]")
                    else:
                        console.print(f"[yellow]⚠ Twitter session cache is expired[/yellow]")
                        console.print(f"[cyan]  Expired: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}[/cyan]")
                except Exception as exc:
                    console.print(f"[red]✗ Cache file is corrupted: {exc}[/red]")
            else:
                console.print("[yellow]⚠ No Twitter session cache found[/yellow]")
            return

        # Clear cache if requested
        if clear_cache:
            cache_file = Path("cache/twitter_session.json")
            if cache_file.exists():
                cache_file.unlink()
                console.print("[yellow]✓ Cleared Twitter session cache[/yellow]\n")
        
        config = TwitterSearchConfig(
            query="tsla OR Tesla",
            since=since,
            until=until,
            min_replies=min_replies,
            min_faves=min_likes,
            min_retweets=min_retweets,
            target_count=target,
            max_scrolls=scrolls,
        )

        # Choose collection method based on flag
        if use_browser:
            # Legacy browser-use method
            cache_file = Path("cache/twitter_session.json")
            has_cache = cache_file.exists()
            
            if not has_cache:
                console.print("\n[red]✗ No Twitter session found![/red]\n")
                console.print("[yellow]First-time setup required (choose one method):[/yellow]\n")
                console.print("[bold green]Method 1 - Simple Cookie Paste (RECOMMENDED):[/bold green]")
                console.print("  • Run: [cyan]python -m app.cli.twitter_sentiment twitter-login-simple[/cyan]")
                console.print("  • Export cookies from your browser")
                console.print("  • Paste and done!\n")
                console.print("[dim]Method 2 - Automated Browser (may have issues):[/dim]")
                console.print("  • Run: [dim cyan]python -m app.cli.twitter_sentiment twitter-login[/dim]")
                console.print("  • Log in manually, press Ctrl+C\n")
                return
            
            console.print("\n[bold cyan]🔍 Collecting Tesla tweets via Browser-Use (legacy mode)...[/bold cyan]\n")
            
            try:
                with timed_span("twitter-collection"):
                    tweets = await fetch_tweets_browser(config)
            except BrowserCollectionError as exc:
                console.print(f"[red]✗ Browser collection failed: {exc}[/red]")
                return
        else:
            # Default n8n + Apify method
            console.print("\n[bold cyan]🔍 Collecting Tesla tweets via n8n + Apify...[/bold cyan]\n")
            
            # Check n8n configuration
            if not settings.n8n_base_url:
                console.print("[red]✗ N8N_BASE_URL not configured[/red]\n")
                console.print("[yellow]To use n8n integration:[/yellow]")
                console.print("  1. Add N8N_BASE_URL to .env (e.g., https://bravecareer.app.n8n.cloud)")
                console.print("  2. Set up n8n workflow with HTTP Request node")
                console.print("  3. See docs/N8N_HTTP_REQUEST_SETUP.md for detailed guide\n")
                console.print("[cyan]Or use legacy browser-use with --use-browser flag[/cyan]\n")
                return
            
            try:
                with timed_span("twitter-collection"):
                    tweets = await fetch_tweets_n8n(config)
            except N8nCollectionError as exc:
                console.print(f"[red]✗ n8n collection failed: {exc}[/red]")
                console.print("[yellow]💡 Try legacy browser-use with --use-browser flag[/yellow]\n")
                return

        if not tweets:
            console.print("[yellow]No tweets fetched. Adjust the filters or login state.[/yellow]")
            return

        console.print(f"[green]✓ Retrieved {len(tweets)} tweets[/green]\n")

        analyzer = None
        if settings.openai_api_key:
            analyzer = SentimentAnalyzer(
                model=settings.planner_llm_model,
                api_key=settings.openai_api_key,
            )
        else:
            logger.warning("OpenAI API key missing; sentiment analysis will be skipped")

        console.print("[cyan]→ Scoring sentiment...[/cyan]")

        with timed_span("twitter-sentiment"):
            enriched = await _analyze_tweets(tweets, analyzer)

        console.print(f"[green]✓ Scored {len(enriched)} tweets[/green]\n")

        # Backfill labels if sentiment analyzer missing
        for record in enriched:
            if record.sentiment_label is None:
                record.sentiment_label = _label_from_score(record.sentiment_score)

        sentiment_index = _compute_sentiment_index(enriched)

        table = _build_console_table(enriched)
        console.print(table)

        console.print("\n[bold]Sentiment Breakdown:[/bold]")
        counts = Counter(record.sentiment_label or "unknown" for record in enriched)
        for label, count in counts.items():
            console.print(f"  • {label.capitalize()}: {count}")

        console.print(f"\n[bold]Sentiment Index:[/bold] {sentiment_index:+.2f}")

        if sentiment_index > 0.3:
            console.print("[green]→ Bullish tone detected[/green]")
        elif sentiment_index < -0.3:
            console.print("[red]→ Bearish tone detected[/red]")
        else:
            console.print("[yellow]→ Neutral or mixed tone[/yellow]")

        if settings.supabase_credentials:
            console.print("\n[cyan]→ Persisting to Supabase...[/cyan]")
            with timed_span("twitter-storage"):
                storage = StorageService()
                storage.upsert_tweets(enriched)
            console.print("[green]✓ Stored tweets in Supabase[/green]")
        else:
            console.print("\n[yellow]⚠ Supabase not configured; skipping persistence[/yellow]")

        if save_markdown:
            report_path = _save_markdown_report(
                records=enriched,
                sentiment_index=sentiment_index,
                output_dir=Path("reports"),
                config=config,
            )
            console.print(f"\n[green]✓ Markdown summary saved to {report_path}[/green]")

    asyncio.run(_run())


if __name__ == "__main__":
    app()

