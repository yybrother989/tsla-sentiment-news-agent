# Tesla Stock Sentiment & News Analysis Agent

An AI-powered system that automatically collects, analyzes, and scores Tesla (TSLA) stock news and sentiment using Browser-Use automation, LLM reasoning, and Supabase persistence.

> **⚠️ Note**: This is currently a **framework implementation**. The news sentiment evaluation is still in progress. The current version demonstrates the complete pipeline architecture with placeholder reasoning and scoring logic. Real LLM-based sentiment analysis and advanced features will be added in future iterations.

## Prerequisites

- Python 3.11+
- Google Chrome installed
- OpenAI API key
- Supabase account and project

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd tsla_sentiment_news_agent
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp env.example .env
```

Edit `.env` and add your credentials:

```bash
# Required
OPENAI_API_KEY=sk-proj-your-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Optional
PLANNER_LLM_MODEL=gpt-4o-mini
APP_USER_ID=1
APP_LOG_LEVEL=INFO
```

### 3. Setup Supabase Database

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project (or create a new one)
3. Navigate to **SQL Editor** in the left sidebar
4. Click **New Query**
5. Open `migrations/001_create_tables.sql` in this repository
6. Copy the entire SQL script and paste it into the Supabase SQL Editor
7. Click **Run** (or press Ctrl/Cmd + Enter)
8. Verify tables were created by going to **Table Editor** - you should see `articles`, `events`, and `scores` tables

### 4. Run the Agent

### Fetch News
```bash
# Fetch Tesla news from all sources (past 7 days)
python -m app.cli.fetch_news --days 7
```

### Generate Report
```bash
# Generate weekly sentiment report
python -m app.cli.generate_report
```

### Run Full Pipeline
```bash
# Complete analysis pipeline
python -m app.cli.run_once TSLA --window-hours 12 --max-docs 10
```

### 5. Verify Results

- Check the terminal output for a formatted table with analysis results
- Go to your Supabase **Table Editor** to view stored data in the database

## Testing

Run all tests:
```bash
pytest
```

Run Supabase integration tests:
```bash
pytest tests/test_supabase_integration.py -v
```

## Troubleshooting

### Browser-Use Issues

**Problem**: Browser fails to launch  
**Solution**: Ensure Chrome is installed. On macOS it should be at `/Applications/Google Chrome.app`. On other systems, update the path in `app/adapters/browser_client.py`

**Problem**: Bot detection or CAPTCHA  
**Solution**: The agent uses stealth mode but may still encounter challenges. This is expected and the system will fall back to stub data.

### Supabase Issues

**Problem**: "Could not find table" error  
**Solution**: Run the migration script `migrations/001_create_tables.sql` in Supabase SQL Editor

**Problem**: Permission denied  
**Solution**: Use the **service role key** from Settings → API, not the anon/public key

**Problem**: Connection timeout  
**Solution**: Check internet connection. Free tier projects pause after inactivity - visit your dashboard to wake it up.

## What's Next

This framework is ready for enhancement with:
- Real LLM-based sentiment analysis (currently using placeholder logic)
- Alpha Vantage API integration for structured news feeds
- Advanced scoring algorithms with market correlation
- Multi-ticker support
- Web dashboard for visualization
- Scheduled/automated runs

See `docs/AI_Powered_Stock_Sentiment_Design_Doc.md` for the complete system design.

## Support

For questions or issues, contact the development team.

---

**Built with**: Browser-Use • OpenAI • Supabase • Python 3.11
