# AI Assistant Setup for Browser-Use Development

## Overview

This workspace is now **optimized for AI-assisted browser-use development**. When you use Cursor AI to write code, it will automatically reference comprehensive browser-use patterns, templates, and best practices.

## What's Been Integrated

### 1. `.cursorrules` - AI Development Guidelines
**Purpose**: Tells Cursor AI how to write browser-use code for this project

**Contains**:
- ✅ Complete agent creation pattern
- ✅ Task prompt structure (STEP 1, STEP 2 format)
- ✅ Pydantic schema patterns
- ✅ Session caching implementation
- ✅ Result parsing patterns
- ✅ Timestamp parsing helpers
- ✅ Project-specific guidelines
- ✅ Anti-patterns to avoid
- ✅ Code generation checklist

**How It Helps**:
When you ask Cursor to add a new feature, it will:
- Follow the exact patterns used in `twitter_source.py`
- Include proper session management
- Use structured task prompts
- Generate validated Pydantic models
- Handle errors appropriately

### 2. `BROWSER_USE_PATTERNS.md` - Code Templates
**Purpose**: Copy-paste-ready templates for common browser-use tasks

**Contains**:
- ✅ 300+ line complete adapter template
- ✅ Task prompt patterns for:
  - Authenticated social media
  - Guest-accessible sites
  - E-commerce/product sites
- ✅ Data model templates
- ✅ Error handling patterns
- ✅ CLI integration code

**How It Helps**:
Cursor can reference this file to generate complete, working code without you having to explain the structure.

### 3. `.browser-use-reference/examples/` - Official Examples
**Purpose**: Access to 50+ official browser-use examples

**Contains**:
- Getting started examples
- Browser features (cookies, scrolling, parallel execution)
- Custom functions (2FA, parallel agents)
- Use cases (influencer profiles, shopping automation)
- Model integrations (OpenAI, Gemini, Claude, etc.)

**How It Helps**:
Cursor can reference official best practices when implementing complex features.

### 4. `examples/` - Learning Resources
**Purpose**: Curated examples for both AI and human developers

**Contains**:
- `README.md` - Index of all examples
- `QUICK_REFERENCE.md` - Cheat sheet for browser-use
- `01_basic_search.py` - Simple search example
- `02_session_caching.py` - Session management demo
- `03_structured_extraction.py` - Pydantic extraction demo
- `04_add_new_platform.py` - Complete template for new platforms

## How to Use This Setup

### Scenario 1: Adding a New Social Media Platform

**You**: "Add Instagram sentiment collection similar to Twitter"

**Cursor AI will**:
1. Read `.cursorrules` for project patterns
2. Reference `BROWSER_USE_PATTERNS.md` complete adapter template
3. Study `app/adapters/twitter_source.py` for comparison
4. Generate:
   - `app/adapters/instagram_source.py` with proper structure
   - Pydantic models (ExtractedInstagramPost, InstagramPostBatch)
   - Session caching (_load_session_cache, _save_session_cache)
   - Structured task prompt with STEP 1, STEP 2, etc.
   - Result parsing with validation
   - Error handling with custom exceptions

### Scenario 2: Improving Existing Code

**You**: "Improve the Twitter scraping to handle rate limiting better"

**Cursor AI will**:
1. Reference anti-patterns in `.cursorrules`
2. Check `.browser-use-reference/examples/` for retry patterns
3. Suggest improvements following project conventions

### Scenario 3: Fixing Bugs

**You**: "Fix the session cache expiration issue"

**Cursor AI will**:
1. Reference session caching pattern in `.cursorrules`
2. Compare with `twitter_source.py` implementation
3. Suggest fix that matches existing code style

### Scenario 4: Adding Features

**You**: "Add ability to filter tweets by verified users only"

**Cursor AI will**:
1. Reference task prompt patterns in `BROWSER_USE_PATTERNS.md`
2. Update the task prompt with new filtering instructions
3. Add new Pydantic field for verified status
4. Update parsing logic

## Files Cursor References Automatically

| File | Purpose | When Used |
|------|---------|-----------|
| `.cursorrules` | Project-wide rules | Always |
| `BROWSER_USE_PATTERNS.md` | Code templates | When generating new code |
| `.browser-use-reference/examples/` | Official examples | For complex features |
| `app/adapters/twitter_source.py` | Reference implementation | When adding similar features |
| `app/adapters/reddit_source.py` | Simpler reference | For guest-mode scraping |

## Testing the Setup

Try asking Cursor:

```
Add YouTube comment sentiment collection:
- Collect comments from Tesla-related videos
- Include author, text, likes, timestamp
- Save to database
- Add CLI command
```

Cursor should generate:
- ✅ Complete adapter in `app/adapters/youtube_source.py`
- ✅ Proper Pydantic models
- ✅ Structured task prompt
- ✅ Session management
- ✅ CLI command in `app/cli/youtube_sentiment.py`
- ✅ Following exact patterns from existing code

## Benefits

### For You (Developer)
- 🚀 **Faster development**: AI generates complete, working code
- 📝 **Consistent patterns**: All code follows same structure
- 🔒 **Fewer bugs**: AI includes error handling, validation
- 📚 **Learning**: Generated code shows best practices

### For the AI (Cursor)
- 🎯 **Clear guidelines**: Knows exactly how to structure code
- 📖 **Rich context**: 50+ examples to reference
- 🔧 **Templates**: Can copy-paste and adapt patterns
- ✅ **Validation**: Checklist ensures nothing is missed

## Maintenance

### Keeping Resources Updated

When browser-use updates:
```bash
cd .browser-use-reference
git pull origin main
```

When you discover new patterns:
1. Add to `.cursorrules` if it's a rule/guideline
2. Add to `BROWSER_USE_PATTERNS.md` if it's a code template
3. Add to `examples/` if it's a learning example

### Customization

You can customize `.cursorrules` with:
- Project-specific requirements
- Team coding standards
- Additional anti-patterns you discover
- Performance optimizations specific to your use case

## Resources

- **Browser-Use Docs**: https://docs.browser-use.com/
- **Browser-Use GitHub**: https://github.com/browser-use/browser-use
- **Browser-Use Examples**: https://github.com/browser-use/browser-use/tree/main/examples
- **Local Examples**: `.browser-use-reference/examples/`

## Support

If Cursor generates code that doesn't match patterns:
1. Check if `.cursorrules` is in the workspace root
2. Ensure `BROWSER_USE_PATTERNS.md` exists
3. Try being more specific in your prompt
4. Reference specific files: "Use the pattern from twitter_source.py"

## Example Prompts That Work Well

✅ **Good prompts**:
```
"Add LinkedIn post collection following the twitter_source.py pattern"
"Improve session caching to handle token refresh"
"Add parallel collection for Twitter and Reddit simultaneously"
"Create a CLI command for YouTube comments like twitter_sentiment.py"
```

❌ **Less effective prompts**:
```
"Make it better" (too vague)
"Add stuff" (no specifics)
"Fix everything" (too broad)
```

## Next Steps

1. ✅ Resources are integrated and ready to use
2. ✅ Try asking Cursor to add a new platform
3. ✅ Review generated code to see the patterns in action
4. ✅ Customize `.cursorrules` with your preferences
5. ✅ Share improvements with the team

---

**You're all set!** Cursor AI now has comprehensive browser-use knowledge specific to your project. Happy coding! 🚀

