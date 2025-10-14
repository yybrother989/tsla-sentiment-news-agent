from __future__ import annotations

import asyncio
from typing import Optional

import typer

from rich.console import Console
from rich.table import Table

from app.domain.schemas import ArticleRecord, EventRecord, ScoreRecord
from app.infra import get_logger, get_settings, setup_logging
from app.infra.telemetry import timed_span
from app.services import collect_articles, plan_sources, reason_documents, score_document
from app.services.storage import StorageService


app = typer.Typer(add_completion=False)


@app.command()
def run(
    ticker: str = typer.Argument(...),
    window_hours: Optional[int] = typer.Option(None),
    max_docs: Optional[int] = typer.Option(None),
) -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    logger = get_logger(__name__)

    async def _run() -> None:
        with timed_span("planner"):
            plan = await plan_sources(
                {
                    "ticker": ticker,
                    "window_hours": window_hours
                    or settings.planner_payload_defaults()["window_hours"],
                    "max_documents": max_docs or settings.planner_max_documents,
                }
            )

        with timed_span("collector"):
            collection = await collect_articles(plan)

        with timed_span("reasoner"):
            reasoning = await reason_documents(ticker, collection.documents)

        # Prepare storage records
        article_records = []
        event_records = []
        score_records = []

        with timed_span("scorer"):
            for item in reasoning:
                score_response = await score_document(item.document, item.result)
                
                # Build records
                article_records.append(
                    ArticleRecord(
                        ticker=ticker,
                        url=str(item.document.url),
                        title=item.document.title,
                        text=item.document.text,
                        source=item.document.source,
                        published_at=item.document.published_at,
                        canonical_hash=item.result.summary_1liner[:64],
                        user_id=settings.user_id,
                    )
                )
                
                event_records.append(
                    EventRecord(
                        article_url=str(item.document.url),
                        about_ticker=item.result.about_ticker,
                        sentiment=item.result.sentiment,
                        stance=item.result.stance,
                        event_type=item.result.event_type,
                        summary=item.result.summary_1liner,
                        user_id=settings.user_id,
                    )
                )
                
                score_records.append(
                    ScoreRecord(
                        article_url=str(item.document.url),
                        score=score_response.score.score,
                        rationale=score_response.score.rationale,
                        user_id=settings.user_id,
                    )
                )

        # Display results in terminal
        console = Console()
        
        table = Table(title=f"TSLA Sentiment Analysis Results ({len(article_records)} articles)")
        table.add_column("Source", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Sentiment", style="yellow")
        table.add_column("Score", style="green")
        
        for article, event, score in zip(article_records, event_records, score_records):
            sentiment_str = f"{event.sentiment:+.2f} ({event.stance})"
            table.add_row(
                article.source,
                article.title[:50] + "..." if len(article.title) > 50 else article.title,
                sentiment_str,
                str(score.score),
            )
        
        console.print(table)
        
        # Store to Supabase if configured
        if settings.supabase_credentials:
            with timed_span("storage"):
                try:
                    storage = StorageService()
                    storage.upsert_articles(article_records)
                    storage.upsert_events(event_records)
                    storage.upsert_scores(score_records)
                    logger.info("Stored %d records to Supabase", len(article_records))
                except Exception as exc:
                    logger.error("Failed to store to Supabase: %s", exc)
        else:
            logger.warning("Supabase not configured; skipping persistence")

        logger.info("Run completed for %s", ticker)

    asyncio.run(_run())


if __name__ == "__main__":
    app()

