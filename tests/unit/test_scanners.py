"""Unit tests for orchestration scanners.

Tests for:
- scan_file_for_pattern: Find match line numbers
- extract_matches_with_context: Extract ErrorMatch objects with context
"""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from src.orchestration.scanners import (
    scan_file_for_pattern,
    extract_matches_with_context,
)
from src.domain.models import (
    ErrorDefinition,
    PatternMatcher,
    PatternType,
    ErrorMatch,
)


class TestScanFileForPattern:
    """Tests for scan_file_for_pattern function."""

    def test_scan_literal_pattern_finds_matches(self, tmp_path):
        """Should find all lines matching literal pattern."""
        # Create test file
        test_file = tmp_path / "test.log"
        test_file.write_text(
            "Line 1: normal log\n"
            "Line 2: ERROR something bad\n"
            "Line 3: normal log\n"
            "Line 4: ERROR another issue\n"
            "Line 5: normal log\n"
        )

        # Create error definition with literal pattern
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Scan file
        line_numbers = scan_file_for_pattern(str(test_file), error_def.pattern)

        # Should find lines 2 and 4
        assert line_numbers == [2, 4]

    def test_scan_regex_pattern_finds_matches(self, tmp_path):
        """Should find all lines matching regex pattern."""
        test_file = tmp_path / "test.log"
        test_file.write_text(
            "Line 1: normal log\n"
            "Line 2: ERROR-001: something bad\n"
            "Line 3: normal log\n"
            "Line 4: ERROR-002: another issue\n"
            "Line 5: WARNING: not an error\n"
        )

        # Create error definition with regex pattern
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(
                type=PatternType.REGEX,
                pattern=r"ERROR-\d+:",
            ),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Scan file
        line_numbers = scan_file_for_pattern(str(test_file), error_def.pattern)

        # Should find lines 2 and 4
        assert line_numbers == [2, 4]

    def test_scan_case_insensitive_regex(self, tmp_path):
        """Should respect regex flags like IGNORECASE."""
        test_file = tmp_path / "test.log"
        test_file.write_text(
            "Line 1: error lowercase\n"
            "Line 2: ERROR uppercase\n"
            "Line 3: Error mixed case\n"
            "Line 4: normal log\n"
        )

        # Create error definition with case-insensitive regex
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(
                type=PatternType.REGEX,
                pattern=r"error",
                flags=["IGNORECASE"],
            ),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Scan file
        line_numbers = scan_file_for_pattern(str(test_file), error_def.pattern)

        # Should find lines 1, 2, and 3
        assert line_numbers == [1, 2, 3]

    def test_scan_no_matches_returns_empty_list(self, tmp_path):
        """Should return empty list when pattern doesn't match."""
        test_file = tmp_path / "test.log"
        test_file.write_text(
            "Line 1: normal log\n"
            "Line 2: normal log\n"
            "Line 3: normal log\n"
        )

        # Create error definition
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Scan file
        line_numbers = scan_file_for_pattern(str(test_file), error_def.pattern)

        # Should find no matches
        assert line_numbers == []

    def test_scan_multiple_matches_on_same_line(self, tmp_path):
        """Should report line only once even with multiple matches."""
        test_file = tmp_path / "test.log"
        test_file.write_text(
            "Line 1: ERROR ERROR ERROR multiple errors on one line\n"
            "Line 2: normal log\n"
        )

        # Create error definition
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Scan file
        line_numbers = scan_file_for_pattern(str(test_file), error_def.pattern)

        # Should report line 1 only once
        assert line_numbers == [1]


