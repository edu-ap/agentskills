---
name: hubspot-read
description: Fetch combined CRM data from HubSpot including companies, contacts, deals, and activities.
composition:
  outputs:
    - crm-companies
    - crm-contacts
    - crm-deals
    - crm-activities
---

# hubspot-read

Fetch comprehensive CRM data from HubSpot in a single operation. Returns companies, contacts, deals, and engagement activities. This is a READ-only operation with no side effects.

## When to Use

Use this skill when you need to:
- Get a complete view of a customer from HubSpot
- Prepare for customer meetings with CRM context
- Aggregate CRM data for intelligence reports
- Check contact and company information

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| company | string | No | - | Filter by company domain |
| limit | integer | No | 10 | Maximum records per type (max: 100) |
| json | flag | No | false | Output as JSON |

## Running

```bash
# Basic usage - fetch all CRM data
HUBSPOT_ACCESS_TOKEN=xxx python scripts/run.py

# Filter by company domain
HUBSPOT_ACCESS_TOKEN=xxx python scripts/run.py --company acme-corp.com

# JSON output
HUBSPOT_ACCESS_TOKEN=xxx python scripts/run.py --json --limit 5
```

## Authentication

Requires `HUBSPOT_ACCESS_TOKEN` environment variable.

```bash
export HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx
```

## Output Format

Returns multiple output types:

### crm-companies
- `companies[]` - Array of company objects
- `companies[].id` - HubSpot company ID
- `companies[].name` - Company name
- `companies[].domain` - Company domain
- `companies[].industry` - Industry classification
- `companies[].lifecycle_stage` - CRM lifecycle stage

### crm-contacts
- `contacts[]` - Array of contact objects
- `contacts[].id` - HubSpot contact ID
- `contacts[].name` - Full name
- `contacts[].email` - Email address
- `contacts[].title` - Job title
- `contacts[].phone` - Phone number

### crm-deals
- `deals[]` - Array of deal objects
- `deals[].id` - HubSpot deal ID
- `deals[].name` - Deal name
- `deals[].stage` - Pipeline stage
- `deals[].amount` - Deal value
- `deals[].close_date` - Expected close date

### crm-activities
- `activities[]` - Array of activity objects
- `activities[].type` - Activity type (email, call, meeting, note)
- `activities[].timestamp` - When it occurred
- `activities[].subject` - Subject or title
- `activities[].direction` - Inbound/outbound (for emails)

## Composition

**Consumes:** None (atomic skill)

**Produces:**
- `crm-companies` - Company data for customer-intel, competitor-intel
- `crm-contacts` - Contact data for email-compose, meeting-prep
- `crm-deals` - Deal data for deal-analysis, deal-loss-analysis
- `crm-activities` - Activity data for customer-intel, deal-analysis

## Examples

### Get customer data by domain
```
Query: company="acme-corp.com"
→ Returns company, contacts, deals, and recent activities
```

### Quick status check
```
Query: company="Example Inc", days_back=7
→ Returns last 7 days of activities
```

## Safety

- **Operation:** READ
- **Side effects:** None
- **Confirmation required:** No
