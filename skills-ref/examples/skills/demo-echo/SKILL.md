---
name: demo-echo
description: Demo skill that echoes input. Works without any authentication.
composition:
  outputs:
    - demo-output
---

# demo-echo

A simple demonstration skill that echoes back input. Use this to verify the skill runtime is working correctly.

## When to Use

Use this skill to:
- Test that the skill runtime is working
- Verify skill discovery and execution
- Debug skill composition chains

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| message | string | No | "Hello from Agent Skills!" | Message to echo back |
| json | flag | No | false | Output as JSON |

## Running

```bash
# Basic usage
python scripts/run.py

# With custom message
python scripts/run.py --message "Testing skills"

# JSON output
python scripts/run.py --json
```

## Output Format

Returns `demo-output` containing:
- `message` - The echoed message
- `skill` - Skill name (demo-echo)
- `note` - Description note

## Authentication

**None required.** This skill works without any API keys or tokens.

## Safety

- **Operation:** READ
- **Side effects:** None
- **Confirmation required:** No
