"""Tests for skill runtime execution."""

import os
import pytest
from skills_ref.runtime import run_skill, check_auth, list_skills, SkillResult


class TestCheckAuth:
    """Test auth capability checking."""

    def test_unknown_skill_no_auth_required(self):
        """Skills without auth requirements pass."""
        ok, msg = check_auth("demo-echo")
        assert ok is True
        assert "No auth required" in msg

    def test_missing_env_var(self, monkeypatch):
        """Missing env var fails auth check."""
        monkeypatch.delenv("HUBSPOT_ACCESS_TOKEN", raising=False)
        ok, msg = check_auth("hubspot-companies")
        assert ok is False
        assert "Missing" in msg

    def test_present_env_var(self, monkeypatch):
        """Present env var passes auth check."""
        monkeypatch.setenv("HUBSPOT_ACCESS_TOKEN", "test-token")
        ok, msg = check_auth("hubspot-companies")
        assert ok is True
        assert "OK" in msg


class TestRunSkill:
    """Test skill execution."""

    def test_demo_echo_runs(self):
        """Demo echo skill runs without auth."""
        result = run_skill("demo-echo")
        assert result.success is True
        assert result.output["message"] == "Hello from Agent Skills!"
        assert result.error is None
        assert "demo-output" in result.output_types

    def test_demo_echo_with_message(self):
        """Demo echo skill accepts --message argument."""
        result = run_skill("demo-echo", ["--message", "Test message"])
        assert result.success is True
        assert result.output["message"] == "Test message"

    def test_unknown_skill_fails(self):
        """Unknown skill returns error."""
        result = run_skill("nonexistent-skill")
        assert result.success is False
        assert "Unknown skill" in result.error

    def test_missing_auth_fails(self, monkeypatch):
        """Skill with missing auth fails."""
        monkeypatch.delenv("HUBSPOT_ACCESS_TOKEN", raising=False)
        result = run_skill("hubspot-companies")
        assert result.success is False
        assert "Auth failed" in result.error


class TestListSkills:
    """Test skill listing."""

    def test_returns_all_skills(self):
        """List returns all discovered skills."""
        skills = list_skills()
        assert "demo-echo" in skills
        assert "hubspot-companies" in skills

    def test_skill_has_required_fields(self):
        """Each skill has required metadata."""
        skills = list_skills()
        for name, info in skills.items():
            assert "description" in info
            assert "auth_status" in info
            assert "outputs" in info
            assert "has_script" in info


class TestSkillResult:
    """Test SkillResult dataclass."""

    def test_to_json(self):
        """SkillResult serializes to JSON."""
        result = SkillResult(
            success=True,
            output={"key": "value"},
            output_types=["test-type"]
        )
        json_str = result.to_json()
        assert '"success": true' in json_str
        assert '"key": "value"' in json_str
        assert '"test-type"' in json_str
