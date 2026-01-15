"""Integration tests for skills with real APIs.

These tests call external APIs and may fail due to:
- Missing credentials
- API rate limits
- Temporary API outages

Run unit tests only (always pass):
    pytest tests/ --ignore=tests/test_integration.py

Run integration tests (requires credentials, may be flaky):
    pytest tests/test_integration.py -v
"""

import os
import pytest
from skills_ref.runtime import run_skill, check_auth, list_skills


# Mark entire module as integration tests
pytestmark = pytest.mark.integration


# ============================================================
# FIXTURES AND HELPERS
# ============================================================

def has_hubspot_auth():
    """Check if HubSpot credentials are available."""
    return bool(os.environ.get("HUBSPOT_ACCESS_TOKEN"))


def has_slack_user_token():
    """Check if Slack USER token is available.

    Slack search API requires a user token with search:read scope.
    Bot tokens will fail with 'not_allowed_token_type'.
    We check for a specific env var to avoid running with wrong token type.
    """
    return os.environ.get("SLACK_TOKEN_TYPE") == "user"


def has_github_auth():
    """Check if GitHub credentials are available."""
    return bool(os.environ.get("GITHUB_TOKEN"))


def has_email_auth():
    """Check if email credentials are available (Gmail or Outlook)."""
    return bool(
        os.environ.get("GMAIL_TOKEN_FILE") or
        os.environ.get("MS_GRAPH_ACCESS_TOKEN")
    )


# ============================================================
# HUBSPOT INTEGRATION TESTS
# ============================================================

@pytest.mark.skipif(not has_hubspot_auth(), reason="HUBSPOT_ACCESS_TOKEN not set")
class TestHubSpotIntegration:
    """Integration tests for HubSpot skills.

    These tests call the real HubSpot API. They may occasionally fail
    due to API rate limits or temporary unavailability (503 errors).
    """

    def test_hubspot_companies_runs(self):
        """Test hubspot-companies skill executes successfully."""
        result = run_skill("hubspot-companies", ["--limit", "1"])
        assert result.success, f"Failed: {result.error}"
        assert result.output is not None

    def test_hubspot_deals_runs(self):
        """Test hubspot-deals skill executes successfully."""
        result = run_skill("hubspot-deals", ["--limit", "1"])
        assert result.success, f"Failed: {result.error}"
        assert result.output is not None

    def test_hubspot_read_runs(self):
        """Test hubspot-read skill executes successfully."""
        result = run_skill("hubspot-read", ["--limit", "1"])
        assert result.success, f"Failed: {result.error}"
        assert result.output is not None

    def test_hubspot_output_types(self):
        """Test HubSpot skills return expected output types."""
        result = run_skill("hubspot-companies", ["--limit", "1"])
        assert result.success, f"Failed: {result.error}"
        assert "crm-companies" in result.output_types


# ============================================================
# SLACK INTEGRATION TESTS
# ============================================================

@pytest.mark.skipif(not has_slack_user_token(), reason="SLACK_USER_TOKEN not set (bot tokens can't search)")
class TestSlackIntegration:
    """Integration tests for Slack skills.

    IMPORTANT: Slack search requires a USER token with search:read scope.
    Bot tokens (SLACK_BOT_TOKEN) will fail with 'not_allowed_token_type'.
    Set SLACK_USER_TOKEN to run these tests.
    """

    def test_slack_read_runs(self):
        """Test slack-read skill executes successfully."""
        result = run_skill("slack-read", ["--query", "test", "--limit", "1"])
        assert result.success, f"Failed: {result.error}"
        assert result.output is not None

    def test_slack_output_types(self):
        """Test Slack skill returns expected output types."""
        result = run_skill("slack-read", ["--query", "test", "--limit", "1"])
        assert result.success
        assert "message-list" in result.output_types


# ============================================================
# GITHUB INTEGRATION TESTS
# ============================================================

@pytest.mark.skipif(not has_github_auth(), reason="GITHUB_TOKEN not set")
class TestGitHubIntegration:
    """Integration tests for GitHub skills."""

    def test_github_repos_runs(self):
        """Test github-repos skill executes successfully."""
        result = run_skill("github-repos", ["--limit", "1"])
        assert result.success, f"Failed: {result.error}"
        assert result.output is not None


