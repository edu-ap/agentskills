"""Integration tests for skills with real APIs.

These tests actually call external APIs when credentials are available.
They are skipped automatically when credentials are missing.

Run with: pytest tests/test_integration.py -v
Run all: HUBSPOT_ACCESS_TOKEN=xxx SLACK_BOT_TOKEN=xxx pytest tests/test_integration.py -v
"""

import os
import pytest
from skills_ref.runtime import run_skill, check_auth, list_skills


# ============================================================
# FIXTURES AND HELPERS
# ============================================================

def has_hubspot_auth():
    """Check if HubSpot credentials are available."""
    return bool(os.environ.get("HUBSPOT_ACCESS_TOKEN"))


def has_slack_auth():
    """Check if Slack credentials are available."""
    return bool(os.environ.get("SLACK_BOT_TOKEN"))


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

    Note: These tests may fail if HubSpot API is unavailable (503 errors).
    This is expected behavior for integration tests against external APIs.
    """

    @pytest.mark.xfail(reason="HubSpot API may be temporarily unavailable")
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
        assert result.success
        # Check output_types are populated from SKILL.md
        assert "crm-companies" in result.output_types


# ============================================================
# SLACK INTEGRATION TESTS
# ============================================================

@pytest.mark.skipif(not has_slack_auth(), reason="SLACK_BOT_TOKEN not set")
class TestSlackIntegration:
    """Integration tests for Slack skills.

    Note: Slack search requires a user token with search:read scope.
    Bot tokens may fail with 'not_allowed_token_type'.
    """

    @pytest.mark.xfail(reason="Slack search requires user token, not bot token")
    def test_slack_read_runs(self):
        """Test slack-read skill executes successfully."""
        # slack-read requires --query or --channel
        result = run_skill("slack-read", ["--query", "test", "--limit", "1"])
        assert result.success, f"Failed: {result.error}"
        assert result.output is not None

    @pytest.mark.xfail(reason="Slack search requires user token, not bot token")
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
# CHAIN INTEGRATION TESTS
# ============================================================

class TestChainIntegration:
    """Integration tests for skill chaining."""

    def test_demo_echo_chain(self):
        """Test chaining demo-echo (no auth needed)."""
        from skills_ref.runtime import chain_skills

        result = chain_skills("demo-echo | demo-echo")
        assert result.success
        assert len(result.steps) == 2
        assert result.output is not None

    def test_demo_echo_three_step_chain(self):
        """Test three-step chain with demo-echo."""
        from skills_ref.runtime import chain_skills

        result = chain_skills("demo-echo | demo-echo | demo-echo")
        assert result.success
        assert len(result.steps) == 3

    @pytest.mark.skipif(not has_hubspot_auth(), reason="HUBSPOT_ACCESS_TOKEN not set")
    def test_hubspot_chain(self):
        """Test chaining HubSpot skills."""
        from skills_ref.runtime import chain_skills

        # hubspot-companies | hubspot-read should work (both output crm data)
        result = chain_skills(
            "hubspot-companies --limit 1 | demo-echo",
            validate=False  # Types don't match, but we can still run
        )
        assert result.success
