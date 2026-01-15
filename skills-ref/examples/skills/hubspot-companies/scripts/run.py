#!/usr/bin/env python3
"""
HubSpot Companies Skill - Fetch companies from HubSpot CRM.

Requires: HUBSPOT_ACCESS_TOKEN environment variable

Usage:
    HUBSPOT_ACCESS_TOKEN=xxx python run.py
    HUBSPOT_ACCESS_TOKEN=xxx python run.py --limit 5
    HUBSPOT_ACCESS_TOKEN=xxx python run.py --domain "acme-corp.com"
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


def get_companies(token: str, limit: int = 10, domain: str = None) -> dict:
    """Fetch companies from HubSpot API."""
    params = {
        "limit": min(limit, 100),
        "properties": "name,domain,lifecyclestage,industry,city,country",
    }

    # Add domain filter if specified
    if domain:
        params["filterGroups"] = json.dumps([{
            "filters": [{
                "propertyName": "domain",
                "operator": "CONTAINS_TOKEN",
                "value": domain
            }]
        }])

    resp = requests.get(
        "https://api.hubapi.com/crm/v3/objects/companies",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30,
    )

    if resp.status_code == 401:
        return {"error": "Invalid or expired HUBSPOT_ACCESS_TOKEN"}

    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Fetch companies from HubSpot CRM")
    parser.add_argument("--limit", "-l", type=int, default=10,
                        help="Maximum companies to return (default: 10, max: 100)")
    parser.add_argument("--domain", "-d",
                        help="Filter by company domain")
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
        result = get_companies(token, args.limit, args.domain)

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            companies = result.get("results", [])
            print(f"Found {len(companies)} companies:\n")
            for company in companies:
                props = company.get("properties", {})
                print(f"  - {props.get('name', 'Unknown')}")
                print(f"    Domain: {props.get('domain', 'N/A')}")
                print(f"    Industry: {props.get('industry', 'N/A')}")
                print(f"    Stage: {props.get('lifecyclestage', 'N/A')}")
                print()

    except requests.RequestException as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
