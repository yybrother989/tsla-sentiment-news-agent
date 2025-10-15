# Tesla Sentiment News Agent - CLI Usage Guide

## 📋 Overview

The Tesla Sentiment News Agent fetches Tesla news from DuckDuckGo, classifies articles into categories, performs sentiment analysis, and stores results in Supabase.

## 🚀 Quick Start

```bash
# Fetch latest news with sentiment analysis (default: 7 days, all articles)
python -m app.cli.fetch_news

# Fetch news with custom options
python -m app.cli.fetch_news --days 3 --limit 5

# Fetch without sentiment analysis (faster)
python -m app.cli.fetch_news --skip-sentiment
```

## ⚙️ CLI Options

### `--days` (default: 7)
**Time window for news collection**

- `--days 1` → Past day
- `--days 7` → Past week (default)
- `--days 30` → Past month
- `--days 365` → Past year

```bash
python -m app.cli.fetch_news --days 3
```

### `--limit` (optional, default: None)
**Maximum number of articles to retrieve**

Controls the number of articles processed to save time and API costs. If not specified, all available articles are retrieved.

```bash
# Get all available articles (default)
python -m app.cli.fetch_news

# Get only 5 most recent articles
python -m app.cli.fetch_news --limit 5

# Get 20 articles for comprehensive analysis
python -m app.cli.fetch_news --limit 20
```

### `--skip-sentiment` (default: False)
**Skip sentiment analysis to save time**

When enabled:
- ✅ Faster execution (skips LLM sentiment analysis)
- ✅ Lower API costs (no sentiment LLM calls)
- ❌ No sentiment scores or impact ratings
- ❌ No sentiment summary

```bash
# Just fetch and classify (no sentiment)
python -m app.cli.fetch_news --skip-sentiment

# Quick check of latest news
python -m app.cli.fetch_news --days 1 --limit 5 --skip-sentiment
```

## 📊 Output Formats

### With Sentiment Analysis (default)
```
┌────────────┬─────────────┬───────────┬────────┬────────────┬──────────┐
│ Category   │ Title       │ Sentiment │ Impact │ Confidence │ Date     │
├────────────┼─────────────┼───────────┼────────┼────────────┼──────────┤
│ Financial  │ Tesla Q3... │ +0.75     │ 4/5    │ 90%        │ 2025-... │
└────────────┴─────────────┴───────────┴────────┴────────────┴──────────┘

Sentiment Summary:
  • Overall Sentiment: +0.45 (Positive)
  • Average Impact: 3.2/5
  • Positive Articles: 7 (70%)
  • Negative Articles: 2 (20%)
  • Neutral Articles: 1 (10%)
```

### Without Sentiment Analysis (`--skip-sentiment`)
```
┌────────────┬─────────────┬────────────┬────────────┬──────────┐
│ Category   │ Title       │ Source     │ Confidence │ Date     │
├────────────┼─────────────┼────────────┼────────────┼──────────┤
│ Financial  │ Tesla Q3... │ Yahoo Fin. │ 90%        │ 2025-... │
└────────────┴─────────────┴────────────┴────────────┴──────────┘

Category Distribution:
  • Financial & Operational: 5 articles
  • Product & Technology: 3 articles
  • Market & Sentiment: 2 articles
```

## 🎯 Common Use Cases

### 1. Quick Daily Check
```bash
# Fast check of today's news (no sentiment)
python -m app.cli.fetch_news --days 1 --limit 5 --skip-sentiment
```

### 2. Comprehensive Analysis
```bash
# Full analysis of past week with sentiment
python -m app.cli.fetch_news --days 7 --limit 20
```

### 3. Cost-Effective Monitoring
```bash
# Collect and classify only, analyze later
python -m app.cli.fetch_news --days 7 --skip-sentiment
```

### 4. High-Impact News Focus
```bash
# Get more articles to find high-impact news
python -m app.cli.fetch_news --days 3 --limit 30
```

## 📈 Performance Comparison

