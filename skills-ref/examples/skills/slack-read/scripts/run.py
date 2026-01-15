#!/usr/bin/env python3
"""
Slack Read Skill - Search and fetch messages from Slack.

Requires: SLACK_BOT_TOKEN environment variable

Usage:
    SLACK_BOT_TOKEN=xoxb-xxx python run.py --query "action item"
    SLACK_BOT_TOKEN=xoxb-xxx python run.py --channel general --limit 20
    SLACK_BOT_TOKEN=xoxb-xxx python run.py --json
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


def search_messages(token: str, query: str, limit: int = 20) -> dict:
    """Search Slack messages."""
    resp = requests.post(
        "https://slack.com/api/search.messages",
        headers={"Authorization": f"Bearer {token}"},
        data={"query": query, "count": min(limit, 100)},
        timeout=30,
    )

    data = resp.json()
    if not data.get("ok"):
        return {"error": data.get("error", "Unknown Slack API error")}

    return data


def get_channel_history(token: str, channel: str, limit: int = 20) -> dict:
    """Get recent messages from a channel."""
    # First, find the channel ID if a name was given
    if not channel.startswith("C"):
        # Look up channel by name
        resp = requests.get(
            "https://slack.com/api/conversations.list",
            headers={"Authorization": f"Bearer {token}"},
            params={"types": "public_channel,private_channel", "limit": 200},
            timeout=30,
        )
        data = resp.json()
        if not data.get("ok"):
            return {"error": data.get("error", "Failed to list channels")}

        channel_name = channel.lstrip("#")
        for ch in data.get("channels", []):
            if ch.get("name") == channel_name:
                channel = ch.get("id")
                break
        else:
            return {"error": f"Channel '{channel_name}' not found"}

    # Get history
    resp = requests.get(
        "https://slack.com/api/conversations.history",
        headers={"Authorization": f"Bearer {token}"},
        params={"channel": channel, "limit": min(limit, 100)},
        timeout=30,
    )

    data = resp.json()
    if not data.get("ok"):
        return {"error": data.get("error", "Failed to get channel history")}

    return {"channel": channel, "messages": data.get("messages", [])}


def main():
    parser = argparse.ArgumentParser(description="Search and fetch Slack messages")
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--channel", "-c", help="Channel name or ID")
    parser.add_argument("--limit", "-l", type=int, default=20,
                        help="Maximum messages to return (default: 20, max: 100)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.query and not args.channel:
        print("Error: Either --query or --channel is required", file=sys.stderr)
        sys.exit(1)

    # Check for auth token
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("Error: SLACK_BOT_TOKEN environment variable not set", file=sys.stderr)
        print("Usage: SLACK_BOT_TOKEN=xoxb-xxx python run.py --query 'search term'", file=sys.stderr)
        sys.exit(1)

    try:
        if args.query:
            result = search_messages(token, args.query, args.limit)
        else:
            result = get_channel_history(token, args.channel, args.limit)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if args.query:
                matches = result.get("messages", {}).get("matches", [])
                print(f"Found {len(matches)} messages:\n")
                for msg in matches[:args.limit]:
                    print(f"  - {msg.get('username', 'Unknown')}: {msg.get('text', '')[:100]}")
                    print(f"    Channel: {msg.get('channel', {}).get('name', 'N/A')}")
                    print()
            else:
                messages = result.get("messages", [])
                print(f"Found {len(messages)} messages in channel:\n")
                for msg in messages:
                    print(f"  - {msg.get('text', '')[:100]}")
                    print()

    except requests.RequestException as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
