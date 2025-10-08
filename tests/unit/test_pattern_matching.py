"""Unit tests for pattern matching functionality.

Tests for:
- LiteralPatternMatcher: Simple string matching
- RegexPatternMatcher: Regex with flags
- CallablePatternMatcher: Loading and executing callable patterns
- PatternMatcherFactory: Creating correct matcher types
"""

import re
import pytest
from src.matching.pattern_matcher import (
    PatternMatcherFactory,
    BasePatternMatcher,
    LiteralPatternMatcher,
    RegexPatternMatcher,
    CallablePatternMatcher,
)
from src.domain.models import PatternMatcher, PatternType


class TestLiteralPatternMatcher:
    """Test literal pattern matching."""

    def test_match_found(self):
        """Test that literal pattern matches when present."""
        pattern = PatternMatcher(type=PatternType.LITERAL, pattern="ERROR")
        matcher = LiteralPatternMatcher(pattern)

        assert matcher.match("ERROR: Out of memory") is True
        assert matcher.match("This is an ERROR message") is True

    def test_match_not_found(self):
        """Test that literal pattern does not match when absent."""
        pattern = PatternMatcher(type=PatternType.LITERAL, pattern="ERROR")
        matcher = LiteralPatternMatcher(pattern)

        assert matcher.match("Warning: low memory") is False
        assert matcher.match("Everything is fine") is False

    def test_case_sensitive(self):
        """Test that literal matching is case-sensitive by default."""
        pattern = PatternMatcher(type=PatternType.LITERAL, pattern="ERROR")
        matcher = LiteralPatternMatcher(pattern)

        assert matcher.match("ERROR") is True
        assert matcher.match("error") is False
        assert matcher.match("Error") is False

    def test_find_all_single_match(self):
        """Test finding single occurrence."""
        pattern = PatternMatcher(type=PatternType.LITERAL, pattern="ERROR")
        matcher = LiteralPatternMatcher(pattern)

        matches = matcher.find_all("ERROR: Out of memory")
        assert len(matches) == 1
        assert matches[0].start() == 0
        assert matches[0].end() == 5
        assert matches[0].group() == "ERROR"

    def test_find_all_multiple_matches(self):
        """Test finding multiple occurrences."""
        pattern = PatternMatcher(type=PatternType.LITERAL, pattern="ERROR")
        matcher = LiteralPatternMatcher(pattern)

        matches = matcher.find_all("ERROR: First ERROR and second ERROR")
        assert len(matches) == 3
        assert matches[0].group() == "ERROR"
        assert matches[1].group() == "ERROR"
        assert matches[2].group() == "ERROR"

    def test_find_all_no_match(self):
        """Test that find_all returns empty list when no matches."""
        pattern = PatternMatcher(type=PatternType.LITERAL, pattern="ERROR")
        matcher = LiteralPatternMatcher(pattern)

        matches = matcher.find_all("Everything is fine")
        assert matches == []


class TestRegexPatternMatcher:
    """Test regex pattern matching."""

    def test_simple_regex_match(self):
        """Test basic regex pattern matching."""
        pattern = PatternMatcher(type=PatternType.REGEX, pattern=r"ERROR:\s+\w+")
        matcher = RegexPatternMatcher(pattern)

        assert matcher.match("ERROR: OutOfMemory") is True
        assert matcher.match("ERROR:   TimeoutError") is True
        assert matcher.match("WARNING: Something") is False

    def test_regex_with_groups(self):
        """Test regex with capture groups."""
        pattern = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"Job (\d+) on node ([\w-]+)"
        )
        matcher = RegexPatternMatcher(pattern)

        matches = matcher.find_all("Job 12345 on node compute-01")
        assert len(matches) == 1
        assert matches[0].group(1) == "12345"
        assert matches[0].group(2) == "compute-01"

    def test_regex_flag_ignorecase(self):
        """Test IGNORECASE flag works."""
        pattern = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"error",
            flags=["IGNORECASE"]
        )
        matcher = RegexPatternMatcher(pattern)

        assert matcher.match("ERROR") is True
        assert matcher.match("error") is True
        assert matcher.match("Error") is True
        assert matcher.match("eRRoR") is True

    def test_regex_flag_multiline(self):
        """Test MULTILINE flag works."""
        pattern = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"^ERROR",
            flags=["MULTILINE"]
        )
        matcher = RegexPatternMatcher(pattern)

        text = "First line\nERROR: Second line\nThird line"
        assert matcher.match(text) is True

        matches = matcher.find_all(text)
        assert len(matches) == 1

    def test_regex_flag_dotall(self):
        """Test DOTALL flag allows . to match newlines."""
        pattern = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"ERROR.*failed",
            flags=["DOTALL"]
        )
        matcher = RegexPatternMatcher(pattern)

        text = "ERROR: Something\nwent wrong and\nfailed"
        assert matcher.match(text) is True

    def test_regex_multiple_flags(self):
        """Test combining multiple flags."""
        pattern = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"^error.*failed",
            flags=["IGNORECASE", "MULTILINE", "DOTALL"]
        )
        matcher = RegexPatternMatcher(pattern)

        text = "First line\nERROR: Something\nfailed"
        assert matcher.match(text) is True

    def test_regex_find_all_multiple(self):
        """Test finding all regex matches."""
        pattern = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"Job \d+"
        )
        matcher = RegexPatternMatcher(pattern)

        matches = matcher.find_all("Job 123 started, Job 456 finished")
        assert len(matches) == 2
        assert matches[0].group() == "Job 123"
        assert matches[1].group() == "Job 456"

    def test_regex_invalid_pattern(self):
        """Test that invalid regex raises error."""
        pattern = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"[invalid("
        )

        with pytest.raises(re.error):
            RegexPatternMatcher(pattern)


