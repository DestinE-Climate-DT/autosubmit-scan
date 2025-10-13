"""Unit tests for context extraction.

Tests for:
- ContextExtractor: Extracting lines before/after a match
- ContextResult: Data structure for context
- Edge cases (beginning/end of file, single line, etc.)
"""

import tempfile
from pathlib import Path

import pytest

from src.matching.context_extractor import ContextExtractor, ContextResult


class TestContextExtractor:
    """Test context extraction functionality."""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file with test content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("Line 1\n")
            f.write("Line 2\n")
            f.write("Line 3\n")
            f.write("Line 4\n")
            f.write("Line 5\n")
            f.write("Line 6\n")
            f.write("Line 7\n")
            f.write("Line 8\n")
            f.write("Line 9\n")
            f.write("Line 10\n")
            temp_path = f.name

        yield temp_path

        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def single_line_file(self):
        """Create a single-line file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("Only line")
            temp_path = f.name

        yield temp_path

        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def three_line_file(self):
        """Create a three-line file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("First\n")
            f.write("Second\n")
            f.write("Third\n")
            temp_path = f.name

        yield temp_path

        Path(temp_path).unlink(missing_ok=True)

    def test_extract_context_middle(self, temp_file):
        """Test extracting context from middle of file."""
        extractor = ContextExtractor()
        result = extractor.extract_context(temp_file, line_number=5, context_lines=2)

        assert result.line_number == 5
        assert result.matched_line == "Line 5\n"
        assert result.before == ["Line 3\n", "Line 4\n"]
        assert result.after == ["Line 6\n", "Line 7\n"]

    def test_extract_context_beginning(self, temp_file):
        """Test extracting context near start of file."""
        extractor = ContextExtractor()
        result = extractor.extract_context(temp_file, line_number=2, context_lines=3)

        assert result.line_number == 2
        assert result.matched_line == "Line 2\n"
        # Can only get 1 line before (line 1)
        assert result.before == ["Line 1\n"]
        # Can get 3 lines after
        assert result.after == ["Line 3\n", "Line 4\n", "Line 5\n"]

    def test_extract_context_first_line(self, temp_file):
        """Test extracting context from first line."""
        extractor = ContextExtractor()
        result = extractor.extract_context(temp_file, line_number=1, context_lines=2)

        assert result.line_number == 1
        assert result.matched_line == "Line 1\n"
        assert result.before == []
        assert result.after == ["Line 2\n", "Line 3\n"]

    def test_extract_context_end(self, temp_file):
        """Test extracting context near end of file."""
        extractor = ContextExtractor()
        result = extractor.extract_context(temp_file, line_number=9, context_lines=3)

        assert result.line_number == 9
        assert result.matched_line == "Line 9\n"
        # Can get 3 lines before
        assert result.before == ["Line 6\n", "Line 7\n", "Line 8\n"]
        # Can only get 1 line after (line 10)
        assert result.after == ["Line 10\n"]

    def test_extract_context_last_line(self, temp_file):
        """Test extracting context from last line."""
        extractor = ContextExtractor()
        result = extractor.extract_context(temp_file, line_number=10, context_lines=2)

        assert result.line_number == 10
        assert result.matched_line == "Line 10\n"
        assert result.before == ["Line 8\n", "Line 9\n"]
        assert result.after == []

    def test_context_lines_zero(self, temp_file):
        """Test with context_lines=0 (only matched line)."""
        extractor = ContextExtractor()
        result = extractor.extract_context(temp_file, line_number=5, context_lines=0)

        assert result.line_number == 5
        assert result.matched_line == "Line 5\n"
        assert result.before == []
        assert result.after == []

    def test_context_lines_one(self, temp_file):
        """Test with context_lines=1."""
        extractor = ContextExtractor()
        result = extractor.extract_context(temp_file, line_number=5, context_lines=1)

        assert result.line_number == 5
        assert result.matched_line == "Line 5\n"
        assert result.before == ["Line 4\n"]
        assert result.after == ["Line 6\n"]

    def test_context_lines_large(self, temp_file):
        """Test with large context_lines value."""
        extractor = ContextExtractor()
        result = extractor.extract_context(temp_file, line_number=5, context_lines=100)

        assert result.line_number == 5
        assert result.matched_line == "Line 5\n"
        # Should get all 4 lines before
        assert len(result.before) == 4
        # Should get all 5 lines after
        assert len(result.after) == 5

    def test_single_line_file(self, single_line_file):
        """Test extracting from single-line file."""
        extractor = ContextExtractor()
        result = extractor.extract_context(single_line_file, line_number=1, context_lines=5)

        assert result.line_number == 1
        assert result.matched_line == "Only line"
        assert result.before == []
        assert result.after == []

    def test_three_line_file_middle(self, three_line_file):
        """Test extracting from middle of small file."""
        extractor = ContextExtractor()
        result = extractor.extract_context(three_line_file, line_number=2, context_lines=1)

        assert result.line_number == 2
        assert result.matched_line == "Second\n"
        assert result.before == ["First\n"]
        assert result.after == ["Third\n"]

    def test_invalid_line_number_zero(self, temp_file):
        """Test error handling for line_number=0."""
        extractor = ContextExtractor()

        with pytest.raises(ValueError):
            extractor.extract_context(temp_file, line_number=0, context_lines=2)

    def test_invalid_line_number_negative(self, temp_file):
        """Test error handling for negative line_number."""
        extractor = ContextExtractor()

        with pytest.raises(ValueError):
            extractor.extract_context(temp_file, line_number=-5, context_lines=2)

    def test_invalid_context_lines_negative(self, temp_file):
        """Test error handling for negative context_lines."""
        extractor = ContextExtractor()

        with pytest.raises(ValueError):
            extractor.extract_context(temp_file, line_number=5, context_lines=-1)

    def test_line_number_beyond_file(self, temp_file):
        """Test error handling for line_number beyond file length."""
        extractor = ContextExtractor()

        with pytest.raises(ValueError):
            extractor.extract_context(temp_file, line_number=100, context_lines=2)

    def test_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        extractor = ContextExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.extract_context("/nonexistent/file.log", line_number=1, context_lines=2)

    def test_file_uri_format(self, temp_file):
        """Test that file:// URI works."""
        extractor = ContextExtractor()
        uri = f"file://{temp_file}"
        result = extractor.extract_context(uri, line_number=5, context_lines=2)

        assert result.line_number == 5
        assert result.matched_line == "Line 5\n"


