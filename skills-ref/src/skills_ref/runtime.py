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


# ============================================================
# SKILL CHAINING
# ============================================================

@dataclass
class ChainResult:
    """Result of running a skill chain."""
    success: bool
    output: Any
    error: Optional[str] = None
    steps: list[dict] = field(default_factory=list)  # Track each step


def parse_chain(chain_spec: str) -> list[tuple[str, list[str]]]:
    """
    Parse a chain specification into skill names and args.

    Format: "skill-a | skill-b --arg value | skill-c"

    Returns:
        List of (skill_name, args) tuples
    """
    import shlex

    steps = []
    for part in chain_spec.split("|"):
        part = part.strip()
        if not part:
            continue

        tokens = shlex.split(part)
        skill_name = tokens[0]
        args = tokens[1:] if len(tokens) > 1 else []
        steps.append((skill_name, args))

    return steps


def chain_skills(
    chain_spec: str,
    validate: bool = True,
    skills_dir: Path = None
) -> ChainResult:
    """
    Run a chain of skills, piping output from one to the next.

    Args:
        chain_spec: Pipeline specification like "skill-a | skill-b"
        validate: If True, validate composition before running
        skills_dir: Directory containing skills (optional)

    Returns:
        ChainResult with final output or error

    Example:
        result = chain_skills("hubspot-read | customer-intel")
    """
    from .composition import check_composition

    steps = parse_chain(chain_spec)

    if not steps:
        return ChainResult(
            success=False,
            output=None,
            error="Empty chain specification"
        )

    if len(steps) < 2:
        return ChainResult(
            success=False,
            output=None,
            error="Chain requires at least 2 skills (use 'run' for single skill)"
        )

    # Discover skills
    skills = discover_skills(skills_dir)

    # Validate all skills exist and have scripts
    for skill_name, _ in steps:
        if skill_name not in skills:
            return ChainResult(
                success=False,
                output=None,
                error=f"Unknown skill: {skill_name}"
            )
        skill_dir = skills[skill_name]
        if not (skill_dir / "scripts" / "run.py").exists():
            return ChainResult(
                success=False,
                output=None,
                error=f"Skill '{skill_name}' has no scripts/run.py"
            )

    # Validate composition between adjacent skills
    if validate:
        for i in range(len(steps) - 1):
            source_name = steps[i][0]
            target_name = steps[i + 1][0]

            source_dir = skills[source_name]
            target_dir = skills[target_name]

            comp_result = check_composition(source_dir, target_dir)
            if not comp_result.valid:
                return ChainResult(
                    success=False,
                    output=None,
                    error=f"Composition failed at step {i+1}: {comp_result.reason}"
                )

    # Check auth for all skills before running
    for skill_name, _ in steps:
        auth_ok, auth_msg = check_auth(skill_name)
        if not auth_ok:
            return ChainResult(
                success=False,
                output=None,
                error=f"Auth failed for '{skill_name}': {auth_msg}"
            )

    # Execute the chain
    chain_steps = []
    current_input = None

    for i, (skill_name, args) in enumerate(steps):
        skill_dir = skills[skill_name]
        script_path = skill_dir / "scripts" / "run.py"

        # Build command with --json flag and any user args
        cmd = [sys.executable, str(script_path), "--json"] + args

        # If we have input from previous step, pass via stdin
        stdin_data = None
        if current_input is not None:
            if isinstance(current_input, (dict, list)):
                stdin_data = json.dumps(current_input)
            else:
                stdin_data = str(current_input)

        try:
            result = subprocess.run(
                cmd,
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(skill_dir),
            )

            step_info = {
                "skill": skill_name,
                "success": result.returncode == 0,
                "exit_code": result.returncode,
            }

            if result.returncode != 0:
                step_info["error"] = result.stderr.strip() or f"Exit code {result.returncode}"
                chain_steps.append(step_info)
                return ChainResult(
                    success=False,
                    output=None,
                    error=f"Step {i+1} ({skill_name}) failed: {step_info['error']}",
                    steps=chain_steps
                )

            # Parse output for next step
            try:
                current_input = json.loads(result.stdout)
            except json.JSONDecodeError:
                current_input = result.stdout

            step_info["output_type"] = "json" if isinstance(current_input, (dict, list)) else "text"
            chain_steps.append(step_info)

        except subprocess.TimeoutExpired:
            chain_steps.append({
                "skill": skill_name,
                "success": False,
                "error": "Timeout (60s)"
            })
            return ChainResult(
                success=False,
                output=None,
                error=f"Step {i+1} ({skill_name}) timed out",
                steps=chain_steps
            )
        except Exception as e:
            chain_steps.append({
                "skill": skill_name,
                "success": False,
                "error": str(e)
            })
            return ChainResult(
                success=False,
                output=None,
                error=f"Step {i+1} ({skill_name}) error: {e}",
                steps=chain_steps
            )

    return ChainResult(
        success=True,
        output=current_input,
        steps=chain_steps
    )
