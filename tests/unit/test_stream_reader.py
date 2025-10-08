"""Unit tests for streaming file reader.

Tests for:
- FileStream: Opening files via fsspec
- Line-by-line iteration with line numbers
- Reading specific line ranges
- Edge cases (empty files, single lines, etc.)
- Memory efficiency
"""

import pytest
import tempfile
from pathlib import Path
from src.matching.stream_reader import FileStream


class TestFileStream:
    """Test file streaming functionality."""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file with test content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("Line 1: First line\n")
            f.write("Line 2: Second line\n")
            f.write("Line 3: Third line\n")
            f.write("Line 4: Fourth line\n")
            f.write("Line 5: Fifth line\n")
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def empty_file(self):
        """Create an empty temporary file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_path = f.name

        yield temp_path

        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def single_line_file(self):
        """Create a single-line file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("Only one line")
            temp_path = f.name

        yield temp_path

        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def large_file(self):
        """Create a large file for streaming tests."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            for i in range(10000):
                f.write(f"Line {i+1}: This is line number {i+1}\n")
            temp_path = f.name

        yield temp_path

        Path(temp_path).unlink(missing_ok=True)

    def test_open_local_file(self, temp_file):
        """Test opening a local file."""
        stream = FileStream.open_file(temp_file)
        assert stream is not None
        stream.close()

    def test_open_local_file_with_file_uri(self, temp_file):
        """Test opening with file:// URI."""
        uri = f"file://{temp_file}"
        stream = FileStream.open_file(uri)
        assert stream is not None
        stream.close()

    def test_stream_lines(self, temp_file):
        """Test line-by-line iteration."""
        stream = FileStream.open_file(temp_file)

        lines = list(stream.read_lines())

        assert len(lines) == 5
        assert lines[0] == (1, "Line 1: First line\n")
        assert lines[1] == (2, "Line 2: Second line\n")
        assert lines[2] == (3, "Line 3: Third line\n")
        assert lines[3] == (4, "Line 4: Fourth line\n")
        assert lines[4] == (5, "Line 5: Fifth line\n")

        stream.close()

    def test_line_numbers_start_at_1(self, temp_file):
        """Test that line numbers are 1-indexed."""
        stream = FileStream.open_file(temp_file)

        first_line = next(stream.read_lines())

        assert first_line[0] == 1
        assert first_line[1] == "Line 1: First line\n"

        stream.close()

    def test_read_lines_range(self, temp_file):
        """Test reading specific line range."""
        stream = FileStream.open_file(temp_file)

        # Read lines 2-4 (inclusive)
        lines = stream.read_lines_range(2, 4)

        assert len(lines) == 3
        assert lines[0] == "Line 2: Second line\n"
        assert lines[1] == "Line 3: Third line\n"
        assert lines[2] == "Line 4: Fourth line\n"

        stream.close()

    def test_read_lines_range_single_line(self, temp_file):
        """Test reading a single line via range."""
        stream = FileStream.open_file(temp_file)

        lines = stream.read_lines_range(3, 3)

        assert len(lines) == 1
        assert lines[0] == "Line 3: Third line\n"

        stream.close()

    def test_read_lines_range_beginning(self, temp_file):
        """Test reading from beginning of file."""
        stream = FileStream.open_file(temp_file)

        lines = stream.read_lines_range(1, 2)

        assert len(lines) == 2
        assert lines[0] == "Line 1: First line\n"
        assert lines[1] == "Line 2: Second line\n"

        stream.close()

    def test_read_lines_range_end(self, temp_file):
        """Test reading to end of file."""
        stream = FileStream.open_file(temp_file)

        lines = stream.read_lines_range(4, 5)

        assert len(lines) == 2
        assert lines[0] == "Line 4: Fourth line\n"
        assert lines[1] == "Line 5: Fifth line\n"

        stream.close()

    def test_read_lines_range_out_of_bounds(self, temp_file):
        """Test reading beyond file bounds."""
        stream = FileStream.open_file(temp_file)

        # Request lines beyond file length
        lines = stream.read_lines_range(4, 10)

        # Should only return lines 4-5
        assert len(lines) == 2
        assert lines[0] == "Line 4: Fourth line\n"
        assert lines[1] == "Line 5: Fifth line\n"

        stream.close()

    def test_empty_file(self, empty_file):
        """Test handling empty file."""
        stream = FileStream.open_file(empty_file)

        lines = list(stream.read_lines())

        assert lines == []

        stream.close()

    def test_single_line_file(self, single_line_file):
        """Test handling single-line file."""
        stream = FileStream.open_file(single_line_file)

        lines = list(stream.read_lines())

        assert len(lines) == 1
        assert lines[0] == (1, "Only one line")

        stream.close()

    def test_large_file_streaming(self, large_file):
        """Test that large files are streamed efficiently without loading all into memory."""
        stream = FileStream.open_file(large_file)

        # Read first 100 lines only
        count = 0
        for line_num, line_text in stream.read_lines():
            count += 1
            if count == 100:
                break

        assert count == 100

        stream.close()

    def test_context_manager(self, temp_file):
        """Test using FileStream as context manager."""
        with FileStream.open_file(temp_file) as stream:
            lines = list(stream.read_lines())
            assert len(lines) == 5

        # File should be closed after exiting context

    def test_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            FileStream.open_file("/nonexistent/path/to/file.log")

    def test_read_lines_range_invalid_bounds(self, temp_file):
        """Test error handling for invalid line range."""
        stream = FileStream.open_file(temp_file)

        # Start line > end line
        with pytest.raises(ValueError):
            stream.read_lines_range(5, 2)

        # Start line < 1
        with pytest.raises(ValueError):
            stream.read_lines_range(0, 3)

        stream.close()

    def test_iterator_can_be_reused(self, temp_file):
        """Test that we can iterate multiple times (file is reopened)."""
        stream = FileStream.open_file(temp_file)

        # First iteration
        lines1 = list(stream.read_lines())
        assert len(lines1) == 5

        # Second iteration (should work if file is reopened)
        lines2 = list(stream.read_lines())
        assert len(lines2) == 5
        assert lines1 == lines2

        stream.close()

    def test_strip_newlines_option(self, temp_file):
        """Test option to strip newlines from lines."""
        stream = FileStream.open_file(temp_file, strip_newlines=True)

        lines = list(stream.read_lines())

        assert lines[0] == (1, "Line 1: First line")
        assert lines[1] == (2, "Line 2: Second line")
        # No trailing newlines

        stream.close()
