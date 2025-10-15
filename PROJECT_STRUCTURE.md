# 🏗️ Tesla Sentiment News Agent - Project Structure

## 📂 Complete Directory Structure

```
tsla_sentiment_news_agent/
│
├── 📁 app/                          # Main application code
│   ├── adapters/                    # External service adapters
│   │   ├── news_sources.py          # DuckDuckGo news fetching with Browser-Use
│   │   └── supabase_client.py       # Supabase database adapter
│   │
│   ├── cli/                         # Command-line interfaces
│   │   ├── fetch_news.py            # Fetch, classify & analyze news
│   │   ├── generate_report.py       # Generate HTML/MD/JSON reports
│   │   └── send_email.py            # Send AI-powered email notifications
│   │
│   ├── domain/                      # Business logic and models
│   │   ├── schemas.py               # Pydantic data models
│   │   ├── taxonomy.py              # 7-category news taxonomy
│   │   └── validators.py            # Data validation utilities
│   │
│   ├── infra/                       # Infrastructure and configuration
│   │   ├── config.py                # Settings and environment variables
│   │   ├── logging.py               # Logging configuration
│   │   └── telemetry.py             # Performance tracking
│   │
│   └── services/                    # Core business services
│       ├── classifier.py            # News classification (keywords + LLM)
│       ├── email_generator.py       # LLM-powered email content generation
│       ├── email_service.py         # SMTP email sending
│       ├── report_generator.py      # Report generation (HTML/MD/JSON)
│       ├── scorer.py                # Sentiment & impact analysis
│       └── storage.py               # Database persistence
│
├── 📁 docs/                         # Documentation
│   └── AI_Powered_Stock_Sentiment_Design_Doc.md  # Original design doc
│
├── 📁 email_previews/               # Email preview outputs
│   └── *.txt                        # Preview files
│
├── 📁 migrations/                   # Database migrations
│   └── 001_create_sentiment_analysis_table.sql  # Complete DB schema
│
├── 📁 reports/                      # Generated reports
│   ├── *.html                       # Interactive HTML reports
│   ├── *.md                         # Markdown reports
│   └── *.json                       # JSON data exports
│
├── 📁 templates/                    # Jinja2 templates
│   ├── email_notification.html      # Beautiful email template
│   ├── news_report.html             # Interactive HTML report
│   └── news_report.md               # Markdown report template
│
├── 📁 tests/                        # Test suite
│   ├── test_domain_schemas.py       # Schema validation tests
│   ├── test_news_fetch_live.py      # Live news fetching tests
│   ├── test_news_sources.py         # News source tests
│   └── test_supabase_integration.py # Database integration tests
│
├── 📄 CLI_USAGE.md                  # CLI commands guide
├── 📄 EMAIL_SETUP_GUIDE.md          # Email notification setup
├── 📄 MIGRATION_GUIDE.md            # Database migration guide
├── 📄 README.md                     # Main project documentation
├── 📄 REPORT_GENERATION_GUIDE.md    # Report generation guide
├── 📄 env.example                   # Environment variables template
├── 📄 pyproject.toml                # Python dependencies
└── 📄 test_quick.sh                 # Quick test script
```

## 🎯 Core Components

### 1. News Collection Pipeline
**File:** `app/adapters/news_sources.py`

- Searches DuckDuckGo for Tesla news
- Dynamic time filter mapping (1 day → "Past day", 7 days → "Past week", etc.)
- Browser-Use integration with structured output
- Extracts: title, URL, date, summary
- Returns: `List[CollectorDocument]`

**CLI:** `python -m app.cli.fetch_news`

---

### 2. News Classification System
**File:** `app/services/classifier.py`

- 7-category taxonomy (Financial, Product, Strategic, etc.)
- Keyword-based pre-classification (fast)
- LLM validation for low-confidence cases
- Returns: category, confidence, rationale

**Categories:**
1. Financial & Operational
2. Product & Technology
3. Strategic & Expansion
4. Management & Governance
5. Policy & Regulatory
6. Market & Sentiment
7. Macro & External

---

### 3. Sentiment Analysis Engine
**File:** `app/services/scorer.py`

- **Sentiment Score:** -1.0 to +1.0 (negative to positive)
- **Impact Score:** 1-5 (low to high market impact)
- **Confidence Score:** 0.0 to 1.0 (analysis confidence)
- **Stance:** bullish/bearish/neutral
- **Summary:** One-sentence article summary
- **Rationale:** Explains sentiment AND impact
- **Key Factors:** 3-5 influencing factors

**Category-aware prompting** for better accuracy.

---

### 4. Database Persistence
**File:** `app/services/storage.py`

- Single table: `sentiment_analysis`
- Atomic upserts (all data in one write)
- Deduplication by URL
- Row-level security enabled

**Schema:** See `migrations/001_create_sentiment_analysis_table.sql`

---

### 5. Report Generation
**File:** `app/services/report_generator.py`

**Formats:**
- **HTML** - Interactive web report with filtering
- **Markdown** - Clean text for Slack/Teams
- **JSON** - Structured data for APIs

**CLI:** `python -m app.cli.generate_report`

---

### 6. Email Notifications
**Files:**
- `app/services/email_generator.py` - LLM content generation
- `app/services/email_service.py` - SMTP sending
- `templates/email_notification.html` - Beautiful template