class TestExtractMatchesWithContext:
    """Tests for extract_matches_with_context function."""

    def test_extract_single_match_with_context(self, tmp_path):
        """Should extract match with before/after context."""
        test_file = tmp_path / "test.log"
        test_file.write_text(
            "Line 1: context before\n"
            "Line 2: more context\n"
            "Line 3: ERROR something bad\n"
            "Line 4: context after\n"
            "Line 5: more context\n"
        )

        # Create error definition
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Extract matches
        matches = extract_matches_with_context(
            str(test_file),
            [3],  # Line 3 has the match
            error_def,
        )

        # Should have one match
        assert len(matches) == 1

        match = matches[0]
        assert isinstance(match, ErrorMatch)
        assert match.error_id == "test_error"
        assert match.file_uri == str(test_file)
        assert match.line_number == 3
        assert "ERROR" in match.matched_text
        assert len(match.context_before) == 2
        assert len(match.context_after) == 2

    def test_extract_multiple_matches(self, tmp_path):
        """Should extract multiple matches with their contexts."""
        test_file = tmp_path / "test.log"
        test_file.write_text(
            "Line 1: context\n"
            "Line 2: ERROR first\n"
            "Line 3: context\n"
            "Line 4: ERROR second\n"
            "Line 5: context\n"
        )

        # Create error definition
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=1,
            suggestion="Fix it",
        )

        # Extract matches
        matches = extract_matches_with_context(
            str(test_file),
            [2, 4],
            error_def,
        )

        # Should have two matches
        assert len(matches) == 2

        assert matches[0].line_number == 2
        assert matches[1].line_number == 4

    def test_extract_match_at_file_start(self, tmp_path):
        """Should handle match at start of file (no context before)."""
        test_file = tmp_path / "test.log"
        test_file.write_text(
            "Line 1: ERROR at start\n"
            "Line 2: context after\n"
            "Line 3: more context\n"
        )

        # Create error definition
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Extract matches
        matches = extract_matches_with_context(str(test_file), [1], error_def)

        # Should have one match with no context before
        assert len(matches) == 1
        assert matches[0].line_number == 1
        assert len(matches[0].context_before) == 0
        assert len(matches[0].context_after) == 2

    def test_extract_match_at_file_end(self, tmp_path):
        """Should handle match at end of file (no context after)."""
        test_file = tmp_path / "test.log"
        test_file.write_text(
            "Line 1: context before\n"
            "Line 2: more context\n"
            "Line 3: ERROR at end\n"
        )

        # Create error definition
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Extract matches
        matches = extract_matches_with_context(str(test_file), [3], error_def)

        # Should have one match with no context after
        assert len(matches) == 1
        assert matches[0].line_number == 3
        assert len(matches[0].context_before) == 2
        assert len(matches[0].context_after) == 0

    def test_extract_with_zero_context(self, tmp_path):
        """Should extract match with zero context lines."""
        test_file = tmp_path / "test.log"
        test_file.write_text(
            "Line 1: context\n"
            "Line 2: ERROR in middle\n"
            "Line 3: context\n"
        )

        # Create error definition with zero context
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=0,
            suggestion="Fix it",
        )

        # Extract matches
        matches = extract_matches_with_context(str(test_file), [2], error_def)

        # Should have one match with no context
        assert len(matches) == 1
        assert matches[0].line_number == 2
        assert len(matches[0].context_before) == 0
        assert len(matches[0].context_after) == 0

    def test_extract_includes_metadata(self, tmp_path):
        """Should include error definition metadata in matches."""
        test_file = tmp_path / "test.log"
        test_file.write_text("Line 1: ERROR\n")

        # Create error definition with metadata
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=0,
            suggestion="Fix it",
            metadata={"severity": "high", "tags": ["important"]},
        )

        # Extract matches
        matches = extract_matches_with_context(str(test_file), [1], error_def)

        # Should include metadata
        assert len(matches) == 1
        assert matches[0].metadata["severity"] == "high"
        assert matches[0].metadata["tags"] == ["important"]

    def test_extract_match_has_timestamp(self, tmp_path):
        """Should add timestamp to each match."""
        test_file = tmp_path / "test.log"
        test_file.write_text("Line 1: ERROR\n")

        # Create error definition
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=0,
            suggestion="Fix it",
        )

        # Extract matches
        before_time = datetime.utcnow()
        matches = extract_matches_with_context(str(test_file), [1], error_def)
        after_time = datetime.utcnow()

        # Should have timestamp between before and after
        assert len(matches) == 1
        assert before_time <= matches[0].timestamp <= after_time
