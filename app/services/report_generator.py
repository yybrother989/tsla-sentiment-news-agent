from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader

from app.domain.schemas import SentimentAnalysisRecord
from app.infra import get_logger


class ReportGenerator:
    """Generate news sentiment reports in multiple formats."""

    def __init__(self):
        self.logger = get_logger(__name__)
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent.parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def _calculate_stats(self, records: List[SentimentAnalysisRecord]) -> dict:
        """Calculate report statistics."""
        total = len(records)
        
        # Sentiment-based counts
        positive_count = sum(1 for r in records if r.sentiment_score and r.sentiment_score > 0.1)
        negative_count = sum(1 for r in records if r.sentiment_score and r.sentiment_score < -0.1)
        neutral_count = sum(1 for r in records if r.sentiment_score and -0.1 <= r.sentiment_score <= 0.1)
        
        # Stance-based counts
        bullish_count = sum(1 for r in records if r.stance == 'bullish')
        bearish_count = sum(1 for r in records if r.stance == 'bearish')
        stance_neutral_count = sum(1 for r in records if r.stance == 'neutral')
        
        # Average scores
        sentiment_scores = [r.sentiment_score for r in records if r.sentiment_score is not None]
        impact_scores = [r.impact_score for r in records if r.impact_score is not None]
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0.0
        
        # Category distribution
        category_counts = Counter(r.category for r in records if r.category)
        
        return {
            'total_articles': total,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'positive_pct': int(positive_count / total * 100) if total > 0 else 0,
            'negative_pct': int(negative_count / total * 100) if total > 0 else 0,
            'neutral_pct': int(neutral_count / total * 100) if total > 0 else 0,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'stance_neutral_count': stance_neutral_count,
            'avg_sentiment': f"{avg_sentiment:+.2f}",
            'avg_impact': f"{avg_impact:.1f}",
            'category_distribution': dict(category_counts.most_common()),
        }

    def generate_html_report(
        self,
        records: List[SentimentAnalysisRecord],
        output_path: str | Path,
        time_period: str = "Last 7 days"
    ) -> str:
        """Generate HTML report with interactive features."""
        self.logger.info("Generating HTML report for %d articles", len(records))
        
        stats = self._calculate_stats(records)
        
        # Sort articles by impact and sentiment
        sorted_records = sorted(
            records,
            key=lambda r: (r.impact_score or 0, r.sentiment_score or 0),
            reverse=True
        )
        
        template = self.env.get_template('news_report.html')
        html_content = template.render(
            report_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            time_period=time_period,
            articles=sorted_records,
            **stats
        )
        
        output_file = Path(output_path)
        output_file.write_text(html_content, encoding='utf-8')
        
        self.logger.info("HTML report saved to %s", output_file)
        return str(output_file)

    def generate_markdown_report(
        self,
        records: List[SentimentAnalysisRecord],
        output_path: str | Path,
        time_period: str = "Last 7 days"
    ) -> str:
        """Generate Markdown report for easy sharing."""
        self.logger.info("Generating Markdown report for %d articles", len(records))
        
        stats = self._calculate_stats(records)
        
        # Separate by stance
        bullish_articles = [r for r in records if r.stance == 'bullish']
        bearish_articles = [r for r in records if r.stance == 'bearish']
        neutral_articles = [r for r in records if r.stance == 'neutral']
        high_impact_articles = [r for r in records if r.impact_score and r.impact_score >= 4]
        
        # Sort each group by impact and sentiment
        for article_list in [bullish_articles, bearish_articles, neutral_articles, high_impact_articles]:
            article_list.sort(key=lambda r: (r.impact_score or 0, abs(r.sentiment_score or 0)), reverse=True)
        
        template = self.env.get_template('news_report.md')
        md_content = template.render(
            report_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            time_period=time_period,
            bullish_articles=bullish_articles,
            bearish_articles=bearish_articles,
            neutral_articles=neutral_articles,
            high_impact_articles=high_impact_articles,
            **stats
        )
        
        output_file = Path(output_path)
        output_file.write_text(md_content, encoding='utf-8')
        
        self.logger.info("Markdown report saved to %s", output_file)
        return str(output_file)

    def generate_json_export(
        self,
        records: List[SentimentAnalysisRecord],
        output_path: str | Path
    ) -> str:
        """Generate JSON export for programmatic access."""
        self.logger.info("Generating JSON export for %d articles", len(records))
        
        stats = self._calculate_stats(records)
        
        # Convert records to dict
        articles_data = [
            {
                'id': r.id,
                'title': r.title,
                'url': r.url,
                'source': r.source,
                'published_at': r.published_at.isoformat() if r.published_at else None,
                'category': r.category,
                'sentiment_score': r.sentiment_score,
                'impact_score': r.impact_score,
                'sentiment_confidence': r.sentiment_confidence,
                'stance': r.stance,
                'summary': r.summary,
                'sentiment_rationale': r.sentiment_rationale,
                'key_factors': r.key_factors,
                'classification_confidence': r.classification_confidence,
            }
            for r in records
        ]
        
        export_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_articles': len(records),
            },
            'statistics': stats,
            'articles': articles_data,
        }
        
        output_file = Path(output_path)
        output_file.write_text(json.dumps(export_data, indent=2), encoding='utf-8')
        
        self.logger.info("JSON export saved to %s", output_file)
        return str(output_file)


__all__ = ['ReportGenerator']
