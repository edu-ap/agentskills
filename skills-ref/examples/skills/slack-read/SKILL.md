---
name: slack-read
description: Search and fetch messages from Slack channels, threads, and mentions. READ-only operation.
composition:
  outputs:
    - message-list
---

# slack-read

Search and fetch messages from Slack channels, threads, and user mentions. This is a READ-only operation with no side effects.

## When to Use

Use this skill when you need to:
- Search for messages across channels
- Get recent activity in a specific channel
- Find mentions of a user or topic
- Check thread replies for context

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | No | - | Search query |
| channel | string | No | - | Channel name or ID |
| limit | integer | No | 20 | Maximum messages (max: 100) |
| json | flag | No | false | Output as JSON |

## Running

```bash
# Search messages
SLACK_BOT_TOKEN=xoxb-xxx python scripts/run.py --query "action item"

# Get channel history
SLACK_BOT_TOKEN=xoxb-xxx python scripts/run.py --channel general --limit 20

# JSON output
SLACK_BOT_TOKEN=xoxb-xxx python scripts/run.py --query "deadline" --json
```

## Authentication

Requires `SLACK_BOT_TOKEN` environment variable.

```bash
export SLACK_BOT_TOKEN=xoxb-xxxx-xxxx-xxxx
```

The bot token needs these scopes:
- `search:read` - For message search
- `channels:history` - For channel history
- `channels:read` - For channel lookup

## Output Format

Returns a `message-list` containing:
- `messages[]` - Array of message objects
- `messages[].ts` - Message timestamp (unique ID)
- `messages[].user` - User ID who posted
- `messages[].text` - Message content
- `messages[].channel` - Channel ID
- `messages[].thread_ts` - Thread parent timestamp (if in thread)
- `messages[].source` - Always `slack`

## Composition

This skill produces `message-list` which can be consumed by:
- **customer-intel** - Aggregate with email and CRM data
- **daily-synthesis** - Extract action items from Slack
- **meeting-prep** - Prepare briefings with recent discussions

## Examples

### Search for action items
```
Query: operation=search, query="action item OR todo OR by EOD", days_back=7
```

### Get customer channel history
```
Query: operation=channel, query="#customer-example-inc", limit=100
```

### Check thread for responses
```
Query: operation=thread, query="C0123456/1702000000.000000"
```

## Safety

- **Operation:** READ
- **Side effects:** None
- **Confirmation required:** No
