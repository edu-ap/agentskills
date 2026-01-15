---
name: github-repos
description: Fetch repositories from GitHub for a user or the authenticated account.
composition:
  outputs:
    - repo-list
---

# github-repos

Fetch repositories from GitHub. Can list repos for the authenticated user or any public user.

## When to Use

Use this skill to:
- List your own repositories
- Explore a user's public repos
- Find repos by language or activity

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | integer | No | 10 | Maximum repos to return (max: 100) |
| user | string | No | authenticated | GitHub username to list repos for |
| json | flag | No | false | Output as JSON |

## Running

```bash
# Your repos (requires GITHUB_TOKEN)
GITHUB_TOKEN=xxx python scripts/run.py

# Specific user's repos
GITHUB_TOKEN=xxx python scripts/run.py --user anthropics

# JSON output
GITHUB_TOKEN=xxx python scripts/run.py --json --limit 5
```

## Output Format

Returns `repo-list` containing:
- `results[]` - Array of repository objects
- `results[].full_name` - Owner/repo format
- `results[].description` - Repository description
- `results[].stargazers_count` - Star count
- `results[].language` - Primary language
- `results[].html_url` - Web URL

## Authentication

Requires `GITHUB_TOKEN` environment variable with `repo` scope.

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

## Safety

- **Operation:** READ
- **Side effects:** None
- **Confirmation required:** No
