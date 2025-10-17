# Browser-Use Quick Reference Card

## 🚀 Basic Agent Setup

```python
from browser_use import Agent, ChatOpenAI
from browser_use.browser.profile import BrowserProfile

# 1. Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",  # or "gpt-4", "gpt-4o", etc.
    api_key="your-api-key",
    temperature=0.0  # 0.0 = deterministic, 1.0 = creative
)

# 2. Configure browser (optional but recommended)
profile = BrowserProfile(
    headless=False,  # True = invisible, False = visible
    disable_security=True,  # Bypass CORS/CSP for scraping
    minimum_wait_page_load_time=2.0,  # Seconds to wait after navigation
    wait_between_actions=1.0,  # Seconds between each action
)

# 3. Create agent
agent = Agent(
    task="Your task description here",
    llm=llm,
    browser_profile=profile,
    max_actions_per_step=10,  # Actions per reasoning step
)

# 4. Run agent
result = await agent.run(max_steps=15)  # Max reasoning steps
```

## 📝 Task Prompt Best Practices

### ✅ Good Task Prompt
```python
task = """
STEP 1: Navigate directly to https://example.com/search?q=tesla
STEP 2: Verify you're on the correct page (check URL contains 'example.com')
STEP 3: Scroll down 5 times, waiting 3 seconds between scrolls
STEP 4: Extract the top 10 results with title, URL, and date
STOP when you have 10 results or after 5 scrolls (whichever comes first)
"""
```

### ❌ Bad Task Prompt
```python
task = "Find some Tesla stuff online"  # Too vague, no steps, no constraints
```

### 📋 Template
```python
task = f"""
You are a [role]. Your job is [objective].

CRITICAL RULES:
- Stay on [specific domain] ONLY
- Do NOT use search engines
- Stop after [condition]

STEP 1: [specific action with URL]
STEP 2: [validation step]
STEP 3: [data collection with specifics]
STEP 4: [extraction with field names]

WHAT TO SKIP:
- [unwanted content type 1]
- [unwanted content type 2]

FINAL OUTPUT:
[output format specification]
"""
```

## 🏗️ Structured Output (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import List

# Define your data structure
class Article(BaseModel):
    title: str
    url: str
    author: str | None = None  # Optional field
    tags: List[str] = Field(default_factory=list)  # Default to empty list

class ArticleBatch(BaseModel):
    articles: List[Article]

# Use it in agent
agent = Agent(
    task="Extract 5 articles from example.com",
    llm=llm,
    output_model_schema=ArticleBatch,  # ← Enforces structure!
)

result = await agent.run()

# Parse result
if hasattr(result, 'history') and result.history.structured_output:
    data: ArticleBatch = result.history.structured_output
    print(f"Got {len(data.articles)} articles")
```

## 💾 Session Caching Pattern

```python
import json
from pathlib import Path
from datetime import datetime, timedelta

def load_session(cache_file: Path) -> dict | None:
    """Load cached session if not expired."""
    if not cache_file.exists():
        return None
    
    with open(cache_file) as f:
        data = json.load(f)
    
    # Check expiration (24 hours)
    cache_time = datetime.fromisoformat(data['timestamp'])
    if datetime.now() - cache_time > timedelta(hours=24):
        cache_file.unlink()  # Delete expired cache
        return None
    
    return data['storage_state']

def save_session(cache_file: Path, storage_state: dict):
    """Save session state to cache."""
    data = {
        'timestamp': datetime.now().isoformat(),
        'storage_state': storage_state
    }
    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)

# Usage
storage_state = load_session(Path("cache/session.json"))

profile = BrowserProfile(
    storage_state=storage_state,  # ← Loads cookies, localStorage
    # ... other config
)

agent = Agent(task=task, llm=llm, browser_profile=profile)
result = await agent.run()

# After successful run
if profile.browser and profile.browser.contexts:
    new_state = await profile.browser.contexts[0].storage_state()
    save_session(Path("cache/session.json"), new_state)