**Features:**
- AI-generated executive summary
- Market outlook analysis
- Key takeaways (3-5 bullets)
- Action items (2-3 recommendations)
- Visual sentiment dashboard
- Top stories with summaries

**CLI:** `python -m app.cli.send_email`

---

## 📊 Data Flow

```
┌─────────────────┐
│  DuckDuckGo     │
│  News Search    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Browser-Use    │
│  Extraction     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Classifier     │
│  (7 categories) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Sentiment      │
│  Analyzer (LLM) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Supabase DB    │
│  (Single Table) │
└────────┬────────┘
         │
         ├──────────────┐
         │              │
         ▼              ▼
┌──────────────┐  ┌──────────────┐
│   Reports    │  │    Email     │
│ (HTML/MD/JSON)│  │ Notification │
└──────────────┘  └──────────────┘
```

## 🚀 CLI Commands

### Fetch News
```bash
python -m app.cli.fetch_news --days 7 --limit 20
python -m app.cli.fetch_news --days 1 --skip-sentiment  # Fast mode
```

### Generate Report
```bash
python -m app.cli.generate_report --days 7 --format all
python -m app.cli.generate_report --days 1 --format html
```

### Send Email
```bash
python -m app.cli.send_email --days 1 --generate-only  # Preview
python -m app.cli.send_email --days 1  # Send
```

## 📝 Configuration Files

### `.env` (Your private config)
```bash
# LLM
OPENAI_API_KEY=sk-...
PLANNER_LLM_MODEL=gpt-4o-mini

# Database
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...

# Email
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
RECIPIENT_EMAILS=recipient@example.com
```

### `env.example` (Template)
Template for creating your `.env` file

### `pyproject.toml` (Dependencies)
Python package dependencies and project metadata

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation |
| `CLI_USAGE.md` | CLI commands reference |
| `MIGRATION_GUIDE.md` | Database setup guide |
| `REPORT_GENERATION_GUIDE.md` | Report generation guide |
| `EMAIL_SETUP_GUIDE.md` | Email notification setup |
| `docs/AI_Powered_Stock_Sentiment_Design_Doc.md` | Original design document |

## 🧪 Testing

### Test Files
- `test_domain_schemas.py` - Schema validation
- `test_news_fetch_live.py` - Live news fetching
- `test_news_sources.py` - News source adapters
- `test_supabase_integration.py` - Database integration

### Quick Test Script
```bash
./test_quick.sh  # Runs full pipeline test
```

## 🗄️ Database Schema

### Single Table: `sentiment_analysis`

**Article Fields:**
- id, user_id, ticker, url, title, text, source, published_at

**Classification Fields:**
- category, classification_confidence, classification_rationale

**Sentiment Analysis Fields:**
- sentiment_score, impact_score, sentiment_confidence
- sentiment_rationale, key_factors, summary, stance

**See:** `migrations/001_create_sentiment_analysis_table.sql`

## 🔧 Utility Scripts

### `test_quick.sh`
Quick pipeline test for fetching and classifying news

```bash
chmod +x test_quick.sh
./test_quick.sh
```

## 📦 Output Directories

### `reports/`
Generated HTML, Markdown, and JSON reports

### `email_previews/`
Email preview files (when using `--generate-only`)

## 🎯 Key Features

1. ✅ **Dynamic News Collection** - DuckDuckGo with intelligent time filtering
2. ✅ **Smart Classification** - 7 categories with keyword + LLM hybrid
3. ✅ **Comprehensive Sentiment Analysis** - Multi-dimensional scoring
4. ✅ **Flexible Reporting** - Multiple formats (HTML/MD/JSON)
5. ✅ **AI-Powered Email Notifications** - LLM-generated summaries
6. ✅ **Production Ready** - Error handling, logging, retry logic

## 📊 Technology Stack

- **Language:** Python 3.11+
- **Web Automation:** Browser-Use
- **LLM:** OpenAI GPT-4o-mini
- **Database:** Supabase (PostgreSQL)
- **Email:** SMTP (Gmail/Outlook/SendGrid)
- **Templates:** Jinja2
- **CLI:** Typer
- **Data Validation:** Pydantic
- **Testing:** pytest

## 🚀 Quick Start

```bash
# 1. Setup environment
cp env.example .env
# Edit .env with your API keys

# 2. Run database migration
# Execute: migrations/001_create_sentiment_analysis_table.sql

# 3. Fetch news
python -m app.cli.fetch_news --days 7 --limit 20

# 4. Generate report
python -m app.cli.generate_report --days 7 --format all

# 5. Send email
python -m app.cli.send_email --days 1 --generate-only
```

## 📈 Development Workflow

```bash
# Daily development cycle

# 1. Fetch latest news
python -m app.cli.fetch_news --days 1 --limit 10

# 2. Review in database (Supabase dashboard)

# 3. Test email preview
python -m app.cli.send_email --days 1 --generate-only

# 4. Send to yourself for testing
python -m app.cli.send_email --days 1 --recipient your-email@gmail.com

# 5. Generate full report
python -m app.cli.generate_report --days 1 --format html
```

---

**Last Updated:** October 15, 2025  
**Status:** Production Ready ✅

