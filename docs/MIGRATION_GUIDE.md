# Database Migration Guide

## 🗄️ Complete Fresh Setup

You've deleted the existing table and are starting fresh. Here's your new clean migration:

### Step 1: Run the Migration in Supabase

1. Go to your Supabase SQL Editor
2. Copy and paste the contents of `migrations/001_create_sentiment_analysis_table.sql`
3. Execute the SQL

This will create a complete `sentiment_analysis` table with:

✅ **All article fields** (url, title, text, source, published_at)  
✅ **Classification fields** (category, classification_confidence, classification_rationale)  
✅ **Sentiment analysis fields** (sentiment_score, impact_score, sentiment_confidence, sentiment_rationale, key_factors, summary, stance)  
✅ **Proper indexes** for fast queries  
✅ **Row Level Security (RLS)** enabled  
✅ **Auto-updated timestamps**  

### Step 2: Verify the Table

```sql
-- Check if table exists
SELECT * FROM sentiment_analysis LIMIT 1;

-- View table structure
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'sentiment_analysis'
ORDER BY ordinal_position;
```

### Step 3: Test the Pipeline

```bash
# Quick test with 3 articles
python -m app.cli.fetch_news --days 1 --limit 3

# Full test with sentiment analysis
python -m app.cli.fetch_news --days 1 --limit 5
```

## 📊 Table Schema

### Core Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGSERIAL | Primary key |
| `user_id` | INTEGER | User ID (default: 1) |
| `ticker` | VARCHAR(10) | Stock ticker (TSLA) |
| `url` | TEXT | Article URL (unique) |
| `title` | TEXT | Article headline |
| `text` | TEXT | Article content |
| `source` | VARCHAR(255) | News source |
| `published_at` | TIMESTAMP | Publication time |

### Classification Fields
| Field | Type | Description |
|-------|------|-------------|
| `category` | VARCHAR(50) | News category |
| `classification_confidence` | DECIMAL(3,2) | 0.0 to 1.0 |
| `classification_rationale` | TEXT | Why this category |

### Sentiment Analysis Fields
| Field | Type | Description |
|-------|------|-------------|
| `sentiment_score` | DECIMAL(3,2) | -1.0 to +1.0 |
| `impact_score` | INTEGER | 1 to 5 |
| `sentiment_confidence` | DECIMAL(3,2) | 0.0 to 1.0 |
| `sentiment_rationale` | TEXT | **Explains sentiment AND impact** |
| `key_factors` | TEXT | Comma-separated factors |
| `summary` | TEXT | **One-sentence summary** |
| `stance` | VARCHAR(20) | **bullish/bearish/neutral** |

## 🔍 Example Queries

### Get Latest Bullish News
```sql
SELECT title, sentiment_score, impact_score, summary, stance
FROM sentiment_analysis
WHERE stance = 'bullish'
  AND published_at > NOW() - INTERVAL '7 days'
ORDER BY impact_score DESC, sentiment_score DESC
LIMIT 10;
```

### High-Impact News by Category
```sql
SELECT 
    category,
    COUNT(*) as article_count,
    AVG(sentiment_score) as avg_sentiment,
    AVG(impact_score) as avg_impact
FROM sentiment_analysis
WHERE impact_score >= 4
  AND published_at > NOW() - INTERVAL '30 days'
GROUP BY category
ORDER BY avg_impact DESC;
```

### Sentiment Trend Analysis
```sql
SELECT 
    DATE(published_at) as date,
    stance,
    COUNT(*) as count,
    AVG(sentiment_score) as avg_sentiment,
    AVG(impact_score) as avg_impact
FROM sentiment_analysis
WHERE published_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(published_at), stance
ORDER BY date DESC, stance;
```

### Top Articles by Impact
```sql
SELECT 
    title,
    category,
    stance,
    sentiment_score,
    impact_score,
    summary,
    key_factors,
    published_at
FROM sentiment_analysis
WHERE impact_score >= 4
  AND sentiment_confidence >= 0.7
ORDER BY impact_score DESC, sentiment_score DESC
LIMIT 20;
```

## 🚀 What's Different from Before

### ✅ New Fields Added:
1. **`summary`** - One-sentence article summary
2. **`stance`** - Market direction (bullish/bearish/neutral)
3. **`classification_rationale`** - Why the category was chosen

### ✅ Enhanced Fields:
1. **`sentiment_rationale`** - Now explains BOTH sentiment AND impact scores

### ✅ Better Indexing:
- Indexes on `stance` for quick filtering
- Composite indexes for common query patterns
- Optimized for time-based queries

## 🎯 Complete Record Example

```json
{
  "id": 1,
  "user_id": 1,
  "ticker": "TSLA",
  "url": "https://example.com/tesla-earnings",
  "title": "Tesla Q3 Earnings Beat Expectations",
  "text": "Tesla reported strong Q3 earnings...",
  "source": "duckduckgo",
  "published_at": "2025-10-15T10:00:00Z",
  
  "category": "Financial & Operational",
  "classification_confidence": 0.95,
  "classification_rationale": "Article focuses on quarterly earnings and financial performance",
  
  "sentiment_score": 0.75,
  "impact_score": 4,
  "sentiment_confidence": 0.90,
  "sentiment_rationale": "Strong earnings beat with raised guidance indicates robust performance and positive outlook, significant for investor sentiment",
  "key_factors": "Earnings beat, Revenue growth, Raised guidance, Strong margins, Production efficiency",
  "summary": "Tesla exceeded Q3 earnings expectations with strong revenue growth and raised full-year guidance",
  "stance": "bullish"
}
```

## 🔧 Troubleshooting

### Issue: RLS Policy Blocking Inserts
```sql
-- Disable RLS temporarily for testing
ALTER TABLE sentiment_analysis DISABLE ROW LEVEL SECURITY;

-- Or set the user_id parameter
SET app.user_id = '1';
```

### Issue: Check Constraint Violations
- `sentiment_score` must be between -1.00 and +1.00
- `impact_score` must be between 1 and 5
- `sentiment_confidence` must be between 0.00 and 1.00
- `stance` must be 'bullish', 'bearish', or 'neutral'

### Issue: Duplicate URL
- Table has UNIQUE constraint on `url`
- Use UPSERT to update existing records
- Check `app/services/storage.py` for upsert logic

## 📝 Next Steps

1. ✅ Run the migration SQL in Supabase
2. ✅ Test with `--days 1 --limit 3` 
3. ✅ Verify data in Supabase table
4. ✅ Run full analysis with sentiment
5. ✅ Query results using example queries above

---

**Migration file**: `migrations/001_create_sentiment_analysis_table.sql`  
**Status**: Ready to execute ✅

