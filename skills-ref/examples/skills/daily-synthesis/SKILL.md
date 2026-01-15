---
name: daily-synthesis
description: Analyse Slack and email to extract action items, deadlines, and follow-ups.
composition:
  inputs:
    - email-list
    - message-list
  outputs:
    - action-items
---

# daily-synthesis

Analyse Slack messages and emails to extract action items, deadlines, commitments, and required follow-ups. Produces a prioritised list of tasks.

## When to Use

Use this skill when you need to:
- Start the day with a clear task list
- Catch up after being away
- Find commitments you may have missed
- Review what needs follow-up

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| days_back | integer | No | 1 | How far back to analyse |
| include_sent | boolean | No | true | Include your sent messages |
| priority_filter | string | No | - | Filter by priority level |

## Input Types

This skill consumes data from atomic skills:
- **email-list** - From `email-read` (Gmail and Outlook)
- **message-list** - From `slack-read` (all relevant channels)

## Output Format

Returns `action-items` containing:
- `items[]` - Array of action item objects
- `items[].description` - What needs to be done
- `items[].source` - Where it came from (slack/email)
- `items[].source_url` - Link to original message
- `items[].owner` - Who is responsible (you or someone else)
- `items[].deadline` - When it's due (if mentioned)
- `items[].priority` - High/Medium/Low
- `items[].context` - Surrounding conversation
- `summary.total` - Total items found
- `summary.by_priority` - Count by priority level
- `summary.by_source` - Count by source

## Composition

**Consumes from:**
- `email-read` → `email-list`
- `slack-read` → `message-list`

**Produces:**
- `action-items` - Prioritised task list

**Can feed into:**
- `morning-briefing` - Include action items in daily brief

## Detection Patterns

The skill looks for:
- Direct requests: "can you", "please", "could you"
- Deadlines: "by EOD", "by Friday", "before the meeting"
- Commitments: "I'll", "I will", "let me"
- Questions awaiting response: "?" from others
- Follow-up indicators: "following up", "checking in"

## Examples

### Morning review
```
"What action items do I have from yesterday?"
→ Returns prioritised list from last 24h
```

### Weekly catch-up
```
"What did I miss while I was on holiday?"
Query: days_back=5
→ Returns action items from last 5 days
```

## Safety

- **Operation:** READ
- **Side effects:** None
- **Confirmation required:** No
