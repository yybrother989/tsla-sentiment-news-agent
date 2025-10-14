# Supabase Database Setup

## Prerequisites
- Supabase account at https://supabase.com
- Project created with URL and service role key

## Setup Steps

### 1. Configure Environment Variables

Add to your `.env` file:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 2. Create Database Tables

Go to your Supabase project dashboard:
1. Navigate to **SQL Editor**
2. Click **New Query**
3. Copy the contents of `migrations/001_create_tables.sql`
4. Click **Run** to execute

This will create:
- `articles` table - stores raw news content
- `events` table - stores sentiment analysis results
- `scores` table - stores fear-greed scores
- Indexes for performance
- Row Level Security policies
- Auto-update triggers

### 3. Verify Tables

In the Supabase dashboard:
1. Go to **Table Editor**
2. You should see three tables: `articles`, `events`, `scores`
3. Check that columns match the schema in `app/domain/schemas.py`

### 4. Test Connection

Run the integration tests:
```bash
pytest tests/test_supabase_integration.py -v
```

All tests should pass if tables are created correctly.

## Schema Overview

### articles
- Primary storage for news content
- Unique constraint on `url`
- Indexed on `canonical_hash` for deduplication
- Indexed on `ticker` and `published_at` for queries

### events
- Sentiment analysis results
- Foreign key to `articles.url`
- Stores sentiment score, stance, event type

### scores
- Fear-greed index (1-10)
- Foreign key to `articles.url`
- Stores rationale for score

## Row Level Security

All tables have RLS enabled with policies allowing:
- Users to access their own data (filtered by `user_id`)
- Service role to access all data (for backend operations)

## Troubleshooting

### "Could not find table" error
- Ensure migration SQL was executed successfully
- Check that tables exist in **Table Editor**
- Verify you're using the correct project URL

### Permission denied
- Ensure you're using the **service role key**, not the anon key
- Check RLS policies are configured correctly

### Connection timeout
- Verify your internet connection
- Check Supabase project is not paused (free tier pauses after inactivity)

