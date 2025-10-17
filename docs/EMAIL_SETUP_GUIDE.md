# 📧 Email Notification Setup Guide

## Overview

The Tesla Sentiment News Agent can send **AI-generated email notifications** with:
- 🤖 **LLM-powered executive summaries** (dynamic, context-aware)
- 📊 **Visual sentiment dashboard** (bullish/bearish/neutral indicators)
- 🔥 **Top stories highlights** (most impactful news)
- 🎯 **Action recommendations** (AI-suggested insights)
- 📈 **Market outlook analysis** (sentiment trends)

## 🚀 Quick Start

### Step 1: Configure Email Settings

Add these to your `.env` file:

```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com
RECIPIENT_EMAILS=recipient@example.com
```

### Step 2: Set Up Gmail App Password (Recommended)

**For Gmail users:**

1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Create a new app password for "Mail"
3. Copy the 16-character password
4. Use it as `SMTP_PASSWORD` in `.env`

**Why App Password?**
- ✅ More secure than your main password
- ✅ Works with 2FA enabled
- ✅ Can be revoked anytime
- ✅ Recommended by Google

### Step 3: Test Email Preview (No Sending)

```bash
python -m app.cli.send_email --days 1 --generate-only
```

This will:
- ✅ Generate LLM-powered email content
- ✅ Save preview to `email_previews/` folder
- ✅ Show what the email will look like
- ❌ NOT send any emails

### Step 4: Send Your First Email

```bash
python -m app.cli.send_email --days 1 --recipient your-email@example.com
```

## 📋 CLI Options

### `--days` (default: 1)
Time period to include in the email

```bash
# Daily briefing (last 24 hours)
python -m app.cli.send_email --days 1

# Weekly summary (last 7 days)
python -m app.cli.send_email --days 7
```

### `--recipient` (optional)
Recipient email address (overrides .env setting)

```bash
# Send to specific person
python -m app.cli.send_email --recipient boss@company.com

# Send to multiple (comma-separated)
python -m app.cli.send_email --recipient "team@company.com,ceo@company.com"
```

### `--generate-only` (default: False)
Generate email preview without sending

```bash
# Test before sending
python -m app.cli.send_email --generate-only
```

## 📧 Email Structure

### 1. Header
- **Tesla News Briefing** title
- Date and time period
- Visual branding

### 2. Sentiment Dashboard
```
┌─────────────┬─────────────┬─────────────┐
│ +0.45       │   3.2/5     │     25      │
│ Sentiment   │ Avg Impact  │  Articles   │
└─────────────┴─────────────┴─────────────┘
   🐂 10        🐻 8         ➖ 7
  Bullish     Bearish      Neutral
```

### 3. Executive Summary (LLM-Generated)
**Example:**
> "Today's Tesla news flow presents a mixed picture with moderate bullish sentiment. The standout development is Tesla's Q3 delivery numbers beating analyst expectations by 8%, signaling robust demand despite macroeconomic headwinds. However, concerns persist around margin compression and increased competition in the EV space. Overall, the positive operational metrics outweigh near-term challenges."

### 4. Market Outlook (LLM-Generated)
**Example:**
> "The overall market sentiment for Tesla remains cautiously optimistic. With strong delivery numbers and improving production efficiency, the company is well-positioned for Q4. However, investors should monitor regulatory developments in Europe and competitive pricing pressure. The bullish thesis remains intact, supported by the company's technology leadership and global expansion."

### 5. Key Takeaways
- ✅ Q3 deliveries exceeded expectations (+8% vs consensus)
- ⚠️ Margin pressure from price cuts in China
- 📈 Energy storage business showing strong growth
- 🚗 New affordable models driving volume
- ⚖️ Legal challenges around Musk's compensation package

### 6. Top Stories (With Summaries)
```
1. [BULLISH] Tesla Q3 Deliveries Beat Estimates
   Impact: ★★★★☆ | Sentiment: +0.75
   Summary: Tesla delivered 497,000 vehicles in Q3, 
            exceeding analyst expectations...
   
2. [BEARISH] Tesla's UK Sales Drop 35% Amid Brand Concerns
   Impact: ★★★★☆ | Sentiment: -0.60
   Summary: New data shows Tesla's UK market share...
```

### 7. Action Items (LLM-Generated)
- Monitor Q4 guidance during upcoming earnings call
- Watch for regulatory updates in EU markets
- Track competitive pricing moves in China
- Review energy storage segment growth trajectory

## 🎯 Use Cases

### 1. Daily Morning Briefing
```bash
# Send every morning at 8 AM (use cron)
0 8 * * * cd /path/to/project && python -m app.cli.send_email --days 1
```

### 2. Weekly Executive Summary
```bash
# Every Monday at 9 AM
0 9 * * 1 cd /path/to/project && python -m app.cli.send_email --days 7
```

### 3. On-Demand Updates
```bash
# Fetch latest news and immediately send email
python -m app.cli.fetch_news --days 1 --limit 20
python -m app.cli.send_email --days 1
```

### 4. Team Distribution
```bash
# Send to multiple team members
python -m app.cli.send_email --days 1 --recipient "team@company.com,executives@company.com"
```

## 🔧 SMTP Configuration

### Gmail
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

