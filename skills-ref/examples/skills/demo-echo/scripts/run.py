#!/usr/bin/env python3
"""
Demo Echo Skill - Returns input as output.

This skill demonstrates the basic skill execution pattern.
No authentication required.

Usage:
    python run.py
    python run.py --message "Hello World"
    python run.py --json
"""

import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(description="Demo echo skill")
    parser.add_argument("--message", "-m", default="Hello from Agent Skills!",
                        help="Message to echo")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    result = {
        "message": args.message,
        "skill": "demo-echo",
        "note": "This is a demo skill to verify the runtime works.",
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Message: {result['message']}")
        print(f"Skill: {result['skill']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
