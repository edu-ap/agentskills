"""
Tests for skill composition.

These tests validate real composition scenarios ensuring the type-based
composition validation catches real issues.
"""

import pytest
from skill_catalog import (
    ATOMIC_SKILLS,
    COMPOSITE_SKILLS,
    ALL_SKILLS,
    get_skill,
    get_skills_by_output,
    get_skills_by_input,
    can_compose,
    validate_chain,
    SkillDefinition,
    COMPOSITION_TYPES,
)


class TestSkillDefinitions:
    """Test that skill definitions are complete and valid."""

    def test_all_skills_have_names(self):
        for name, skill in ALL_SKILLS.items():
            assert skill.name == name, f"Skill {name} has mismatched name"

    def test_all_skills_have_descriptions(self):
        for name, skill in ALL_SKILLS.items():
            assert skill.description, f"Skill {name} missing description"

    def test_readers_have_outputs(self):
        for name, skill in ATOMIC_SKILLS.items():
            if skill.operation == "READ":
                assert skill.outputs, f"Reader {name} should have outputs"

    def test_writers_have_inputs(self):
        for name, skill in ATOMIC_SKILLS.items():
            if skill.operation == "WRITE":
                assert skill.inputs, f"Writer {name} should have inputs"

    def test_composites_have_inputs(self):
        """Composite skills should declare what they consume."""
        for name, skill in COMPOSITE_SKILLS.items():
            assert skill.inputs, f"Composite {name} should have inputs"

    def test_all_types_are_documented(self):
        """All composition types used by skills should be documented."""
        used_types = set()
        for skill in ALL_SKILLS.values():
            used_types.update(skill.inputs)
            used_types.update(skill.outputs)

        undocumented = used_types - set(COMPOSITION_TYPES.keys())
        assert not undocumented, f"Undocumented types: {undocumented}"


class TestAtomicComposition:
    """Test atomic skill composition scenarios."""

    def test_email_read_to_customer_intel(self):
        valid, reason = can_compose("email-read", "customer-intel")
        assert valid is True
        assert "email-list" in reason

    def test_slack_read_to_customer_intel(self):
        valid, reason = can_compose("slack-read", "customer-intel")
        assert valid is True
        assert "message-list" in reason

    def test_hubspot_read_to_customer_intel(self):
        valid, reason = can_compose("hubspot-read", "customer-intel")
        assert valid is True
        assert "crm-" in reason  # crm-companies, crm-contacts, etc.

    def test_web_search_to_research(self):
        valid, reason = can_compose("web-search", "research")
        assert valid is True
        assert "search-results" in reason

    def test_email_read_cannot_feed_slack_write(self):
        """email-list is not message-content."""
        valid, reason = can_compose("email-read", "slack-write")
        assert valid is False
        assert "Type mismatch" in reason

    def test_hubspot_to_deal_loss_analysis(self):
        valid, reason = can_compose("hubspot-read", "deal-loss-analysis")
        assert valid is True


class TestCompositeComposition:
    """Test composite skill composition scenarios."""

    def test_customer_intel_output_type(self):
        skill = get_skill("customer-intel")
        assert "intel-brief" in skill.outputs

    def test_daily_synthesis_consumes_email_and_slack(self):
        skill = get_skill("daily-synthesis")
        assert "email-list" in skill.inputs
        assert "message-list" in skill.inputs

    def test_meeting_prep_consumes_calendar(self):
        skill = get_skill("meeting-prep")
        assert "calendar-events" in skill.inputs


class TestChainValidation:
    """Test multi-step composition chains."""

    def test_simple_two_step_chain(self):
        valid, messages = validate_chain(["email-read", "customer-intel"])
        assert valid is True
        assert len(messages) == 1
        assert "✓" in messages[0]

    def test_parallel_readers_to_composite(self):
        """All three readers should feed into customer-intel."""
        chains = [
            ["email-read", "customer-intel"],
            ["slack-read", "customer-intel"],
            ["hubspot-read", "customer-intel"],
        ]
        for chain in chains:
            valid, _ = validate_chain(chain)
            assert valid is True, f"Chain {chain} should be valid"

    def test_invalid_chain_detected(self):
        """email-read output can't feed slack-write input."""
        valid, messages = validate_chain(["email-read", "slack-write"])
        assert valid is False
        assert "✗" in messages[0]

    def test_longer_chain_with_failure(self):
        """Chain fails at specific point."""
        valid, messages = validate_chain(
            ["email-read", "customer-intel", "morning-briefing"]
        )
        assert valid is False
        # First step succeeds
        assert "✓" in messages[0]
        # Second step fails (intel-brief not in morning-briefing inputs)
        assert "✗" in messages[1]


class TestTypeDiscovery:
    """Test finding skills by type."""

    def test_find_email_list_producers(self):
        producers = get_skills_by_output("email-list")
        names = [s.name for s in producers]
        assert "email-read" in names

    def test_find_email_list_consumers(self):
        consumers = get_skills_by_input("email-list")
        names = [s.name for s in consumers]
        assert "customer-intel" in names
        assert "daily-synthesis" in names
        assert "meeting-prep" in names

    def test_find_message_list_flow(self):
        """slack-read produces what customer-intel consumes."""
        producers = get_skills_by_output("message-list")
        consumers = get_skills_by_input("message-list")

        producer_names = {s.name for s in producers}
        consumer_names = {s.name for s in consumers}

        assert "slack-read" in producer_names
        assert "customer-intel" in consumer_names


class TestFrontmatterGeneration:
    """Test SKILL.md frontmatter generation."""

    def test_generate_email_read_frontmatter(self):
        skill = get_skill("email-read")
        frontmatter = skill.to_frontmatter()

        assert "---" in frontmatter
        assert "name: email-read" in frontmatter
        assert "outputs:" in frontmatter
        assert "- email-list" in frontmatter
        # Readers have no inputs
        assert "inputs:" not in frontmatter

    def test_generate_customer_intel_frontmatter(self):
        skill = get_skill("customer-intel")
        frontmatter = skill.to_frontmatter()

        assert "name: customer-intel" in frontmatter
        assert "inputs:" in frontmatter
        assert "- email-list" in frontmatter
        assert "- message-list" in frontmatter
        assert "- crm-companies" in frontmatter  # CRM types are now specific
        assert "outputs:" in frontmatter
        assert "- intel-brief" in frontmatter


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_customer_briefing_workflow(self):
        """
        Real scenario: Prepare customer briefing.

        Data flows:
        - hubspot-read → crm-data
        - slack-read → message-list
        - email-read → email-list
        All feed into customer-intel → intel-brief
        """
        # Each atomic reader can feed customer-intel
        for reader in ["hubspot-read", "slack-read", "email-read"]:
            valid, _ = can_compose(reader, "customer-intel")
            assert valid is True

    def test_daily_synthesis_workflow(self):
        """
        Real scenario: Daily action item extraction.

        Data flows:
        - email-read → email-list → daily-synthesis
        - slack-read → message-list → daily-synthesis
        """
        valid1, _ = can_compose("email-read", "daily-synthesis")
        valid2, _ = can_compose("slack-read", "daily-synthesis")
        assert valid1 is True
        assert valid2 is True

    def test_research_workflow(self):
        """
        Real scenario: Research a topic.

        Data flows:
        - web-search → search-results → research → research-findings
        """
        valid, messages = validate_chain(["web-search", "research"])
        assert valid is True

    def test_email_reply_workflow(self):
        """
        Real scenario: Smart email reply.

        Data flows:
        - email-read → email-list → email-compose → draft-result
        """
        valid, messages = validate_chain(["email-read", "email-compose"])
        assert valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
