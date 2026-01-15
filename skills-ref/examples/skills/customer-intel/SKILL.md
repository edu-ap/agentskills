---
name: customer-intel
description: Aggregate customer intelligence from HubSpot, Slack, and email into a comprehensive brief.
composition:
  inputs:
    - email-list
    - message-list
    - crm-companies
    - crm-contacts
    - crm-deals
  outputs:
    - intel-brief
---

# customer-intel

Aggregate customer intelligence from multiple sources (HubSpot CRM, Slack channels, email) into a comprehensive customer brief. Used for meeting preparation, status updates, and identifying urgent items.

## When to Use

Use this skill when you need to:
- Prepare for a customer meeting
- Get a quick status update on a customer
- Investigate a customer escalation
- Review activity before a status call

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| customer | string | Yes | - | Customer name or identifier |
| days_back | integer | No | 30 | How far back to search |
| include_meetings | boolean | No | true | Include meeting transcripts |

## Input Types

This skill consumes data from atomic skills:
- **email-list** - From `email-read` (Outlook/Gmail)
- **message-list** - From `slack-read` (customer channels)
- **crm-data** - From `hubspot-read` (deals, contacts)

## Output Format

Returns an `intel-brief` containing:
- `brief.customer` - Customer name
- `brief.generated_at` - Timestamp
- `brief.period_days` - Period covered
- `brief.timeline[]` - Chronological activity events
- `brief.alerts[]` - Urgent items needing attention
- `brief.contacts[]` - Key contacts with roles
- `sources.hubspot_count` - Number of CRM records
- `sources.slack_count` - Number of Slack messages
- `sources.email_count` - Number of emails

## Composition

**Consumes from:**
- `email-read` → `email-list`
- `slack-read` → `message-list`
- `hubspot-read` → `crm-data`

**Produces:**
- `intel-brief` - Comprehensive customer summary

## Workflow

```
┌─────────────────────────────────────────────┐
│              PARALLEL FETCH                  │
├──────────────┬──────────────┬───────────────┤
│ hubspot-read │  slack-read  │  email-read   │
│  (crm-data)  │ (msg-list)   │ (email-list)  │
└──────┬───────┴──────┬───────┴───────┬───────┘
       │              │               │
       └──────────────┴───────────────┘
                      │
               ┌──────▼──────┐
               │  AGGREGATE   │
               │  & ANALYSE   │
               └──────┬──────┘
                      │
               ┌──────▼──────┐
               │ intel-brief  │
               └─────────────┘
```

## Examples

### Quick status check
```
"What's happening with Example Inc?"
→ Returns brief with recent activity and alerts
```

### Meeting preparation
```
"Prepare for customer standup tomorrow"
→ Returns detailed brief with open items and recent discussions
```

## Safety

- **Operation:** READ
- **Side effects:** None
- **Confirmation required:** No
