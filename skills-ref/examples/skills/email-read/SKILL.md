---
name: email-read
description: Search and fetch emails from Gmail or Outlook. READ-only operation with no side effects.
composition:
  outputs:
    - email-list
---

# email-read

Search and fetch emails from Gmail or Outlook. This is a READ-only operation with no side effects, making it safe to execute without confirmation.

## When to Use

Use this skill when you need to:
- Search for specific emails by sender, subject, or date
- Find booking confirmations or receipts
- Look up email threads for context
- Check for recent communications from a person or company

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | - | Search query |
| service | string | No | gmail | `gmail`, `outlook`, or `both` |
| limit | integer | No | 20 | Maximum emails to return |
| json | flag | No | false | Output as JSON |

## Running

```bash
# Gmail (requires OAuth token file)
GMAIL_TOKEN_FILE=~/.gmail_token.pickle python scripts/run.py --query "from:example.com"

# Outlook (requires Graph API token)
MS_GRAPH_ACCESS_TOKEN=xxx python scripts/run.py --query "invoice" --service outlook

# Search both
GMAIL_TOKEN_FILE=~/.gmail_token.pickle MS_GRAPH_ACCESS_TOKEN=xxx \
  python scripts/run.py --query "urgent" --service both --json
```

## Authentication

**Gmail:** Requires OAuth token file (pickle format)
```bash
export GMAIL_TOKEN_FILE=/path/to/token.pickle
```
Generate using Google OAuth flow with scopes: `gmail.readonly`

**Outlook:** Requires Microsoft Graph API access token
```bash
export MS_GRAPH_ACCESS_TOKEN=eyJ0eXAi...
```
Generate using MSAL with scopes: `Mail.Read`

## Output Format

Returns an `email-list` containing:
- `emails[]` - Array of email objects
- `emails[].id` - Email ID for fetching full content
- `emails[].subject` - Email subject line
- `emails[].from` - Sender email address
- `emails[].date` - Date received (ISO format)
- `emails[].snippet` - Preview text (~100 chars)
- `emails[].source` - `gmail` or `outlook`

## Composition

This skill produces `email-list` which can be consumed by:
- **customer-intel** - Aggregate with Slack and CRM data
- **daily-synthesis** - Extract action items from emails
- **meeting-prep** - Prepare briefings for meetings
- **email-compose** - Context for smart replies

## Examples

### Search for booking confirmations
```
Query: service=gmail, query="from:airbnb OR from:booking.com", days_back=365
```

### Find emails from a customer
```
Query: service=outlook, query="from:@example-inc.com", days_back=30
```

## Safety

- **Operation:** READ
- **Side effects:** None
- **Confirmation required:** No