| Options | Speed | API Costs | Output |
|---------|-------|-----------|--------|
| Default | ~2-3 min | Medium | Full analysis |
| `--skip-sentiment` | ~30 sec | Low | Classification only |
| `--limit 5` | ~1 min | Low | Small dataset |
| `--limit 30` | ~4-5 min | High | Large dataset |

## 🔧 Pipeline Stages

### Stage 1: News Collection
- Searches DuckDuckGo for Tesla news
- Applies time filter based on `--days`
- Limits results to `--limit` articles
- Extracts: title, URL, date, summary

### Stage 2: Classification
- Categorizes into 7 news types:
  - Financial & Operational
  - Management & Governance
  - Product & Technology
  - Policy & Regulatory
  - Market & Sentiment
  - Strategic & Expansion
  - Macro & External
- Uses keyword matching + LLM validation
- Provides confidence score

### Stage 3: Sentiment Analysis (optional)
- Analyzes sentiment (-1.0 to +1.0)
- Scores market impact (1-5)
- Calculates confidence (0.0 to 1.0)
- Provides rationale and key factors
- **Skipped with `--skip-sentiment`**

### Stage 4: Storage
- Stores to Supabase database
- All data in single `sentiment_analysis` table
- Indexed for fast queries

## 🗄️ Database Schema

Run this migration to add sentiment fields:

```sql
-- migrations/003_add_sentiment_analysis_fields.sql
ALTER TABLE sentiment_analysis 
ADD COLUMN IF NOT EXISTS sentiment_score DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS impact_score INTEGER CHECK (impact_score >= 1 AND impact_score <= 5),
ADD COLUMN IF NOT EXISTS sentiment_confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS sentiment_rationale TEXT,
ADD COLUMN IF NOT EXISTS key_factors TEXT,
ADD COLUMN IF NOT EXISTS classification_rationale TEXT;
```

## 🔍 Example Workflows

### Morning Briefing
```bash
# Quick overview of overnight news
python -m app.cli.fetch_news --days 1 --limit 10 --skip-sentiment
```

### Weekly Analysis
```bash
# Full sentiment analysis of the week
python -m app.cli.fetch_news --days 7 --limit 30
```

### Pre-Trading Check
```bash
# High-impact news with sentiment
python -m app.cli.fetch_news --days 1 --limit 5
```

### Monthly Report
```bash
# Comprehensive monthly data collection
python -m app.cli.fetch_news --days 30 --limit 50
```

## 💡 Tips

1. **Start Small**: Use `--limit 5` to test configuration
2. **Save Costs**: Use `--skip-sentiment` for quick checks
3. **Balance Speed vs Coverage**: Higher limits = more data but slower
4. **Time Windows**: Align `--days` with DuckDuckGo filters (1, 7, 30, 365)
5. **Database**: Run migrations before first use
6. **API Keys**: Ensure `.env` has `OPENAI_API_KEY` for sentiment analysis

## 📝 Environment Variables

Required in `.env`:
```bash
OPENAI_API_KEY=sk-...              # For sentiment analysis
SUPABASE_CREDENTIALS={"url":"..."}  # For storage
PLANNER_LLM_MODEL=gpt-4o-mini       # LLM model (default)
USER_ID=1                           # Your user ID
```

## 🐛 Troubleshooting

**Error: "No articles found"**
- Try different time window (`--days 30`)
- Check internet connection
- Verify DuckDuckGo is accessible

**Error: "Sentiment analysis failed"**
- Check `OPENAI_API_KEY` in `.env`
- Use `--skip-sentiment` to bypass
- Verify API quota/billing

**Slow Performance**
- Reduce `--limit` to fewer articles
- Use `--skip-sentiment` flag
- Check network latency

**Missing Sentiment Scores**
- Run migration `003_add_sentiment_analysis_fields.sql`
- Ensure `--skip-sentiment` is NOT set
- Check logs for LLM errors

## 📚 Next Steps

1. ✅ Set up `.env` with API keys
2. ✅ Run database migrations
3. ✅ Test with `--days 1 --limit 5`
4. ✅ Review sentiment results
5. ✅ Configure report generation
6. ✅ Schedule automated runs

---

**Need Help?** Check logs with `LOG_LEVEL=debug` in `.env`