class TestContextResult:
    """Test ContextResult data structure."""

    def test_context_result_creation(self):
        """Test creating ContextResult."""
        result = ContextResult(
            before=["Line 1\n", "Line 2\n"],
            matched_line="Line 3\n",
            after=["Line 4\n", "Line 5\n"],
            line_number=3
        )

        assert result.before == ["Line 1\n", "Line 2\n"]
        assert result.matched_line == "Line 3\n"
        assert result.after == ["Line 4\n", "Line 5\n"]
        assert result.line_number == 3

    def test_context_result_empty_context(self):
        """Test ContextResult with no context lines."""
        result = ContextResult(
            before=[],
            matched_line="Only line\n",
            after=[],
            line_number=1
        )

        assert result.before == []
        assert result.matched_line == "Only line\n"
        assert result.after == []
        assert result.line_number == 1

    def test_context_result_get_full_text(self):
        """Test getting full context as single text block."""
        result = ContextResult(
            before=["Line 1\n", "Line 2\n"],
            matched_line="Line 3\n",
            after=["Line 4\n", "Line 5\n"],
            line_number=3
        )

        full_text = result.get_full_text()
        expected = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
        assert full_text == expected

    def test_context_result_total_lines(self):
        """Test getting total number of context lines."""
        result = ContextResult(
            before=["Line 1\n", "Line 2\n"],
            matched_line="Line 3\n",
            after=["Line 4\n", "Line 5\n"],
            line_number=3
        )

        assert result.total_lines() == 5