# ============================================================
# EMAIL INTEGRATION TESTS
# ============================================================

@pytest.mark.skipif(not has_email_auth(), reason="GMAIL_TOKEN_FILE or MS_GRAPH_ACCESS_TOKEN not set")
class TestEmailIntegration:
    """Integration tests for email skills."""

    def test_email_read_runs(self):
        """Test email-read skill executes successfully."""
        result = run_skill("email-read", ["--limit", "1"])
        assert result.success, f"Failed: {result.error}"
        assert result.output is not None


# ============================================================
# SKILL DISCOVERY TESTS (No auth needed)
# ============================================================

class TestSkillDiscovery:
    """Tests for skill discovery that don't require API calls."""

    def test_list_skills_returns_all(self):
        """Test that list_skills returns all expected skills."""
        skills = list_skills()

        expected = [
            "demo-echo",
            "hubspot-companies",
            "hubspot-deals",
            "hubspot-read",
            "github-repos",
            "slack-read",
            "email-read",
            "compose-validator",
        ]

        for skill in expected:
            assert skill in skills, f"Missing skill: {skill}"

    def test_all_skills_have_scripts(self):
        """Test that all discovered skills have scripts/run.py."""
        skills = list_skills()

        for name, info in skills.items():
            assert info["has_script"], f"Skill {name} missing scripts/run.py"

    def test_auth_check_reports_correctly(self):
        """Test that auth checking reports status accurately."""
        # demo-echo needs no auth
        ok, msg = check_auth("demo-echo")
        assert ok
        assert "No auth required" in msg

        # hubspot-companies needs HUBSPOT_ACCESS_TOKEN
        ok, msg = check_auth("hubspot-companies")
        if has_hubspot_auth():
            assert ok
            assert "OK" in msg
        else:
            assert not ok
            assert "Missing" in msg

    def test_skill_metadata_populated(self):
        """Test that skill metadata is correctly populated."""
        skills = list_skills()

        # Check demo-echo has basic fields
        demo = skills.get("demo-echo")
        assert demo is not None
        assert demo["description"]
        assert demo["path"]

        # Check hubspot-companies has output types
        hubspot = skills.get("hubspot-companies")
        assert hubspot is not None
        assert "crm-companies" in hubspot["outputs"]


# ============================================================
# COMPOSE-VALIDATOR TESTS (No auth needed - reads metadata only)
# ============================================================

class TestComposeValidator:
    """Tests for the compose-validator skill.

    This skill is key to the LLM-driven composition approach:
    The LLM can choose to use this skill to check compatibility
    before running skills, rather than having infrastructure force it.
    """

    def test_compose_validator_runs(self):
        """Test compose-validator executes successfully."""
        result = run_skill("compose-validator", [
            "--source", "hubspot-read",
            "--target", "demo-echo"
        ])
        assert result.success, f"Failed: {result.error}"
        assert result.output is not None

    def test_compose_validator_valid_composition(self):
        """Test compose-validator correctly identifies valid composition."""
        result = run_skill("compose-validator", [
            "--source", "demo-echo",
            "--target", "demo-echo",
            "--json"
        ])
        assert result.success
        # demo-echo has no composition constraints, so should be valid
        assert result.output.get("valid") is True

    def test_compose_validator_returns_composition_result(self):
        """Test compose-validator returns expected output type."""
        result = run_skill("compose-validator", [
            "--source", "hubspot-companies",
            "--target", "demo-echo"
        ])
        assert result.success
        assert "composition-result" in result.output_types

    def test_compose_validator_invalid_skill(self):
        """Test compose-validator handles invalid skill names."""
        result = run_skill("compose-validator", [
            "--source", "nonexistent-skill",
            "--target", "demo-echo"
        ])
        # Script exits 1 for invalid composition (correct behavior)
        assert not result.success  # exit code 1
        assert "not found" in result.error or "not found" in str(result.output).lower()
