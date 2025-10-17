#!/bin/bash

echo "🚀 Starting Tesla Sentiment Analysis Workflow"
echo "================================================"
echo ""

# Step 1: Fetch Reddit posts
echo "📊 Step 1/3: Collecting Reddit posts from r/wallstreetbets..."
python -m app.cli.reddit_sentiment reddit-sentiment --subreddit wallstreetbets --target 5 --scrolls 0

if [ $? -ne 0 ]; then
    echo "❌ Reddit collection failed!"
    exit 1
fi

echo ""
echo "✅ Reddit collection complete!"
echo ""

# Step 2: Fetch Tesla news
echo "📰 Step 2/3: Fetching Tesla news from DuckDuckGo..."
python -m app.cli.fetch_news fetch --days 1 --limit 10

if [ $? -ne 0 ]; then
    echo "❌ News fetch failed!"
    exit 1
fi

echo ""
echo "✅ News fetch complete!"
echo ""

# Step 3: Generate and send email
echo "📧 Step 3/3: Generating and sending email report..."
python -m app.cli.send_email send --days 1

if [ $? -ne 0 ]; then
    echo "❌ Email send failed!"
    exit 1
fi

echo ""
echo "🎉 Complete workflow finished successfully!"
echo "================================================"
