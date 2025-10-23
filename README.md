# Tesla Sentiment News Agent 🚗📰

An AI-powered sentiment analysis system that monitors Tesla (TSLA) news, Twitter discussions, and Reddit communities to generate comprehensive daily email reports for investors.

## 🌟 Features

- **📰 Automated News Collection**: Fetches Tesla news from DuckDuckGo with time-based filtering
- **🐦 Twitter Monitoring**: Collects tweets via n8n + Apify (or legacy Browser-Use with authentication)
- **📊 Reddit Tracking**: Monitors r/wallstreetbets for top Tesla discussions
- **🤖 AI-Powered Sentiment Analysis**: Uses GPT-4o to analyze sentiment and market impact
- **📧 Smart Email Reports**: Generates professional HTML email summaries with AI insights
- **💾 Database Storage**: Stores all data in Supabase with structured schemas
- **🔄 Session Caching**: Persistent browser sessions for efficient data collection

## 🏗️ Architecture

```
app/
├── adapters/          # External integrations (news, Twitter, Reddit, Supabase)
├── cli/               # Command-line interfaces for each workflow
├── domain/            # Core business logic and data schemas
├── infra/             # Configuration, logging, telemetry
├── services/          # Business services (sentiment analysis, email generation)
└── pipelines/         # Data processing workflows (empty, for future use)

migrations/            # SQL database schema migrations
templates/             # HTML/Markdown email templates
docs/                  # Documentation files
tests/                 # Unit and integration tests
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (3.12 recommended)
- OpenAI API key
- Supabase account (for database)
- Gmail account (for sending emails)

**For Twitter collection, choose one:**
- **n8n + Apify** (recommended): n8n instance + Apify account
- **Browser-Use** (legacy): Chrome browser installed

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/tsla_sentiment_news_agent.git
cd tsla_sentiment_news_agent
```

2. **Set up Python environment**
```bash
# Using uv (recommended)
uv venv --python 3.12
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
uvx playwright install chromium --with-deps

# Or using pip
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium --with-deps
```

3. **Configure environment variables**
```bash
cp env.example .env
# Edit .env with your API keys and credentials
```

Required environment variables:
- `OPENAI_API_KEY` - OpenAI API key for GPT-4o
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase service role key
- `SMTP_USER` / `SMTP_PASSWORD` - Gmail credentials
- `RECIPIENT_EMAILS` - Email recipient(s)

4. **Set up database**
```bash
# Run migrations in your Supabase SQL editor
cat migrations/*.sql
```

## 📖 Usage

### 1. Fetch Tesla News
```bash
python -m app.cli.fetch_news --days 1 --limit 10
```

### 2. Collect Reddit Posts
```bash
# First run (collects top 5 posts from r/wallstreetbets)
python -m app.cli.reddit_sentiment reddit-sentiment --subreddit wallstreetbets --target 5
```

### 3. Collect Twitter/X Posts

**Option A: n8n + Apify (Recommended)**
```bash
# Configure n8n in .env (see docs/N8N_INTEGRATION.md)
# N8N_API_KEY, N8N_BASE_URL, N8N_TWITTER_WORKFLOW_ID

# Collect tweets via n8n workflow
python -m app.cli.twitter_sentiment twitter-sentiment --target 10
```

**Option B: Browser-Use (Legacy)**
```bash
# Step 1: Set up Twitter session (one-time)
python -m app.cli.twitter_sentiment twitter-login-simple

# Step 2: Collect tweets with browser automation
python -m app.cli.twitter_sentiment twitter-sentiment --target 10 --use-browser
```

See [N8N Integration Guide](docs/N8N_INTEGRATION.md) for setup details.

### 4. Send Email Report
```bash
# Sends report with news from past 24 hours + top Reddit posts from past week
python -m app.cli.send_email --days 1

# Send to specific recipient
python -m app.cli.send_email --days 1 --recipient user@example.com

# Preview without sending
python -m app.cli.send_email --days 1 --generate-only
```

### 5. Complete Workflow
```bash
# Run all steps in sequence
./run_full_workflow.sh
```

## 🛠️ Key Technologies

- **[n8n](https://n8n.io/)** - Workflow automation for Twitter data collection
- **[Apify](https://apify.com/)** - Twitter scraper API
- **[Browser-Use](https://github.com/browser-use/browser-use)** - AI-powered browser automation (legacy option)
- **OpenAI GPT-4o** - LLM for sentiment analysis and content generation
- **Supabase** - PostgreSQL database for data storage
- **Playwright** - Browser automation runtime (for browser-use mode)
- **Jinja2** - HTML email templating
- **Typer** - CLI framework
- **Pydantic** - Data validation and schemas

## 📊 Database Schema

### `sentiment_analysis` (News Articles)
- Article metadata (title, URL, published date)
- Sentiment scores and labels
- Category classification
- Impact ratings

### `twitter_sentiment` (Twitter/X Posts)
- Tweet content and metadata
- Engagement metrics
- Author information
- Sentiment analysis results

### `reddit_sentiment` (Reddit Posts)
- Post title, URL, and subreddit
- Upvote and comment counts
- Author username
- Post timestamp

## 🔧 Configuration

Key settings in `app/infra/config.py`:
- `planner_llm_model`: LLM model for sentiment analysis (default: gpt-4o-mini)
- `planner_max_documents`: Maximum articles to process
- `user_id`: User ID for multi-tenant support (default: 1)

## 📚 Documentation

Comprehensive documentation available in the `docs/` folder:
- [CLI Usage Guide](docs/CLI_USAGE.md)
- [Email Setup Guide](docs/EMAIL_SETUP_GUIDE.md)
- [Report Generation Guide](docs/REPORT_GENERATION_GUIDE.md)
- [Browser-Use Patterns](docs/BROWSER_USE_PATTERNS.md)
- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Migration Guide](docs/MIGRATION_GUIDE.md)

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run specific test
pytest tests/test_news_sources.py

# Run with coverage
pytest --cov=app tests/
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- [Browser-Use](https://github.com/browser-use/browser-use) for the amazing browser automation framework
- OpenAI for GPT-4o
- Supabase for the database platform

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**⚠️ Disclaimer**: This tool is for educational and research purposes. Always comply with Twitter/Reddit's Terms of Service and rate limits. Not financial advice.
