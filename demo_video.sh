#!/bin/bash

clear
echo "════════════════════════════════════════════════════════════════"
echo "  🚗 Tesla Sentiment Analysis - Browser-Use AI Demo"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "This demo will show:"
echo "  1. 📰 AI agent fetching Tesla news from DuckDuckGo"
echo "  2. 📊 AI agent collecting Reddit posts from r/wallstreetbets"
echo "  3. 📧 Generating and previewing email report"
echo ""
echo "Press ENTER to start..."
read

# Activate virtual environment
source .venv/bin/activate

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  📰 DEMO 1: Fetching Tesla News with Browser-Use"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Watch the browser automatically:"
echo "  • Search DuckDuckGo for 'Tesla news'"
echo "  • Click the News tab"
echo "  • Apply time filter (Past day)"
echo "  • Extract article data with AI"
echo ""
sleep 2

python -m app.cli.fetch_news --days 1 --limit 3

echo ""
echo "✅ News collection complete!"
echo ""
echo "Press ENTER to continue to Reddit demo..."
read

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  📊 DEMO 2: Collecting Reddit Posts with Browser-Use"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Watch the browser automatically:"
echo "  • Navigate to r/wallstreetbets search"
echo "  • Search for 'TSLA OR Tesla'"
echo "  • Apply filters (sort by top, past week)"
echo "  • Extract top posts with AI"
echo ""
sleep 2

python -m app.cli.reddit_sentiment reddit-sentiment --subreddit wallstreetbets --target 3 --scrolls 0

echo ""
echo "✅ Reddit collection complete!"
echo ""
echo "Press ENTER to generate email report..."
read

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  📧 DEMO 3: Generating Email Report"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Generating AI-powered email with:"
echo "  • Tesla news articles with sentiment analysis"
echo "  • Top Reddit posts with clickable links"
echo "  • Executive summary and action items"
echo ""
sleep 2

python -m app.cli.send_email --days 1 --generate-only

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🎉 Demo Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  ✅ Fetched Tesla news automatically"
echo "  ✅ Collected top Reddit posts automatically"
echo "  ✅ Generated professional email report"
echo ""
echo "All data saved to Supabase database!"
echo ""
echo "To run the full workflow:"
echo "  ./run_full_workflow.sh"
echo ""
echo "════════════════════════════════════════════════════════════════"



