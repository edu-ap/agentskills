---
name: compose-validator
description: Validate that two skills can be composed together based on their input/output types. Use this before chaining skills to fail fast and avoid silent errors.
composition:
  inputs:
    - skill-reference
  outputs:
    - composition-result
---

# compose-validator

Validate that two skills can be composed together by checking their input/output type compatibility. Use this skill before executing a chain to catch type mismatches early rather than failing silently at runtime.

## When to Use

Use this skill when you need to:
- Verify a skill chain will work before executing it
- Debug why a composition is failing
- Validate a planned workflow before running expensive operations
- Prevent silent failures and hallucinated data from type mismatches

## Why This Matters

Without validation, an LLM might:
1. Chain `email-read` → `deal-analysis` (incompatible types)
2. Get no output or malformed data
3. Hallucinate results to "be helpful"
4. User gets incorrect information

With validation:
1. LLM calls `compose-validator` first
2. Gets clear error: "email-list is not compatible with crm-deals input"
3. LLM adjusts the plan before executing
4. No wasted API calls, no hallucination

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| source | string | Yes | - | Source skill name or path |
| target | string | Yes | - | Target skill name or path |
| json | flag | No | false | Output as JSON |

## Running

```bash
# Check if two skills can be composed
python scripts/run.py --source hubspot-read --target customer-intel

# JSON output for programmatic use
python scripts/run.py --source email-read --target deal-analysis --json
```

## Output Format

Returns a `composition-result` containing:
- `valid` - Boolean indicating if composition is valid
- `source` - Source skill name
- `target` - Target skill name
- `source_outputs` - Output types from source skill
- `target_inputs` - Input types expected by target skill
- `matched_types` - Types that match between source outputs and target inputs
- `reason` - Human-readable explanation

### Example: Valid Composition
```json
{
  "valid": true,
  "source": "hubspot-read",
  "target": "customer-intel",
  "source_outputs": ["crm-companies", "crm-contacts", "crm-deals"],
  "target_inputs": ["crm-data", "email-list", "message-list"],
  "matched_types": ["crm-companies", "crm-contacts", "crm-deals"],
  "reason": "Source outputs satisfy target inputs"
}
```

### Example: Invalid Composition
```json
{
  "valid": false,
  "source": "email-read",
  "target": "deal-analysis",
  "source_outputs": ["email-list"],
  "target_inputs": ["crm-deals"],
  "matched_types": [],
  "reason": "No matching types: email-read produces email-list but deal-analysis requires crm-deals"
}
```

## Composition

**Consumes:**
- `skill-reference` - Names or paths of skills to validate

**Produces:**
- `composition-result` - Validation result with compatibility details

## Authentication

**None required.** This skill only reads SKILL.md metadata files.

## Safety

- **Operation:** READ
- **Side effects:** None
- **Confirmation required:** No
