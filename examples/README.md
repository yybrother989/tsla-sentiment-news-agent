# Browser-Use Examples for Tesla Sentiment Analysis

This directory contains curated browser-use examples specifically tailored for the Tesla sentiment analysis project. These examples demonstrate patterns used in the main codebase and provide learning paths for extending the system.

## 📚 Official Browser-Use Resources

- **Full Examples Repository**: `/Users/yuegao/tsla_sentiment_news_agent/.browser-use-reference/examples/`
- **Official GitHub**: https://github.com/browser-use/browser-use/tree/main/examples
- **Official Docs**: https://docs.browser-use.com/

## 🎯 Learning Path

### Beginner (Start Here)
1. `01_basic_search.py` - Simple search and data extraction
2. `02_session_caching.py` - Save and reuse authentication sessions
3. `03_structured_extraction.py` - Extract data into Pydantic models

### Intermediate (Build On Project Patterns)
4. `04_social_scraping.py` - Twitter/Reddit-style social media scraping
5. `05_sentiment_collection.py` - Complete sentiment collection pipeline
6. `06_parallel_collection.py` - Collect from multiple sources simultaneously

### Advanced (Extend the Project)
7. `07_custom_filters.py` - Advanced filtering and content selection
8. `08_multi_platform.py` - Add new social media platforms
9. `09_real_time_monitoring.py` - Monitor for new posts in real-time

## 📂 Official Examples Overview

### Getting Started (`/.browser-use-reference/examples/getting_started/`)
- `01_basic_search.py` - Your first browser-use agent
- `02_form_filling.py` - Interact with web forms
- `03_data_extraction.py` - Extract structured data
- `04_multi_step_task.py` - Complex multi-step workflows
- `05_fast_agent.py` - Optimized fast execution

### Browser Features (`/.browser-use-reference/examples/browser/`)
- `save_cookies.py` - **HIGHLY RELEVANT**: Session persistence (used in twitter_source.py)
- `parallel_browser.py` - Run multiple browsers simultaneously
- `real_browser.py` - Use your existing Chrome profile
- `using_cdp.py` - Chrome DevTools Protocol integration

### Features (`/.browser-use-reference/examples/features/`)
- `scrolling_page.py` - **HIGHLY RELEVANT**: Smart scrolling strategies (used for Twitter/Reddit)
- `custom_output.py` - Define custom output formats
- `multi_tab.py` - Work with multiple tabs
- `download_file.py` - Download files during automation
- `video_recording.py` - Record browser sessions for debugging

### Custom Functions (`/.browser-use-reference/examples/custom-functions/`)
- `parallel_agents.py` - **HIGHLY RELEVANT**: Run agents in parallel (great for multi-source collection)
- `2fa.py` - Handle two-factor authentication
- `advanced_search.py` - Complex search patterns
- `file_upload.py` - Upload files to websites

### Use Cases (`/.browser-use-reference/examples/use-cases/`)
- `find_influencer_profiles.py` - **RELEVANT**: Similar to Twitter influencer tracking
- `shopping.py` - E-commerce automation patterns
- `check_appointment.py` - Monitoring and notification patterns

### Models (`/.browser-use-reference/examples/models/`)
- Different LLM providers (OpenAI, Anthropic, Gemini, Ollama, etc.)
- Cost optimization strategies
- Model selection guide

### Integrations (`/.browser-use-reference/examples/integrations/`)
- `slack/` - Slack bot integration
- `discord/` - Discord bot integration
- `gmail_2fa_integration.py` - Email-based 2FA

### Apps (`/.browser-use-reference/examples/apps/`)
- `news-use/` - **VERY RELEVANT**: News monitoring application
- `msg-use/` - Messaging automation
- `ad-use/` - Ad generation and analysis

## 🔗 How to Use Official Examples

### Method 1: Run Examples Directly
```bash
# Navigate to the reference directory
cd /Users/yuegao/tsla_sentiment_news_agent/.browser-use-reference/examples

# Run any example
python getting_started/01_basic_search.py
python browser/save_cookies.py
python features/scrolling_page.py
```

### Method 2: Copy and Adapt
```bash
# Copy an example to your workspace
cp .browser-use-reference/examples/browser/save_cookies.py examples/my_custom_example.py

# Modify it for your needs
# ...
```

### Method 3: Study and Learn
- Read the source code
- Understand the patterns
- Apply concepts to your project

## 🎓 Recommended Study Order for This Project

1. **Session Management**
   - Study: `.browser-use-reference/examples/browser/save_cookies.py`
   - Compare: `app/adapters/twitter_source.py` (lines 318-376)
   - Learn: How to persist authentication across runs

2. **Scrolling and Collection**
   - Study: `.browser-use-reference/examples/features/scrolling_page.py`
   - Compare: `app/adapters/twitter_source.py` (lines 169-217)
   - Learn: Smart scrolling strategies for infinite feeds

3. **Structured Data Extraction**
   - Study: `.browser-use-reference/examples/cloud/03_structured_output.py`
   - Compare: `app/adapters/twitter_source.py` (lines 21-43)
   - Learn: Pydantic schema design for data validation

4. **Parallel Collection**
   - Study: `.browser-use-reference/examples/custom-functions/parallel_agents.py`
   - Future: Collect from Twitter + Reddit + LinkedIn simultaneously
   - Learn: AsyncIO patterns for concurrent execution

5. **News Monitoring App**
   - Study: `.browser-use-reference/examples/apps/news-use/news_monitor.py`
   - Compare: `app/cli/fetch_news.py`
   - Learn: Complete monitoring pipeline architecture

## 💡 Quick Tips

### Debug Mode
```python
# Watch the browser in action
profile = BrowserProfile(
    headless=False,  # Show browser window
    minimum_wait_page_load_time=3.0  # Slow down to watch
)
```

### Logging
```python
# Add detailed logging to examples
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing
```python
# Test with small targets first
task = "Collect 5 tweets (not 100) to test the pattern"
```

## 🚀 Next Steps

1. **Read** the official examples in `.browser-use-reference/examples/`
2. **Run** the getting_started examples to understand basics
3. **Study** the features examples to learn advanced techniques
4. **Adapt** patterns from use-cases for your specific needs
5. **Build** new social media sources using learned patterns

## 📖 Additional Resources

- **Browser-Use Docs**: https://docs.browser-use.com/
- **Playwright Docs** (underlying library): https://playwright.dev/python/
- **Project Learning Guide**: `docs/BROWSER_USE_GUIDE.md`
- **Cursor Rules**: `.cursorrules` for AI-assisted development

