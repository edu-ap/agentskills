"""CLI for skills-ref library."""

import json
import sys
from pathlib import Path

import click

from .errors import SkillError
from .parser import read_properties
from .prompt import to_prompt
from .validator import validate
from .composition import check_composition


def _is_skill_md_file(path: Path) -> bool:
    """Check if path points directly to a SKILL.md or skill.md file."""
    return path.is_file() and path.name.lower() == "skill.md"


@click.group()
@click.version_option()
def main():
    """Reference library for Agent Skills."""
    pass


@main.command("validate")
@click.argument("skill_path", type=click.Path(exists=True, path_type=Path))
def validate_cmd(skill_path: Path):
    """Validate a skill directory.

    Checks that the skill has a valid SKILL.md with proper frontmatter,
    correct naming conventions, and required fields.

    Exit codes:
        0: Valid skill
        1: Validation errors found
    """
    if _is_skill_md_file(skill_path):
        skill_path = skill_path.parent

    errors = validate(skill_path)

    if errors:
        click.echo(f"Validation failed for {skill_path}:", err=True)
        for error in errors:
            click.echo(f"  - {error}", err=True)
        sys.exit(1)
    else:
        click.echo(f"Valid skill: {skill_path}")


@main.command("read-properties")
@click.argument("skill_path", type=click.Path(exists=True, path_type=Path))
def read_properties_cmd(skill_path: Path):
    """Read and print skill properties as JSON.

    Parses the YAML frontmatter from SKILL.md and outputs the
    properties as JSON.

    Exit codes:
        0: Success
        1: Parse error
    """
    try:
        if _is_skill_md_file(skill_path):
            skill_path = skill_path.parent

        props = read_properties(skill_path)
        click.echo(json.dumps(props.to_dict(), indent=2))
    except SkillError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("to-prompt")
@click.argument(
    "skill_paths", type=click.Path(exists=True, path_type=Path), nargs=-1, required=True
)
def to_prompt_cmd(skill_paths: tuple[Path, ...]):
    """Generate <available_skills> XML for agent prompts.

    Accepts one or more skill directories.

    Exit codes:
        0: Success
        1: Error
    """
    try:
        resolved_paths = []
        for skill_path in skill_paths:
            if _is_skill_md_file(skill_path):
                resolved_paths.append(skill_path.parent)
            else:
                resolved_paths.append(skill_path)

        output = to_prompt(resolved_paths)
        click.echo(output)
    except SkillError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("compose")
@click.argument("source_path", type=click.Path(exists=True, path_type=Path))
@click.argument("target_path", type=click.Path(exists=True, path_type=Path))
def compose_cmd(source_path: Path, target_path: Path):
    """Check if two skills can be composed together.

    Validates that the source skill's output types are compatible with
    the target skill's input types. Skills without composition metadata
    are treated as unconstrained (always compatible).

    Example:
        skills-ref compose ./email-read ./customer-intel

    Exit codes:
        0: Composition is valid
        1: Composition is invalid or error occurred
    """
    if _is_skill_md_file(source_path):
        source_path = source_path.parent
    if _is_skill_md_file(target_path):
        target_path = target_path.parent

    result = check_composition(source_path, target_path)

    if result.valid:
        click.echo(f"✓ {result.source} → {result.target}")
        click.echo(f"  {result.reason}")
    else:
        click.echo(f"✗ {result.source} → {result.target}", err=True)
        click.echo(f"  {result.reason}", err=True)
        sys.exit(1)


@main.command("run")
@click.argument("skill_name")
@click.argument("args", nargs=-1)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def run_cmd(skill_name: str, args: tuple[str, ...], as_json: bool):
    """Run a skill and return its output.

    Actually executes the skill's underlying script with auth checking.

    Example:
        skills-ref run hubspot-companies --limit 5
        skills-ref run slack-read --channel "general"

    Exit codes:
        0: Success
        1: Auth failed or execution error
    """
    try:
        from .runtime import run_skill
    except ImportError as e:
        click.echo(f"Runtime not available: {e}", err=True)
        sys.exit(1)

    result = run_skill(skill_name, list(args))

    if result.success:
        if as_json:
            click.echo(result.to_json())
        else:
            click.echo(f"✓ {skill_name} completed")
            click.echo(f"Output types: {result.output_types}")
            click.echo("---")
            output_str = result.output if isinstance(result.output, str) else json.dumps(result.output, indent=2)
            # Truncate very long output
            if len(output_str) > 3000:
                click.echo(output_str[:3000] + "\n... (truncated)")
            else:
                click.echo(output_str)
    else:
        click.echo(f"✗ {skill_name} failed: {result.error}", err=True)
        sys.exit(1)