class TestCallablePatternMatcher:
    """Test callable pattern matching."""

    def test_callable_returns_bool_true(self):
        """Test callable that returns True."""
        pattern = PatternMatcher(
            type=PatternType.CALLABLE,
            pattern="tests.unit.test_pattern_matching:always_match"
        )
        matcher = CallablePatternMatcher(pattern)

        assert matcher.match("Any text") is True

    def test_callable_returns_bool_false(self):
        """Test callable that returns False."""
        pattern = PatternMatcher(
            type=PatternType.CALLABLE,
            pattern="tests.unit.test_pattern_matching:never_match"
        )
        matcher = CallablePatternMatcher(pattern)

        assert matcher.match("Any text") is False

    def test_callable_with_logic(self):
        """Test callable with actual matching logic."""
        pattern = PatternMatcher(
            type=PatternType.CALLABLE,
            pattern="tests.unit.test_pattern_matching:has_oom_pattern"
        )
        matcher = CallablePatternMatcher(pattern)

        assert matcher.match("slurmstepd: error: Detected 1 oom-kill event") is True
        assert matcher.match("Job completed successfully") is False

    def test_callable_invalid_module(self):
        """Test error handling for non-existent module."""
        pattern = PatternMatcher(
            type=PatternType.CALLABLE,
            pattern="nonexistent.module:function"
        )

        with pytest.raises(ImportError):
            CallablePatternMatcher(pattern)

    def test_callable_invalid_function(self):
        """Test error handling for non-existent function."""
        pattern = PatternMatcher(
            type=PatternType.CALLABLE,
            pattern="tests.unit.test_pattern_matching:nonexistent_function"
        )

        with pytest.raises(AttributeError):
            CallablePatternMatcher(pattern)

    def test_callable_find_all_not_supported(self):
        """Test that find_all raises NotImplementedError for bool-returning callables."""
        pattern = PatternMatcher(
            type=PatternType.CALLABLE,
            pattern="tests.unit.test_pattern_matching:always_match"
        )
        matcher = CallablePatternMatcher(pattern)

        # Bool-returning callables cannot provide match positions
        with pytest.raises(NotImplementedError):
            matcher.find_all("Any text")


class TestPatternMatcherFactory:
    """Test pattern matcher factory."""

    def test_create_literal_matcher(self):
        """Test factory creates LiteralPatternMatcher."""
        pattern = PatternMatcher(type=PatternType.LITERAL, pattern="ERROR")
        matcher = PatternMatcherFactory.create_matcher(pattern)

        assert isinstance(matcher, LiteralPatternMatcher)
        assert matcher.match("ERROR occurred") is True

    def test_create_regex_matcher(self):
        """Test factory creates RegexPatternMatcher."""
        pattern = PatternMatcher(type=PatternType.REGEX, pattern=r"\d+")
        matcher = PatternMatcherFactory.create_matcher(pattern)

        assert isinstance(matcher, RegexPatternMatcher)
        assert matcher.match("Job 12345") is True

    def test_create_callable_matcher(self):
        """Test factory creates CallablePatternMatcher."""
        pattern = PatternMatcher(
            type=PatternType.CALLABLE,
            pattern="tests.unit.test_pattern_matching:always_match"
        )
        matcher = PatternMatcherFactory.create_matcher(pattern)

        assert isinstance(matcher, CallablePatternMatcher)
        assert matcher.match("Anything") is True

    def test_factory_returns_base_matcher_type(self):
        """Test that all factory products are BasePatternMatcher instances."""
        patterns = [
            PatternMatcher(type=PatternType.LITERAL, pattern="test"),
            PatternMatcher(type=PatternType.REGEX, pattern=r"test"),
            PatternMatcher(
                type=PatternType.CALLABLE,
                pattern="tests.unit.test_pattern_matching:always_match"
            ),
        ]

        for pattern in patterns:
            matcher = PatternMatcherFactory.create_matcher(pattern)
            assert isinstance(matcher, BasePatternMatcher)


# Helper callable functions for testing
def always_match(text: str) -> bool:
    """Always returns True."""
    return True


def never_match(text: str) -> bool:
    """Always returns False."""
    return False


def has_oom_pattern(text: str) -> bool:
    """Check if text contains OOM kill pattern."""
    return "oom-kill" in text.lower()
