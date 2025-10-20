#!/bin/bash

# Quick 30-second demo - shows Browser-Use in action

clear
echo "🚗 Tesla Sentiment Analysis - Quick Demo"
echo ""

source .venv/bin/activate

echo "📊 Collecting Reddit posts from r/wallstreetbets..."
echo "   (Watch the browser automatically search and extract posts)"
echo ""
python -m app.cli.reddit_sentiment reddit-sentiment --subreddit wallstreetbets --target 2 --scrolls 0

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Demo complete! Browser-Use AI collected Tesla posts automatically"
echo "════════════════════════════════════════════════════════════════"



