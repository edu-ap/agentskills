#!/usr/bin/env python3
"""
Compose Validator Skill - Check if two skills can be composed.

Validates that source skill outputs are compatible with target skill inputs.
Use this before executing skill chains to fail fast.

Usage:
    python run.py --source hubspot-read --target customer-intel
    python run.py --source email-read --target deal-analysis --json
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import strictyaml
except ImportError:
    print("Error: strictyaml required. Install with: pip install strictyaml", file=sys.stderr)
    sys.exit(1)


def get_skills_directory() -> Path:
    """Get the skills directory (parent of this skill's directory)."""
    # This script is at: compose-validator/scripts/run.py
    # Skills are at: ../  (sibling directories)
    return Path(__file__).parent.parent.parent


def parse_skill_composition(skill_dir: Path) -> dict:
    """Parse composition metadata from a skill's SKILL.md."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        skill_md = skill_dir / "skill.md"

    if not skill_md.exists():
        return {"error": f"SKILL.md not found in {skill_dir}"}

    content = skill_md.read_text()

    if not content.startswith("---"):
        return {"inputs": [], "outputs": []}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {"inputs": [], "outputs": []}

    try:
        parsed = strictyaml.load(parts[1])
        metadata = parsed.data
    except Exception as e:
        return {"error": f"Invalid YAML: {e}"}

    composition = metadata.get("composition", {})
    if not composition:
        return {"inputs": [], "outputs": []}

    inputs = composition.get("inputs", [])
    outputs = composition.get("outputs", [])

    # Normalize to lists
    if isinstance(inputs, str):
        inputs = [inputs]
    if isinstance(outputs, str):
        outputs = [outputs]

    return {
        "inputs": inputs or [],
        "outputs": outputs or [],
        "name": metadata.get("name", skill_dir.name),
        "description": metadata.get("description", ""),
    }


def find_skill(skill_ref: str, skills_dir: Path) -> Path:
    """Find a skill by name or path."""
    # If it's a path, use it directly
    skill_path = Path(skill_ref)
    if skill_path.exists():
        return skill_path

    # Otherwise, look in the skills directory
    skill_dir = skills_dir / skill_ref
    if skill_dir.exists():
        return skill_dir

    return None


def check_composition(source_ref: str, target_ref: str) -> dict:
    """Check if source skill can be composed with target skill."""
    skills_dir = get_skills_directory()

    # Find skills
    source_dir = find_skill(source_ref, skills_dir)
    target_dir = find_skill(target_ref, skills_dir)

    if not source_dir:
        return {
            "valid": False,
            "source": source_ref,
            "target": target_ref,
            "reason": f"Source skill not found: {source_ref}",
        }

    if not target_dir:
        return {
            "valid": False,
            "source": source_ref,
            "target": target_ref,
            "reason": f"Target skill not found: {target_ref}",
        }

    # Parse composition metadata
    source_comp = parse_skill_composition(source_dir)
    target_comp = parse_skill_composition(target_dir)

    if "error" in source_comp:
        return {
            "valid": False,
            "source": source_ref,
            "target": target_ref,
            "reason": f"Source skill error: {source_comp['error']}",
        }

    if "error" in target_comp:
        return {
            "valid": False,
            "source": source_ref,
            "target": target_ref,
            "reason": f"Target skill error: {target_comp['error']}",
        }

    source_outputs = set(source_comp.get("outputs", []))
    target_inputs = set(target_comp.get("inputs", []))

    # If target has no input constraints, it's always compatible
    if not target_inputs:
        return {
            "valid": True,
            "source": source_ref,
            "target": target_ref,
            "source_outputs": list(source_outputs),
            "target_inputs": [],
            "matched_types": [],
            "reason": "Target skill has no input constraints (accepts any input)",
        }

    # If source has no outputs declared, it's unconstrained
    if not source_outputs:
        return {
            "valid": True,
            "source": source_ref,
            "target": target_ref,
            "source_outputs": [],
            "target_inputs": list(target_inputs),
            "matched_types": [],
            "reason": "Source skill has no output constraints (produces untyped output)",
        }

    # Check for matching types
    matched = source_outputs & target_inputs

    if matched:
        return {
            "valid": True,
            "source": source_ref,
            "target": target_ref,
            "source_outputs": list(source_outputs),
            "target_inputs": list(target_inputs),
            "matched_types": list(matched),
            "reason": f"Compatible: {', '.join(matched)} can flow from source to target",
        }
    else:
        return {
            "valid": False,
            "source": source_ref,
            "target": target_ref,
            "source_outputs": list(source_outputs),
            "target_inputs": list(target_inputs),
            "matched_types": [],
            "reason": f"Incompatible: {source_ref} produces {list(source_outputs)} but {target_ref} requires {list(target_inputs)}",
        }


def main():
    parser = argparse.ArgumentParser(
        description="Validate that two skills can be composed together"
    )
    parser.add_argument("--source", "-s", required=True,
                        help="Source skill name or path")
    parser.add_argument("--target", "-t", required=True,
                        help="Target skill name or path")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    result = check_composition(args.source, args.target)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["valid"]:
            print(f"✓ {result['source']} → {result['target']}")
            print(f"  {result['reason']}")
            if result.get("matched_types"):
                print(f"  Matched types: {', '.join(result['matched_types'])}")
        else:
            print(f"✗ {result['source']} → {result['target']}")
            print(f"  {result['reason']}")

        # Show type details
        if result.get("source_outputs"):
            print(f"  Source outputs: {result['source_outputs']}")
        if result.get("target_inputs"):
            print(f"  Target inputs: {result['target_inputs']}")

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
