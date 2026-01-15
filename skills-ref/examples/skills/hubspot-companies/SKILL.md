---
name: hubspot-companies
description: Fetch companies from HubSpot CRM with filtering and search.
composition:
  outputs:
    - crm-companies
---

# hubspot-companies

Fetch companies from HubSpot CRM. Supports filtering by industry, lifecycle stage, and domain search. This is a READ-only operation.

## When to Use

Use this skill when you need to:
- Search for companies by domain or name
- Filter companies by industry or stage
- Get company details for a specific customer
- Build lists for outreach campaigns

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| domain | string | No | - | Search by company domain |
| limit | integer | No | 10 | Maximum results (max: 100) |
| json | flag | No | false | Output as JSON |

## Running

```bash
# Basic usage
HUBSPOT_ACCESS_TOKEN=xxx python scripts/run.py

# Search by domain
HUBSPOT_ACCESS_TOKEN=xxx python scripts/run.py --domain acme-corp.com

# JSON output
HUBSPOT_ACCESS_TOKEN=xxx python scripts/run.py --json --limit 5
```

## Authentication

Requires `HUBSPOT_ACCESS_TOKEN` environment variable.

```bash
export HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx
```

## Output Format

Returns `crm-companies` containing:
- `companies[]` - Array of company objects
- `companies[].id` - HubSpot company ID
- `companies[].name` - Company name
- `companies[].domain` - Company domain
- `companies[].industry` - Industry classification
- `companies[].lifecycle_stage` - lead, customer, opportunity, etc.
- `companies[].city` - Company city
- `companies[].country` - Company country
- `companies[].created_date` - When added to HubSpot
- `companies[].last_modified` - Last update timestamp

## Composition

**Consumes:** None (atomic skill)

**Produces:**
- `crm-companies` - Consumed by customer-intel, competitor-intel, company-research

## Examples

### Search by domain
```
Query: domain="acme-corp.com"
```

### Filter by stage
```
Query: stage="customer", limit=50
```

### Filter by industry
```
Query: industry="Legal Services"
```

## Safety

- **Operation:** READ
- **Side effects:** None
- **Confirmation required:** No
