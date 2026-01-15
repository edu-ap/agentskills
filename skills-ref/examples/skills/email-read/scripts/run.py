#!/usr/bin/env python3
"""
Email Read Skill - Search and fetch emails from Gmail or Outlook.

Supports both Gmail (OAuth) and Microsoft Graph (MSAL).

Requires one of:
- GMAIL_CREDENTIALS_FILE: Path to Gmail OAuth credentials.json
- GMAIL_TOKEN_FILE: Path to Gmail token pickle file
- MS_GRAPH_ACCESS_TOKEN: Microsoft Graph API access token

Usage:
    # Gmail
    GMAIL_TOKEN_FILE=~/.gmail_token.pickle python run.py --query "from:example.com"

    # Outlook/Microsoft Graph
    MS_GRAPH_ACCESS_TOKEN=xxx python run.py --query "from:example.com" --service outlook

    # JSON output
    python run.py --query "invoice" --json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


def search_gmail(query: str, limit: int = 20, token_file: str = None) -> dict:
    """Search Gmail using the Gmail API."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        import pickle
    except ImportError:
        return {"error": "Gmail requires: pip install google-auth google-auth-oauthlib google-api-python-client"}

    token_path = token_file or os.environ.get("GMAIL_TOKEN_FILE")
    if not token_path or not os.path.exists(token_path):
        return {"error": f"Gmail token file not found: {token_path}"}

    try:
        with open(token_path, "rb") as f:
            creds = pickle.load(f)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(
            userId="me", q=query, maxResults=limit
        ).execute()

        messages = []
        for msg in results.get("messages", [])[:limit]:
            msg_data = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
            messages.append({
                "id": msg["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "snippet": msg_data.get("snippet", ""),
                "source": "gmail"
            })

        return {"emails": messages}

    except Exception as e:
        return {"error": f"Gmail API error: {e}"}


def search_outlook(query: str, limit: int = 20, token: str = None) -> dict:
    """Search Outlook using Microsoft Graph API."""
    access_token = token or os.environ.get("MS_GRAPH_ACCESS_TOKEN")
    if not access_token:
        return {"error": "MS_GRAPH_ACCESS_TOKEN environment variable not set"}

    try:
        # Search messages
        resp = requests.get(
            "https://graph.microsoft.com/v1.0/me/messages",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "$search": f'"{query}"',
                "$top": min(limit, 50),
                "$select": "id,subject,from,receivedDateTime,bodyPreview"
            },
            timeout=30,
        )

        if resp.status_code == 401:
            return {"error": "Invalid or expired MS_GRAPH_ACCESS_TOKEN"}

        resp.raise_for_status()
        data = resp.json()

        messages = []
        for msg in data.get("value", []):
            messages.append({
                "id": msg.get("id", ""),
                "from": msg.get("from", {}).get("emailAddress", {}).get("address", ""),
                "subject": msg.get("subject", ""),
                "date": msg.get("receivedDateTime", ""),
                "snippet": msg.get("bodyPreview", "")[:200],
                "source": "outlook"
            })

        return {"emails": messages}

    except requests.RequestException as e:
        return {"error": f"Graph API error: {e}"}


def main():
    parser = argparse.ArgumentParser(description="Search and fetch emails")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--service", "-s", choices=["gmail", "outlook", "both"],
                        default="gmail", help="Email service (default: gmail)")
    parser.add_argument("--limit", "-l", type=int, default=20,
                        help="Maximum emails to return (default: 20)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    all_emails = []
    errors = []

    if args.service in ("gmail", "both"):
        result = search_gmail(args.query, args.limit)
        if "error" in result:
            errors.append(f"Gmail: {result['error']}")
        else:
            all_emails.extend(result.get("emails", []))

    if args.service in ("outlook", "both"):
        result = search_outlook(args.query, args.limit)
        if "error" in result:
            errors.append(f"Outlook: {result['error']}")
        else:
            all_emails.extend(result.get("emails", []))

    if errors and not all_emails:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    output = {"emails": all_emails[:args.limit]}
    if errors:
        output["warnings"] = errors

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"Found {len(all_emails)} emails:\n")
        for email in all_emails[:args.limit]:
            print(f"  - {email.get('subject', 'No subject')}")
            print(f"    From: {email.get('from', 'Unknown')}")
            print(f"    Date: {email.get('date', 'N/A')}")
            print(f"    Source: {email.get('source', 'N/A')}")
            print()

        if errors:
            print("\nWarnings:")
            for error in errors:
                print(f"  - {error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
