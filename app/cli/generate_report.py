from __future__ import annotations

import asyncio
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from app.domain.schemas import SentimentAnalysisRecord
from app.infra import get_logger, get_settings, setup_logging
from app.services.report_generator import ReportGenerator
from app.services.storage import StorageService

app = typer.Typer(add_completion=False)


@app.command()
def report(
    days: int = typer.Option(7, help="Number of days to include in report"),
    format: str = typer.Option("html", help="Report format: html, markdown, json, or all"),
    output_dir: str = typer.Option("reports", help="Output directory for reports"),
    open_browser: bool = typer.Option(True, help="Open HTML report in browser"),
) -> None:
    """Generate a news sentiment report from stored data."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger = get_logger(__name__)
    
    async def _generate() -> None:
        console = Console()
        
        console.print(
            f"\n[bold cyan]📊 Generating Tesla News Sentiment Report...[/bold cyan]\n"
        )
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Fetch data from database
        if not settings.supabase_credentials:
            console.print("[red]✗ Supabase not configured. Cannot generate report.[/red]")
            return
        
        try:
            storage = StorageService()
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            console.print(f"[cyan]→ Fetching articles from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...[/cyan]")
            
            # Query articles from database
            from app.adapters.supabase_client import SupabaseAdapter
            adapter = SupabaseAdapter.default_adapter()
            
            response = adapter.client.table('sentiment_analysis').select('*').gte(
                'published_at', start_date.isoformat()
            ).lte(
                'published_at', end_date.isoformat()
            ).eq(
                'user_id', settings.user_id
            ).order('published_at', desc=True).execute()
            
            if not response.data:
                console.print("[yellow]⚠ No articles found in the specified date range.[/yellow]")
                return
            
            # Convert to SentimentAnalysisRecord objects
            records = [SentimentAnalysisRecord(**row) for row in response.data]
            console.print(f"[green]✓ Retrieved {len(records)} articles[/green]\n")
            
            # Generate reports
            generator = ReportGenerator()
            time_period = f"Last {days} days ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            generated_files = []
            
            if format in ['html', 'all']:
                html_file = output_path / f"tesla_news_report_{timestamp}.html"
                generator.generate_html_report(records, html_file, time_period)
                generated_files.append(('HTML', html_file))
                
                if open_browser:
                    console.print(f"[cyan]→ Opening report in browser...[/cyan]")
                    webbrowser.open(f"file://{html_file.absolute()}")
            
            if format in ['markdown', 'all']:
                md_file = output_path / f"tesla_news_report_{timestamp}.md"
                generator.generate_markdown_report(records, md_file, time_period)
                generated_files.append(('Markdown', md_file))
            
            if format in ['json', 'all']:
                json_file = output_path / f"tesla_news_report_{timestamp}.json"
                generator.generate_json_export(records, json_file)
                generated_files.append(('JSON', json_file))
            
            # Display summary
            console.print()
            console.print(Panel.fit(
                f"[green]✅ Report generated successfully![/green]\n\n"
                f"[bold]Articles:[/bold] {len(records)}\n"
                f"[bold]Time Period:[/bold] {time_period}\n\n"
                f"[bold]Generated Files:[/bold]\n" +
                "\n".join([f"  • {fmt}: [cyan]{path}[/cyan]" for fmt, path in generated_files]),
                title="📊 Report Summary",
                border_style="green"
            ))
            
        except Exception as exc:
            logger.error("Failed to generate report: %s", exc, exc_info=True)
            console.print(f"[red]✗ Error: {exc}[/red]")
    
    asyncio.run(_generate())


if __name__ == "__main__":
    app()
