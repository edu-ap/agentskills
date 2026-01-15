---
name: hubspot-deals
description: Fetch deals and pipeline data from HubSpot CRM.
composition:
  outputs:
    - crm-deals
---

# hubspot-deals

Fetch deals and pipeline data from HubSpot CRM. Supports filtering by stage, close date, and amount. This is a READ-only operation.

## When to Use

Use this skill when you need to:
- Review sales pipeline status
- Find deals closing this quarter
- Identify stalled or at-risk deals
- Generate pipeline reports

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| stage | string | No | - | Filter by deal stage |
| limit | integer | No | 10 | Maximum results (max: 100) |
| json | flag | No | false | Output as JSON |

## Running

```bash
# Basic usage
HUBSPOT_ACCESS_TOKEN=xxx python scripts/run.py

# Filter by stage
HUBSPOT_ACCESS_TOKEN=xxx python scripts/run.py --stage closedwon

# JSON output
HUBSPOT_ACCESS_TOKEN=xxx python scripts/run.py --json --limit 5
```

## Authentication

Requires `HUBSPOT_ACCESS_TOKEN` environment variable.

```bash
export HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx
```

## Output Format

Returns `crm-deals` containing:
- `deals[]` - Array of deal objects
- `deals[].id` - HubSpot deal ID
- `deals[].name` - Deal name
- `deals[].stage` - Pipeline stage (e.g., "closedwon", "negotiation")
- `deals[].amount` - Deal value
- `deals[].close_date` - Expected or actual close date
- `deals[].create_date` - When deal was created
- `deals[].company_id` - Associated company ID
- `deals[].owner_id` - Deal owner HubSpot user ID

## Composition

**Consumes:** None (atomic skill)

**Produces:**
- `crm-deals` - Consumed by deal-analysis, deal-loss-analysis, weekly-review

## Workflow

```
hubspot-deals
     │
     ├──▶ deal-analysis (risk assessment)
     │
     ├──▶ deal-loss-analysis (pattern analysis)
     │
     └──▶ weekly-review (pipeline status)
```

## Examples

### Get pipeline for this quarter
```
Query: close_before="2025-03-31", close_after="2025-01-01"
```

### Find high-value deals
```
Query: min_amount=50000, stage="negotiation"
```

### Get deals by company
```
Query: company="Acme Corp"
```

## Safety

- **Operation:** READ
- **Side effects:** None
- **Confirmation required:** No
