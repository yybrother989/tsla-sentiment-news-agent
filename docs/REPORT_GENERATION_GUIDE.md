# 📊 News Report Generation Guide

## Overview

The Tesla Sentiment News Agent generates beautiful, interactive reports from your collected news data. Reports are available in **3 formats**:

1. **HTML** - Interactive web report with filtering
2. **Markdown** - Clean text format for sharing
3. **JSON** - Structured data for integrations

## 🚀 Quick Start

### Generate HTML Report (Default)
```bash
python -m app.cli.generate_report
```

This will:
- ✅ Generate an HTML report for the last 7 days
- ✅ Automatically open it in your browser
- ✅ Save to `reports/` directory

### Generate All Formats
```bash
python -m app.cli.generate_report --format all
```

### Custom Time Period
```bash
# Last 30 days
python -m app.cli.generate_report --days 30

# Last 24 hours
python -m app.cli.generate_report --days 1
```

## 📋 CLI Options

### `--days` (default: 7)
Number of days to include in the report

```bash
python -m app.cli.generate_report --days 30
```

### `--format` (default: html)
Report format: `html`, `markdown`, `json`, or `all`

```bash
# HTML only (default)
python -m app.cli.generate_report --format html

# Markdown only
python -m app.cli.generate_report --format markdown

# JSON only
python -m app.cli.generate_report --format json

# All formats
python -m app.cli.generate_report --format all
```

### `--output-dir` (default: reports)
Output directory for generated reports

```bash
python -m app.cli.generate_report --output-dir ./my_reports
```

### `--no-open-browser`
Don't automatically open HTML report in browser

```bash
python -m app.cli.generate_report --no-open-browser
```

## 📊 Report Formats

### 1. HTML Report

**Features:**
- 📱 Responsive design
- 🔍 Interactive filtering (bullish/bearish/neutral/high-impact)
- 📊 Visual dashboard with statistics
- 🎨 Color-coded sentiment indicators
- 🔗 Clickable article links
- ⭐ Star ratings for impact
- 📝 Article summaries and analysis

**File naming:** `tesla_news_report_YYYYMMDD_HHMMSS.html`

**Perfect for:**
- Daily reviews
- Email reports to team
- Executive summaries
- Visual presentations

### 2. Markdown Report

**Features:**
- 📝 Clean text format
- 🔗 Clickable links
- 📊 ASCII charts
- 🐂🐻 Organized by stance (bullish/bearish/neutral)
- ⚡ High-impact section
- 📈 Category breakdown

**File naming:** `tesla_news_report_YYYYMMDD_HHMMSS.md`

**Perfect for:**
- Slack/Teams sharing
- GitHub/GitLab documentation
- Email (plain text)
- Note-taking apps

### 3. JSON Export

**Features:**
- 📦 Structured data
- 🔢 Complete metadata
- 📊 Statistics included
- 🔗 API-ready format

**File naming:** `tesla_news_report_YYYYMMDD_HHMMSS.json`

**Perfect for:**
- API integrations
- Data analysis (Python/R)
- Dashboards (Grafana, etc.)
- Database imports

## 📊 HTML Report Features

### Dashboard Metrics
- Total articles count
- Positive/Negative/Neutral distribution
- Average sentiment score
- Average impact score

### Interactive Filtering
Click buttons to filter articles:
- **All Articles** - Show everything
- **🐂 Bullish** - Only bullish news
- **🐻 Bearish** - Only bearish news
- **➖ Neutral** - Only neutral news
- **⚡ High Impact** - Articles with impact >= 4

### Article Table Columns
1. **#** - Article number
2. **Article** - Title (clickable) + Summary
3. **Category** - News category tag
4. **Sentiment** - Color-coded score
5. **Impact** - Star rating (★★★★★)
6. **Stance** - Bullish/Bearish/Neutral badge
7. **Date** - Publication date

### Visual Indicators

**Sentiment Colors:**
- 🟢 **Green** - Positive (> 0.3)
- 🟡 **Yellow** - Neutral (-0.3 to 0.3)
- 🔴 **Red** - Negative (< -0.3)

**Stance Badges:**
- 🐂 **Bullish** - Green badge
- 🐻 **Bearish** - Red badge
- ➖ **Neutral** - Gray badge

**Impact Stars:**
- ★★★★★ - Critical (5/5)
- ★★★★☆ - High (4/5)
- ★★★☆☆ - Moderate (3/5)
- ★★☆☆☆ - Low (2/5)
- ★☆☆☆☆ - Minimal (1/5)

## 📝 Markdown Report Structure

```markdown
# 📊 Tesla News Sentiment Report

## 📈 Summary Dashboard
[Statistics table with key metrics]

## 🐂 Bullish News
[Articles with bullish stance]

## 🐻 Bearish News
[Articles with bearish stance]

## ➖ Neutral News
[Articles with neutral stance]

## 📊 Category Breakdown
[Distribution by category]

## ⚡ High Impact Articles
[Articles with impact >= 4]
```

