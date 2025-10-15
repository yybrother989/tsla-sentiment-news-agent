from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app.adapters.news_sources import fetch_tesla_news
from app.domain.schemas import SentimentAnalysisRecord
from app.infra import get_logger, get_settings, setup_logging
from app.infra.telemetry import timed_span
from app.services.classifier import NewsClassifier
from app.services.scorer import analyze_sentiment
from app.services.storage import StorageService

app = typer.Typer(add_completion=False)


@app.command()
def fetch(
    days: int = typer.Option(7, help="Number of days to look back (time window)"),
    limit: Optional[int] = typer.Option(None, help="Maximum number of articles to retrieve (optional, default: all)"),
    skip_sentiment: bool = typer.Option(False, help="Skip sentiment analysis to save time"),
) -> None:
    """Fetch Tesla news, classify into categories, and perform sentiment analysis."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger = get_logger(__name__)
    ticker = "TSLA"  # Fixed for Tesla-focused agent

    async def _fetch() -> None:
        console = Console()
        
        limit_text = f"max {limit} articles" if limit else "all available articles"
        console.print(
            f"\n[bold cyan]📰 Fetching Tesla news via DuckDuckGo ({days}-day window, {limit_text})...[/bold cyan]\n"
        )

        # Step 1: Fetch all Tesla news via DuckDuckGo (bot-friendly)
        with timed_span("news-collection"):
            try:
                console.print(f"[cyan]→ Searching DuckDuckGo for Tesla news...[/cyan]")
                documents = await fetch_tesla_news(days)
                
                # Apply limit if specified
                if limit and len(documents) > limit:
                    documents = documents[:limit]
                    console.print(f"[green]  ✓ Retrieved {len(documents)} articles (limited from total available)[/green]\n")
                else:
                    console.print(f"[green]  ✓ Retrieved {len(documents)} articles[/green]\n")
            except Exception as exc:
                logger.error("Failed to fetch via DuckDuckGo: %s", exc)
                console.print(f"[red]  ✗ Failed: {exc}[/red]")
                return

            if not documents:
                console.print("[yellow]No articles found.[/yellow]")
                return
        
        # Step 2: Classify each article into categories
        console.print(f"[cyan]→ Classifying articles into categories...[/cyan]")
        
        with timed_span("classification"):
            classifier = NewsClassifier()
            classified_records = []
            
            for doc in documents:
                try:
                    # Classify using keyword + LLM
                    category, confidence, rationale = await classifier.classify(doc.title, doc.text or "")
                    
                    # Create sentiment analysis record with classification
                    record = SentimentAnalysisRecord(
                        ticker=ticker,
                        url=str(doc.url),
                        title=doc.title,
                        text=doc.text,
                        source=doc.source,
                        published_at=doc.published_at,
                        canonical_hash=doc.url.host or "unknown",
                        user_id=settings.user_id,
                        category=category.value,
                        classification_confidence=confidence,
                        classification_rationale=rationale,
                    )
                    classified_records.append(record)
                    
                except Exception as exc:
                    logger.warning("Failed to classify article '%s': %s", doc.title, exc)
                    # Add without classification
                    classified_records.append(
                        SentimentAnalysisRecord(
                            ticker=ticker,
                            url=str(doc.url),
                            title=doc.title,
                            text=doc.text,
                            source=doc.source,
                            published_at=doc.published_at,
                            canonical_hash=doc.url.host or "unknown",
                            user_id=settings.user_id,
                        )
                    )
            
            console.print(f"[green]  ✓ Classified {len(classified_records)} articles[/green]\n")
        
        # Step 3: Perform sentiment analysis on classified articles (optional)
        if skip_sentiment:
            console.print(f"[yellow]⏭️  Skipping sentiment analysis (--skip-sentiment flag set)[/yellow]\n")
            records = classified_records
        else:
            console.print(f"[cyan]→ Analyzing sentiment and market impact...[/cyan]")
            
            with timed_span("sentiment-analysis"):
                sentiment_records = []
                
                for record in classified_records:
                    try:
                        # Perform sentiment analysis
                        sentiment_result = await analyze_sentiment(
                            document=record,  # SentimentAnalysisRecord can be used as CollectorDocument
                            category=record.category
                        )
                        
                        # Update record with sentiment analysis results
                        record.sentiment_score = sentiment_result.sentiment
                        record.impact_score = sentiment_result.impact
                        record.sentiment_confidence = sentiment_result.confidence
                        record.sentiment_rationale = sentiment_result.rationale
                        record.key_factors = ", ".join(sentiment_result.key_factors)
                        record.summary = sentiment_result.summary
                        record.stance = sentiment_result.stance
                        
                        sentiment_records.append(record)
                        
                    except Exception as exc:
                        logger.warning("Failed to analyze sentiment for article '%s': %s", record.title, exc)
                        # Add without sentiment analysis
                        sentiment_records.append(record)
                
                console.print(f"[green]  ✓ Analyzed sentiment for {len(sentiment_records)} articles[/green]\n")
                records = sentiment_records

            # Display results - format depends on whether sentiment analysis was performed
            if skip_sentiment:
                table = Table(title=f"Retrieved & Classified {len(records)} Articles")
                table.add_column("Category", style="magenta")
                table.add_column("Title", style="white")
                table.add_column("Source", style="cyan")
                table.add_column("Confidence", style="yellow")
                table.add_column("Date", style="blue")

                for record in records:
                    confidence_display = f"{record.classification_confidence:.0%}" if record.classification_confidence else "N/A"
                    category_display = record.category or "Uncategorized"
                    
                    table.add_row(
                        category_display,
                        record.title[:50] + "..." if len(record.title) > 50 else record.title,
                        record.source[:20],
                        confidence_display,
                        record.published_at.strftime("%Y-%m-%d"),
                    )
            else:
                table = Table(title=f"Retrieved, Classified & Analyzed {len(records)} Articles")
                table.add_column("Category", style="magenta")
                table.add_column("Title", style="white")
                table.add_column("Sentiment", style="green")
                table.add_column("Impact", style="blue")
                table.add_column("Confidence", style="yellow")
                table.add_column("Date", style="cyan")

                for record in records:
                    # Format sentiment score with color coding
                    sentiment = record.sentiment_score
                    if sentiment is not None:
                        if sentiment > 0.3:
                            sentiment_display = f"[green]{sentiment:+.2f}[/green]"
                        elif sentiment < -0.3:
                            sentiment_display = f"[red]{sentiment:+.2f}[/red]"
                        else:
                            sentiment_display = f"[yellow]{sentiment:+.2f}[/yellow]"
                    else:
                        sentiment_display = "N/A"
                    
                    # Format impact score
                    impact_display = f"{record.impact_score}/5" if record.impact_score else "N/A"
                    
                    # Format classification confidence
                    confidence_display = f"{record.classification_confidence:.0%}" if record.classification_confidence else "N/A"
                    category_display = record.category or "Uncategorized"
                    
                    table.add_row(
                        category_display,
                        record.title[:40] + "..." if len(record.title) > 40 else record.title,
                        sentiment_display,
                        impact_display,
                        confidence_display,
                        record.published_at.strftime("%Y-%m-%d"),
                    )

            console.print(table)
            
            # Display category distribution
            from collections import Counter
            category_counts = Counter(r.category for r in records if r.category)
            
            console.print(f"\n[bold]Category Distribution:[/bold]")
            for cat, count in category_counts.most_common():
                console.print(f"  • {cat}: {count} articles")
            
            # Display sentiment summary (only if sentiment analysis was performed)
            if not skip_sentiment:
                sentiment_scores = [r.sentiment_score for r in records if r.sentiment_score is not None]
                impact_scores = [r.impact_score for r in records if r.impact_score is not None]
                
                if sentiment_scores:
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                    avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0
                    
                    # Color code the average sentiment
                    if avg_sentiment > 0.3:
                        sentiment_color = "green"
                        sentiment_label = "Positive"
                    elif avg_sentiment < -0.3:
                        sentiment_color = "red"
                        sentiment_label = "Negative"
                    else:
                        sentiment_color = "yellow"
                        sentiment_label = "Neutral"
                    
                    console.print(f"\n[bold]Sentiment Summary:[/bold]")
                    console.print(f"  • Overall Sentiment: [{sentiment_color}]{avg_sentiment:+.2f} ({sentiment_label})[/{sentiment_color}]")
                    console.print(f"  • Average Impact: {avg_impact:.1f}/5")
                    console.print(f"  • Positive Articles: {sum(1 for s in sentiment_scores if s > 0.1)} ({sum(1 for s in sentiment_scores if s > 0.1)/len(sentiment_scores)*100:.0f}%)")
                    console.print(f"  • Negative Articles: {sum(1 for s in sentiment_scores if s < -0.1)} ({sum(1 for s in sentiment_scores if s < -0.1)/len(sentiment_scores)*100:.0f}%)")
                    console.print(f"  • Neutral Articles: {sum(1 for s in sentiment_scores if -0.1 <= s <= 0.1)} ({sum(1 for s in sentiment_scores if -0.1 <= s <= 0.1)/len(sentiment_scores)*100:.0f}%)")
            
            console.print()

            # Store to database
            if settings.supabase_credentials:
                with timed_span("storage"):
                    try:
                        storage = StorageService()
                        storage.upsert_records(records)
                        console.print(
                            f"\n[green]✓ Stored {len(records)} articles to Supabase[/green]\n"
                        )
                    except Exception as exc:
                        logger.error("Failed to store to Supabase: %s", exc)
                        console.print(f"\n[red]✗ Storage failed: {exc}[/red]\n")
            else:
                console.print(
                    "\n[yellow]⚠ Supabase not configured; skipping persistence[/yellow]\n"
                )

    asyncio.run(_fetch())


if __name__ == "__main__":
    app()

