#!/usr/bin/env python3
"""
GitHub Repos Skill - Fetch repositories from GitHub.

Requires: GITHUB_TOKEN environment variable

Usage:
    GITHUB_TOKEN=xxx python run.py
    GITHUB_TOKEN=xxx python run.py --limit 5
    GITHUB_TOKEN=xxx python run.py --user "anthropics"
    GITHUB_TOKEN=xxx python run.py --json
"""

import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


def get_repos(token: str, limit: int = 10, user: str = None) -> dict:
    """Fetch repositories from GitHub API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    if user:
        url = f"https://api.github.com/users/{user}/repos"
    else:
        url = "https://api.github.com/user/repos"

    resp = requests.get(
        url,
        headers=headers,
        params={"per_page": min(limit, 100), "sort": "updated"},
        timeout=30,
    )

    if resp.status_code == 401:
        return {"error": "Invalid or expired GITHUB_TOKEN"}
    if resp.status_code == 404:
        return {"error": f"User '{user}' not found"}

    resp.raise_for_status()
    return {"results": resp.json()}


def main():
    parser = argparse.ArgumentParser(description="Fetch repositories from GitHub")
    parser.add_argument("--limit", "-l", type=int, default=10,
                        help="Maximum repos to return (default: 10, max: 100)")
    parser.add_argument("--user", "-u",
                        help="GitHub username (default: authenticated user)")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    # Check for auth token
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        print("Usage: GITHUB_TOKEN=xxx python run.py", file=sys.stderr)
        sys.exit(1)

    try:
        result = get_repos(token, args.limit, args.user)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            repos = result.get("results", [])
            print(f"Found {len(repos)} repositories:\n")
            for repo in repos:
                print(f"  - {repo.get('full_name', 'Unknown')}")
                print(f"    Description: {repo.get('description', 'N/A') or 'N/A'}")
                print(f"    Stars: {repo.get('stargazers_count', 0)}")
                print(f"    Language: {repo.get('language', 'N/A') or 'N/A'}")
                print(f"    URL: {repo.get('html_url', 'N/A')}")
                print()

    except requests.RequestException as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
