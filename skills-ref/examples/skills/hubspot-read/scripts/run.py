#!/usr/bin/env python3
"""
HubSpot Read Skill - Fetch combined CRM data from HubSpot.

Fetches companies, contacts, deals, and activities in a single operation.

Requires: HUBSPOT_ACCESS_TOKEN environment variable

Usage:
    HUBSPOT_ACCESS_TOKEN=xxx python run.py --company "acme-corp.com"
    HUBSPOT_ACCESS_TOKEN=xxx python run.py --limit 5
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


BASE_URL = "https://api.hubapi.com"


def get_companies(token: str, limit: int = 10, domain: str = None) -> list:
    """Fetch companies from HubSpot."""
    params = {
        "limit": min(limit, 100),
        "properties": "name,domain,lifecyclestage,industry",
    }

    resp = requests.get(
        f"{BASE_URL}/crm/v3/objects/companies",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30,
    )
    resp.raise_for_status()

    companies = resp.json().get("results", [])

    # Filter by domain if specified
    if domain:
        companies = [c for c in companies
                     if domain.lower() in (c.get("properties", {}).get("domain", "") or "").lower()]

    return companies


def get_contacts(token: str, limit: int = 10) -> list:
    """Fetch contacts from HubSpot."""
    params = {
        "limit": min(limit, 100),
        "properties": "firstname,lastname,email,jobtitle,phone",
    }

    resp = requests.get(
        f"{BASE_URL}/crm/v3/objects/contacts",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def get_deals(token: str, limit: int = 10) -> list:
    """Fetch deals from HubSpot."""
    params = {
        "limit": min(limit, 100),
        "properties": "dealname,dealstage,amount,closedate",
    }

    resp = requests.get(
        f"{BASE_URL}/crm/v3/objects/deals",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def main():
    parser = argparse.ArgumentParser(description="Fetch combined CRM data from HubSpot")
    parser.add_argument("--company", "-c", help="Filter by company domain")
    parser.add_argument("--limit", "-l", type=int, default=10,
                        help="Maximum records per type (default: 10, max: 100)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Check for auth token
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN")
    if not token:
        print("Error: HUBSPOT_ACCESS_TOKEN environment variable not set", file=sys.stderr)
        print("Usage: HUBSPOT_ACCESS_TOKEN=xxx python run.py", file=sys.stderr)
        sys.exit(1)

    try:
        # Fetch all data types
        companies = get_companies(token, args.limit, args.company)
        contacts = get_contacts(token, args.limit)
        deals = get_deals(token, args.limit)

        result = {
            "companies": companies,
            "contacts": contacts,
            "deals": deals,
            "summary": {
                "companies_count": len(companies),
                "contacts_count": len(contacts),
                "deals_count": len(deals),
            }
        }

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"=== HubSpot CRM Data ===\n")
            print(f"Companies: {len(companies)}")
            for c in companies[:5]:
                props = c.get("properties", {})
                print(f"  - {props.get('name', 'Unknown')} ({props.get('domain', 'N/A')})")

            print(f"\nContacts: {len(contacts)}")
            for c in contacts[:5]:
                props = c.get("properties", {})
                name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
                print(f"  - {name or 'Unknown'} ({props.get('email', 'N/A')})")

            print(f"\nDeals: {len(deals)}")
            for d in deals[:5]:
                props = d.get("properties", {})
                print(f"  - {props.get('dealname', 'Unknown')} - {props.get('dealstage', 'N/A')}")

    except requests.RequestException as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