### Outlook/Office 365
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
```

### SendGrid
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

### Custom SMTP
```bash
SMTP_HOST=smtp.yourserver.com
SMTP_PORT=587
SMTP_USER=your-username
SMTP_PASSWORD=your-password
```

## 🤖 LLM-Generated Content Features

### Dynamic Context Awareness
The LLM analyzes:
- Overall sentiment distribution
- High-impact events
- Category patterns
- Temporal trends
- Article summaries and rationales

### Personalized Insights
Each email is uniquely generated based on:
- Actual news of the day
- Sentiment patterns
- Impact levels
- Market context
- Historical comparisons

### Professional Tone
- Clear, actionable language
- Executive-friendly format
- Fact-based analysis
- Strategic recommendations

## 📊 Email Analytics

### What's Included
- **Total articles** analyzed
- **Sentiment breakdown** (bullish/bearish/neutral)
- **Average scores** (sentiment & impact)
- **Category distribution**
- **Source credibility**

### LLM Analysis
- **Executive summary** (2-3 paragraphs)
- **Market outlook** (sentiment direction)
- **Key takeaways** (3-5 bullets)
- **Action items** (2-3 recommendations)

## 🔍 Preview vs Send

### Preview Mode (`--generate-only`)
```bash
python -m app.cli.send_email --generate-only
```

**What happens:**
- ✅ Fetches data from database
- ✅ Generates LLM content
- ✅ Saves preview to `email_previews/`
- ✅ Shows email subject and summary
- ❌ Does NOT send email

**Use when:**
- Testing email content
- Reviewing before sending
- Verifying LLM output
- Checking formatting

### Send Mode (Default)
```bash
python -m app.cli.send_email
```

**What happens:**
- ✅ Fetches data from database
- ✅ Generates LLM content
- ✅ Renders HTML email
- ✅ Sends via SMTP
- ✅ Confirms delivery

## 🐛 Troubleshooting

### Authentication Failed
```
Error: SMTP authentication failed
```

**Solution:**
- Verify `SMTP_USER` and `SMTP_PASSWORD` in `.env`
- For Gmail: Use App Password (not main password)
- Enable "Less secure app access" if needed
- Check SMTP host and port

### No Articles Found
```
⚠ No articles found in the past 1 day(s).
```

**Solution:**
- Run `python -m app.cli.fetch_news --days 1` first
- Check database has data
- Verify date range

### Email Not Received
**Check:**
- Spam folder
- SMTP configuration
- Recipient email correct
- Check logs for errors

### LLM Content Generation Failed
```
Error: Failed to generate email content
```

**Solution:**
- Verify `OPENAI_API_KEY` in `.env`
- Check API quota/billing
- Review logs for details
- Fallback content will be used

## 📝 Complete Workflow Example

```bash
# Morning routine (automated)

# 1. Fetch latest Tesla news (past 24 hours)
python -m app.cli.fetch_news --days 1 --limit 20

# 2. Preview email content
python -m app.cli.send_email --days 1 --generate-only

# 3. If preview looks good, send to team
python -m app.cli.send_email --days 1 --recipient "team@company.com"

# 4. Generate full HTML report for detailed review
python -m app.cli.generate_report --days 1 --format html
```

## 🔄 Automation

### Cron Job (Linux/Mac)
```bash
# Daily at 8 AM
0 8 * * * cd /path/to/tsla_sentiment_news_agent && /path/to/.venv/bin/python -m app.cli.fetch_news --days 1 --limit 20 && /path/to/.venv/bin/python -m app.cli.send_email --days 1
```

### Task Scheduler (Windows)
1. Open Task Scheduler
2. Create new task
3. Set trigger: Daily at 8:00 AM
4. Set action: Run `fetch_news` then `send_email`

### GitHub Actions
```yaml
name: Daily Tesla News Email
on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8 AM UTC
jobs:
  send-email:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Fetch news and send email
        run: |
          python -m app.cli.fetch_news --days 1
          python -m app.cli.send_email --days 1
```

## 💡 Tips

1. **Test First**: Always use `--generate-only` before sending
2. **Multiple Recipients**: Use comma-separated emails
3. **Frequency**: Daily for active trading, weekly for long-term
4. **Customization**: Edit templates to match your brand
5. **Backup**: Also generate HTML/Markdown reports for archive

## 🎨 Customization

### Email Template
Edit `templates/email_notification.html` to customize:
- Colors and styling
- Logo and branding
- Layout and sections
- Footer information

### LLM Prompt
Edit `app/services/email_generator.py` to adjust:
- Tone and style
- Content structure
- Analysis depth
- Recommendation format

## 🔐 Security

- ✅ Use app passwords (not main passwords)
- ✅ Store credentials in `.env` (never in code)
- ✅ Add `.env` to `.gitignore`
- ✅ Use TLS/SSL for SMTP (port 587)
- ✅ Rotate passwords regularly

## 📚 Next Steps

1. ✅ Configure `.env` with email settings
2. ✅ Set up Gmail app password
3. ✅ Test with `--generate-only`
4. ✅ Send test email to yourself
5. ✅ Add team members to `RECIPIENT_EMAILS`
6. ✅ Schedule automated daily emails

---

**Files:**
- LLM Generator: `app/services/email_generator.py`
- Email Service: `app/services/email_service.py`
- HTML Template: `templates/email_notification.html`
- CLI Command: `app/cli/send_email.py`
- Configuration: `env.example`

