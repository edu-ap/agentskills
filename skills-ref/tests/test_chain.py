"""Tests for skill chaining functionality."""

import pytest
from skills_ref.runtime import parse_chain, chain_skills, ChainResult


class TestParseChain:
    """Tests for chain specification parsing."""

    def test_simple_chain(self):
        """Test parsing a simple two-skill chain."""
        result = parse_chain("skill-a | skill-b")
        assert result == [("skill-a", []), ("skill-b", [])]

    def test_chain_with_args(self):
        """Test parsing a chain with arguments."""
        result = parse_chain("skill-a --limit 10 | skill-b -v")
        assert result == [
            ("skill-a", ["--limit", "10"]),
            ("skill-b", ["-v"])
        ]

    def test_chain_with_quoted_args(self):
        """Test parsing a chain with quoted arguments."""
        result = parse_chain('skill-a --message "hello world" | skill-b')
        assert result == [
            ("skill-a", ["--message", "hello world"]),
            ("skill-b", [])
        ]

    def test_three_skill_chain(self):
        """Test parsing a three-skill chain."""
        result = parse_chain("a | b | c")
        assert result == [("a", []), ("b", []), ("c", [])]

    def test_empty_chain(self):
        """Test parsing an empty chain."""
        result = parse_chain("")
        assert result == []

    def test_whitespace_handling(self):
        """Test that extra whitespace is handled."""
        result = parse_chain("  skill-a   |   skill-b  ")
        assert result == [("skill-a", []), ("skill-b", [])]


class TestChainSkills:
    """Tests for chain execution."""

    def test_demo_echo_chain(self):
        """Test chaining demo-echo to itself."""
        result = chain_skills("demo-echo | demo-echo")
        assert result.success
        assert len(result.steps) == 2
        assert result.steps[0]["skill"] == "demo-echo"
        assert result.steps[1]["skill"] == "demo-echo"

    def test_single_skill_fails(self):
        """Test that single skill chain is rejected."""
        result = chain_skills("demo-echo")
        assert not result.success
        assert "at least 2 skills" in result.error

    def test_empty_chain_fails(self):
        """Test that empty chain is rejected."""
        result = chain_skills("")
        assert not result.success
        assert "Empty chain" in result.error

    def test_unknown_skill_fails(self):
        """Test that unknown skill is rejected."""
        result = chain_skills("demo-echo | nonexistent-skill")
        assert not result.success
        assert "Unknown skill" in result.error

    def test_no_validation_flag(self):
        """Test that validation can be skipped."""
        # demo-echo has no composition metadata, so this should pass
        result = chain_skills("demo-echo | demo-echo", validate=False)
        assert result.success

    def test_chain_result_structure(self):
        """Test ChainResult dataclass structure."""
        result = ChainResult(
            success=True,
            output={"key": "value"},
            steps=[{"skill": "test", "success": True}]
        )
        assert result.success
        assert result.output == {"key": "value"}
        assert len(result.steps) == 1
