#!/bin/bash
# Quick test script for Reuters news fetching with classification

cd /Users/yuegao/tsla_sentiment_news_agent
source .venv/bin/activate

echo "🧪 Testing Tesla News Pipeline (7-day window)"
echo "=============================================="
echo "Step 1: Fetch from Reuters"
echo "Step 2: Classify with LLM"
echo "Step 3: Upload to Supabase"
echo "=============================================="
echo ""

# Fetch, classify, and store
timeout 240 python -m app.cli.fetch_news --days 7

echo ""
echo "=============================================="
echo "✅ Test complete!"