## 🔧 Example Workflows

### Daily Morning Briefing
```bash
# Generate quick HTML report for last 24 hours
python -m app.cli.generate_report --days 1 --format html
```

### Weekly Team Update
```bash
# Generate all formats for last 7 days
python -m app.cli.generate_report --days 7 --format all
```

### Monthly Analysis
```bash
# Generate comprehensive report for last 30 days
python -m app.cli.generate_report --days 30 --format all --output-dir ./monthly_reports
```

### Share on Slack/Teams
```bash
# Generate markdown for easy sharing
python -m app.cli.generate_report --days 7 --format markdown
# Then copy the .md file contents to Slack/Teams
```

### API Integration
```bash
# Export JSON for downstream processing
python -m app.cli.generate_report --days 30 --format json
# Use the JSON in your scripts/dashboards
```

## 📊 JSON Structure

```json
{
  "metadata": {
    "generated_at": "2025-10-15T14:30:00",
    "total_articles": 25
  },
  "statistics": {
    "total_articles": 25,
    "positive_count": 12,
    "negative_count": 8,
    "neutral_count": 5,
    "bullish_count": 10,
    "bearish_count": 7,
    "avg_sentiment": "+0.35",
    "avg_impact": "3.2",
    "category_distribution": {
      "Financial & Operational": 10,
      "Product & Technology": 8,
      "Market & Sentiment": 7
    }
  },
  "articles": [
    {
      "id": 1,
      "title": "Tesla Q3 Earnings Beat Expectations",
      "url": "https://example.com/article",
      "sentiment_score": 0.75,
      "impact_score": 4,
      "stance": "bullish",
      "summary": "Tesla exceeded Q3 earnings...",
      "sentiment_rationale": "Strong earnings...",
      "key_factors": "Earnings beat, Revenue growth..."
    }
  ]
}
```

## 🎯 Complete Pipeline Example

```bash
# 1. Fetch news with sentiment analysis
python -m app.cli.fetch_news --days 7 --limit 20

# 2. Generate comprehensive report
python -m app.cli.generate_report --days 7 --format all

# 3. Share with team
# - Open HTML report (auto-opens in browser)
# - Copy Markdown to Slack
# - Import JSON to dashboard
```

## 🔍 Advanced Usage

### Programmatic Report Generation

```python
from app.services.report_generator import ReportGenerator
from app.services.storage import StorageService

# Fetch records from database
storage = StorageService()
records = storage.get_recent_records(days=7)

# Generate reports
generator = ReportGenerator()

# HTML
generator.generate_html_report(
    records,
    "report.html",
    time_period="Last 7 days"
)

# Markdown
generator.generate_markdown_report(
    records,
    "report.md",
    time_period="Last 7 days"
)

# JSON
generator.generate_json_export(
    records,
    "report.json"
)
```

### Custom Filtering

Edit the HTML template (`templates/news_report.html`) to add custom filters:
- Filter by category
- Filter by source
- Filter by date range
- Filter by confidence level

### Email Reports

The HTML report is email-ready:
1. Generate HTML report
2. Open in browser
3. Send as attachment or embed in email

## 📋 Troubleshooting

### No Articles Found
```
⚠ No articles found in the specified date range.
```

**Solution:**
- Run `python -m app.cli.fetch_news` first to collect data
- Check date range with `--days` parameter
- Verify database has data

### Supabase Not Configured
```
✗ Supabase not configured. Cannot generate report.
```

**Solution:**
- Set `SUPABASE_CREDENTIALS` in `.env`
- Run database migrations
- Verify connection settings

### Report Not Opening
```
Report generated but not opening in browser
```

**Solution:**
- Use `--no-open-browser` and open manually
- Check browser is set as default
- Open file directly from `reports/` folder

## 📚 Tips & Best Practices

1. **Regular Reports**: Schedule daily/weekly report generation
2. **Archive Reports**: Keep historical reports for trend analysis
3. **Share Widely**: Use Markdown for easy team sharing
4. **Integrate**: Use JSON for dashboard integrations
5. **Customize**: Edit templates to match your needs

## 🚀 Next Steps

1. ✅ Run database migration
2. ✅ Fetch some news: `python -m app.cli.fetch_news --days 7`
3. ✅ Generate first report: `python -m app.cli.generate_report`
4. ✅ Review HTML report in browser
5. ✅ Share Markdown version with team

---

**Files:**
- HTML Template: `templates/news_report.html`
- Markdown Template: `templates/news_report.md`
- Generator Service: `app/services/report_generator.py`
- CLI Command: `app/cli/generate_report.py`