```

## 🔒 Stealth Configuration (Anti-Detection)

```python
profile = BrowserProfile(
    headless=False,  # Headless mode easier to detect
    disable_security=True,  # Bypass CORS, CSP
    deterministic_rendering=False,  # More human-like
    executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    minimum_wait_page_load_time=2.0,  # Wait for JS to execute
    wait_between_actions=1.0,  # Slower = more human-like
    extra_chromium_args=[
        '--disable-blink-features=AutomationControlled',  # Hide automation flag
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-web-security',
        '--disable-features=IsolateOrigins,site-per-process',
    ],
    storage_state=storage_state,  # Reuse authenticated sessions
)
```

## 🎯 Common Patterns

### Pattern 1: Conditional Login
```python
has_cache = load_session(cache_file) is not None

if has_cache:
    task = "Check if logged in, then proceed to data collection"
else:
    task = "Login first, then collect data"

max_steps = 15 if has_cache else 25  # More steps for login
use_vision = not has_cache  # Vision helps with login forms
```

### Pattern 2: Scrolling Collection
```python
task = f"""
STEP 3: Scroll down {max_scrolls} times
- Wait 4 seconds between each scroll for content to load
- Stop early if you've collected {target_count} items
"""
```

### Pattern 3: Deduplication
```python
seen_ids: set[str] = set()

for item in raw_data:
    if item.id in seen_ids:
        continue  # Skip duplicate
    seen_ids.add(item.id)
    parsed_items.append(item)
```

## 🐛 Debugging Tips

```python
# 1. Watch the browser
profile = BrowserProfile(headless=False)  # Show browser window

# 2. Slow down actions
profile = BrowserProfile(
    minimum_wait_page_load_time=5.0,  # Longer waits
    wait_between_actions=2.0
)

# 3. Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# 4. Reduce scope for testing
task = "Collect only 3 items to test the pattern quickly"
max_steps = 5  # Fewer steps to debug faster

# 5. Use vision mode
agent = Agent(task=task, llm=llm, use_vision=True)  # Better page understanding
```

## ⚡ Performance Tips

```python
# 1. Reduce steps for cached sessions
max_steps = 10 if has_cache else 20

# 2. Use faster LLM for simple tasks
llm = ChatOpenAI(model="gpt-4o-mini")  # Faster & cheaper than gpt-4

# 3. Batch operations
task = """
Collect 50 items in one session
Don't create new browser instances for each item
"""

# 4. Disable images for speed
profile.args = ['--disable-images']

# 5. Use fixed scroll counts (not infinite)
task = "Scroll exactly 5 times (not 'until no more results')"
```

## 📊 Cost Optimization

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| gpt-4o-mini | ⚡⚡⚡ | 💰 | Simple scraping, testing |
| gpt-4o | ⚡⚡ | 💰💰 | Complex pages, reliability |
| gpt-4 | ⚡ | 💰💰💰 | Maximum accuracy |

```python
# Use mini for most tasks
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

# Upgrade only when needed
if complex_page:
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
```

## 🔗 Helpful Links

- **Official Examples**: [browser-use/examples](https://github.com/browser-use/browser-use/tree/main/examples)
- **Docs**: https://docs.browser-use.com/
- **This Project's Examples**: `/examples/` directory
- **Full Learning Guide**: `/docs/BROWSER_USE_GUIDE.md`
- **Project Best Practices**: `/.cursorrules`

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| "Browser failed to launch" | Check Chrome path in `executable_path` |
| "Bot detection / CAPTCHA" | Add stealth args, slow down actions, use sessions |
| "No structured output" | Check Pydantic model, print raw result to debug |
| "Timeout" | Increase `max_steps`, check internet connection |
| "Session expired" | Implement cache expiration (24-48 hours) |
| "Empty/incomplete data" | Use vision mode, increase wait times, check selectors |

## 💡 Pro Tips

1. **Start small**: Test with 3-5 items before scaling to 100
2. **Use vision for login**: `use_vision=True` helps with complex forms
3. **Save sessions**: Dramatically speeds up subsequent runs
4. **Give direct URLs**: Don't make the agent search for pages
5. **Validate URLs in output**: Check all extracted URLs start with "http"
6. **Handle timestamps**: Convert relative times ("2h ago") to absolute dates
7. **Set clear stop conditions**: "After 5 scrolls OR 20 items"
8. **Test without headless first**: Watch what the agent does before going headless