@main.command("auth")
@click.argument("skill_name", required=False)
def auth_cmd(skill_name: str):
    """Check auth status for skills.

    If no skill specified, shows auth status for all available skills.

    Example:
        skills-ref auth hubspot-companies
        skills-ref auth

    Exit codes:
        0: Auth available
        1: Auth missing or error
    """
    try:
        from .runtime import check_auth, list_skills
    except ImportError as e:
        click.echo(f"Runtime not available: {e}", err=True)
        sys.exit(1)

    if skill_name:
        ok, msg = check_auth(skill_name)
        status = "✓" if ok else "✗"
        click.echo(f"{status} {skill_name}: {msg}")
        sys.exit(0 if ok else 1)
    else:
        skills = list_skills()
        click.echo("=== SKILL AUTH STATUS ===\n")
        for name, info in skills.items():
            click.echo(f"{info['auth_status']} {name}: {info['auth_message']}")


@main.command("list")
def list_cmd():
    """List all available skills with auth status.

    Shows registered skills and their current auth availability.
    """
    try:
        from .runtime import list_skills
    except ImportError as e:
        click.echo(f"Runtime not available: {e}", err=True)
        sys.exit(1)

    skills = list_skills()
    click.echo("=== AVAILABLE SKILLS ===\n")
    for name, info in skills.items():
        click.echo(f"{info['auth_status']} {name}")
        click.echo(f"    {info['description']}")
        click.echo(f"    Auth: {info['auth_message']}")
        click.echo(f"    Outputs: {info['outputs']}")
        click.echo()


@main.command("chain")
@click.argument("pipeline")
@click.option("--no-validate", is_flag=True, help="Skip composition validation")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show step-by-step execution")
def chain_cmd(pipeline: str, no_validate: bool, as_json: bool, verbose: bool):
    """Run a chain of skills piping output from one to the next.

    Validates that skills can be composed (type-compatible) before running.
    Each skill receives the previous skill's JSON output via stdin.

    Example:
        skills-ref chain "demo-echo | demo-echo"
        skills-ref chain "hubspot-read | customer-intel"
        skills-ref chain "email-read --limit 10 | summarize"

    Exit codes:
        0: Chain completed successfully
        1: Validation or execution error
    """
    try:
        from .runtime import chain_skills
    except ImportError as e:
        click.echo(f"Runtime not available: {e}", err=True)
        sys.exit(1)

    if verbose:
        click.echo(f"Chain: {pipeline}")
        click.echo("---")

    result = chain_skills(pipeline, validate=not no_validate)

    if result.success:
        if as_json:
            click.echo(json.dumps({
                "success": True,
                "output": result.output,
                "steps": result.steps
            }, indent=2))
        else:
            if verbose:
                click.echo("\nExecution trace:")
                for i, step in enumerate(result.steps):
                    status = "✓" if step.get("success") else "✗"
                    click.echo(f"  {i+1}. {status} {step['skill']}")

            click.echo("\n✓ Chain completed successfully")
            click.echo("---")
            output_str = result.output if isinstance(result.output, str) else json.dumps(result.output, indent=2)
            if len(output_str) > 3000:
                click.echo(output_str[:3000] + "\n... (truncated)")
            else:
                click.echo(output_str)
    else:
        if as_json:
            click.echo(json.dumps({
                "success": False,
                "error": result.error,
                "steps": result.steps
            }, indent=2), err=True)
        else:
            click.echo(f"✗ Chain failed: {result.error}", err=True)
            if verbose and result.steps:
                click.echo("\nExecution trace:", err=True)
                for i, step in enumerate(result.steps):
                    status = "✓" if step.get("success") else "✗"
                    click.echo(f"  {i+1}. {status} {step['skill']}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
