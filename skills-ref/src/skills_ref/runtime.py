"""
Skill Runtime - Discover and Execute Skills

This module provides runtime execution for skills by:
1. Discovering skills from filesystem (each skill is a folder with SKILL.md)
2. Parsing skill metadata from SKILL.md frontmatter
3. Executing scripts/run.py in each skill folder

Usage:
    skills-ref run demo-echo
    skills-ref run hubspot-companies --limit 5
    HUBSPOT_ACCESS_TOKEN=xxx skills-ref run hubspot-companies
    skills-ref list
    skills-ref auth hubspot-companies
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .parser import read_properties


@dataclass
class SkillResult:
    """Result of running a skill."""
    success: bool
    output: Any  # JSON-serializable output or raw text
    error: Optional[str] = None
    output_types: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps({
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "output_types": self.output_types or [],
        }, indent=2)


# ============================================================
# AUTH CONFIGURATION
# ============================================================

# Maps skill name -> required environment variables
# Note: email-read accepts either GMAIL_TOKEN_FILE or MS_GRAPH_ACCESS_TOKEN
AUTH_REQUIREMENTS = {
    "hubspot-companies": ["HUBSPOT_ACCESS_TOKEN"],
    "hubspot-deals": ["HUBSPOT_ACCESS_TOKEN"],
    "hubspot-read": ["HUBSPOT_ACCESS_TOKEN"],
    "github-repos": ["GITHUB_TOKEN"],
    "slack-read": ["SLACK_BOT_TOKEN"],
    "email-read": ["GMAIL_TOKEN_FILE", "MS_GRAPH_ACCESS_TOKEN"],  # Either one works
}


def check_auth(skill_name: str) -> tuple[bool, str]:
    """
    Check if auth is available for a skill.

    Args:
        skill_name: Name of skill to check

    Returns:
        (is_valid, message)
    """
    env_vars = AUTH_REQUIREMENTS.get(skill_name)
    if not env_vars:
        return True, "No auth required"

    # Special case: email-read accepts either Gmail OR Outlook token
    if skill_name == "email-read":
        present = [var for var in env_vars if os.environ.get(var)]
        if present:
            return True, f"OK ({present[0]} set)"
        return False, f"Missing: need one of {', '.join(env_vars)}"

    # Default: all env vars required
    missing = [var for var in env_vars if not os.environ.get(var)]
    if missing:
        return False, f"Missing: {', '.join(missing)}"

    return True, f"OK ({env_vars[0]} set)"


# ============================================================
# SKILL DISCOVERY
# ============================================================

def get_skills_directory() -> Path:
    """Get the default skills directory."""
    # Look relative to this file: src/skills_ref/runtime.py -> examples/skills/
    runtime_dir = Path(__file__).parent
    skills_dir = runtime_dir.parent.parent / "examples" / "skills"
    return skills_dir


def discover_skills(skills_dir: Path = None) -> dict[str, Path]:
    """
    Discover skills from filesystem.

    Args:
        skills_dir: Directory containing skill folders

    Returns:
        Dict mapping skill name -> skill directory path
    """
    if skills_dir is None:
        skills_dir = get_skills_directory()

    if not skills_dir.exists():
        return {}

    skills = {}
    for item in skills_dir.iterdir():
        if item.is_dir():
            skill_md = item / "SKILL.md"
            if not skill_md.exists():
                skill_md = item / "skill.md"
            if skill_md.exists():
                skills[item.name] = item

    return skills


def get_skill_metadata(skill_dir: Path) -> dict:
    """
    Get metadata for a skill from its SKILL.md.

    Returns dict with: name, description, outputs, inputs
    """
    try:
        props = read_properties(skill_dir)
        outputs = []
        if props.composition:
            outputs = props.composition.get("outputs", [])
            if isinstance(outputs, str):
                outputs = [outputs]

        return {
            "name": props.name,
            "description": props.description,
            "outputs": outputs,
            "has_script": (skill_dir / "scripts" / "run.py").exists(),
        }
    except Exception as e:
        return {
            "name": skill_dir.name,
            "description": f"Error reading metadata: {e}",
            "outputs": [],
            "has_script": (skill_dir / "scripts" / "run.py").exists(),
        }


# ============================================================
# SKILL EXECUTION
# ============================================================

def run_skill(skill_name: str, args: list[str] = None, skills_dir: Path = None) -> SkillResult:
    """
    Run a skill and return structured output.

    Args:
        skill_name: Name of skill to run
        args: Arguments to pass to skill script
        skills_dir: Directory containing skills (optional)

    Returns:
        SkillResult with output or error
    """
    args = args or []

    # Discover available skills
    skills = discover_skills(skills_dir)

    if skill_name not in skills:
        available = list(skills.keys()) if skills else ["(no skills found)"]
        return SkillResult(
            success=False,
            output=None,
            error=f"Unknown skill: {skill_name}. Available: {available}"
        )

    skill_dir = skills[skill_name]
    script_path = skill_dir / "scripts" / "run.py"

    if not script_path.exists():
        return SkillResult(
            success=False,
            output=None,
            error=f"Skill '{skill_name}' has no scripts/run.py"
        )

    # Check auth
    auth_ok, auth_msg = check_auth(skill_name)
    if not auth_ok:
        return SkillResult(
            success=False,
            output=None,
            error=f"Auth failed: {auth_msg}"
        )

    # Get skill metadata for output types
    metadata = get_skill_metadata(skill_dir)

    # Run the script
    try:
        # Always request JSON output for structured parsing
        cmd = [sys.executable, str(script_path), "--json"] + list(args)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(skill_dir),
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or f"Script exited with code {result.returncode}"
            return SkillResult(
                success=False,
                output=result.stdout,
                error=error_msg,
                output_types=metadata.get("outputs", [])
            )

        # Try to parse JSON output
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            output = result.stdout

        return SkillResult(
            success=True,
            output=output,
            output_types=metadata.get("outputs", [])
        )

    except subprocess.TimeoutExpired:
        return SkillResult(
            success=False,
            output=None,
            error="Skill execution timed out (60s)"
        )
    except Exception as e:
        return SkillResult(
            success=False,
            output=None,
            error=f"Execution error: {e}"
        )


# ============================================================
# LISTING
# ============================================================

def list_skills(skills_dir: Path = None) -> dict[str, dict]:
    """
    List all available skills with metadata and auth status.

    Returns:
        Dict mapping skill name -> skill info
    """
    skills = discover_skills(skills_dir)
    result = {}

    for name, skill_dir in skills.items():
        metadata = get_skill_metadata(skill_dir)
        auth_ok, auth_msg = check_auth(name)

        result[name] = {
            "description": metadata.get("description", ""),
            "outputs": metadata.get("outputs", []),
            "has_script": metadata.get("has_script", False),
            "auth_status": "✓" if auth_ok else "✗",
            "auth_message": auth_msg,
            "path": str(skill_dir),
        }

    return result
