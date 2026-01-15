#!/usr/bin/env python3
"""
HubSpot Deals Skill - Fetch deals from HubSpot CRM.

Requires: HUBSPOT_ACCESS_TOKEN environment variable

Usage:
    HUBSPOT_ACCESS_TOKEN=xxx python run.py
    HUBSPOT_ACCESS_TOKEN=xxx python run.py --limit 5
    HUBSPOT_ACCESS_TOKEN=xxx python run.py --stage "closedwon"
    HUBSPOT_ACCESS_TOKEN=xxx python run.py --json
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


def get_deals(token: str, limit: int = 10, stage: str = None) -> dict:
    """Fetch deals from HubSpot API."""
    params = {
        "limit": min(limit, 100),
        "properties": "dealname,dealstage,amount,closedate,pipeline",
    }

    resp = requests.get(
        "https://api.hubapi.com/crm/v3/objects/deals",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30,
    )

    if resp.status_code == 401:
        return {"error": "Invalid or expired HUBSPOT_ACCESS_TOKEN"}

    resp.raise_for_status()
    data = resp.json()

    # Filter by stage if specified
    if stage:
        data["results"] = [
            d for d in data.get("results", [])
            if d.get("properties", {}).get("dealstage", "").lower() == stage.lower()
        ]

    return data


def main():
    parser = argparse.ArgumentParser(description="Fetch deals from HubSpot CRM")
    parser.add_argument("--limit", "-l", type=int, default=10,
                        help="Maximum deals to return (default: 10, max: 100)")
    parser.add_argument("--stage", "-s",
                        help="Filter by deal stage (e.g., closedwon, closedlost)")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    # Check for auth token
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN")
    if not token:
        print("Error: HUBSPOT_ACCESS_TOKEN environment variable not set", file=sys.stderr)
        print("Usage: HUBSPOT_ACCESS_TOKEN=xxx python run.py", file=sys.stderr)
        sys.exit(1)

    try:
        result = get_deals(token, args.limit, args.stage)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            deals = result.get("results", [])
            print(f"Found {len(deals)} deals:\n")
            for deal in deals:
                props = deal.get("properties", {})
                amount = props.get("amount")
                amount_str = f"${float(amount):,.2f}" if amount else "N/A"
                print(f"  - {props.get('dealname', 'Unknown')}")
                print(f"    Amount: {amount_str}")
                print(f"    Stage: {props.get('dealstage', 'N/A')}")
                print(f"    Close Date: {props.get('closedate', 'N/A')}")
                print()

    except requests.RequestException as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
