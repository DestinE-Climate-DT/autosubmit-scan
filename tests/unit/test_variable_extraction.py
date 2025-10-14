"""Tests for variable extraction from files."""

from pathlib import Path

import pytest

from src.domain.models import VariableExtractor
from src.domain.variable_extractor import (
    _extract_line,
    _extract_with_regex,
    _extract_yaml_path,
    extract_catalog_variables,
    extract_variable,
)


class TestRegexExtraction:
    """Test regex-based variable extraction."""

    def test_extract_with_regex_first_group(self, tmp_path):
        """Test extracting first regex group."""
        test_file = tmp_path / "config.txt"
        test_file.write_text("hostname: lumi\nuser: testuser\n")

        extractor = VariableExtractor(path=str(test_file), method="regex", pattern=r"hostname:\s*(\S+)")

        value = extract_variable(extractor)
        assert value == "lumi"

    def test_extract_with_regex_named_group(self, tmp_path):
        """Test extracting named 'value' group."""
        test_file = tmp_path / "config.txt"
        test_file.write_text("host=mn5\n")

        extractor = VariableExtractor(path=str(test_file), method="regex", pattern=r"host=(?P<value>\S+)")

        value = extract_variable(extractor)
        assert value == "mn5"

    def test_extract_with_regex_no_match_uses_default(self, tmp_path):
        """Test that default is used when pattern doesn't match."""
        test_file = tmp_path / "config.txt"
        test_file.write_text("nothing here\n")

        extractor = VariableExtractor(path=str(test_file), method="regex", pattern=r"hostname:\s*(\S+)", default="localhost")

        value = extract_variable(extractor)
        assert value == "localhost"

    def test_extract_with_regex_strips_whitespace(self, tmp_path):
        """Test that whitespace is stripped by default."""
        test_file = tmp_path / "config.txt"
        test_file.write_text("host:   lumi   \n")

        extractor = VariableExtractor(path=str(test_file), method="regex", pattern=r"host:\s*(.+)")

        value = extract_variable(extractor)
        assert value == "lumi"

    def test_extract_with_regex_no_strip(self, tmp_path):
        """Test that whitespace is preserved when strip=False."""
        test_file = tmp_path / "config.txt"
        test_file.write_text("host:   lumi   \n")

        extractor = VariableExtractor(path=str(test_file), method="regex", pattern=r"host:\s*(.+)", strip=False)

        value = extract_variable(extractor)
        assert value == "lumi   "


class TestLineExtraction:
    """Test line-based variable extraction."""

    def test_extract_line_simple(self, tmp_path):
        """Test extracting a specific line."""
        test_file = tmp_path / "config.txt"
        test_file.write_text("line1\nlumi\nline3\n")

        extractor = VariableExtractor(path=str(test_file), method="line", line_number=2)

        value = extract_variable(extractor)
        assert value == "lumi"

    def test_extract_line_strips_whitespace(self, tmp_path):
        """Test that whitespace is stripped."""
        test_file = tmp_path / "config.txt"
        test_file.write_text("  lumi  \n")

        extractor = VariableExtractor(path=str(test_file), method="line", line_number=1)

        value = extract_variable(extractor)
        assert value == "lumi"

    def test_extract_line_out_of_range_uses_default(self, tmp_path):
        """Test that default is used when line is out of range."""
        test_file = tmp_path / "config.txt"
        test_file.write_text("line1\n")

        extractor = VariableExtractor(path=str(test_file), method="line", line_number=10, default="default")

        value = extract_variable(extractor)
        assert value == "default"


class TestYAMLPathExtraction:
    """Test YAML path-based variable extraction."""

    def test_extract_yaml_path_simple(self, tmp_path):
        """Test extracting from YAML with dot notation."""
        test_file = tmp_path / "config.yaml"
        test_file.write_text("config:\n  platforms:\n    host: lumi\n")

        extractor = VariableExtractor(path=str(test_file), method="yaml_path", pattern="config.platforms.host")

        value = extract_variable(extractor)
        assert value == "lumi"

    def test_extract_yaml_path_root_level(self, tmp_path):
        """Test extracting from YAML root level."""
        test_file = tmp_path / "config.yaml"
        test_file.write_text("host: mn5\n")

        extractor = VariableExtractor(path=str(test_file), method="yaml_path", pattern="host")

        value = extract_variable(extractor)
        assert value == "mn5"

    def test_extract_yaml_path_not_found_uses_default(self, tmp_path):
        """Test that default is used when path doesn't exist."""
        test_file = tmp_path / "config.yaml"
        test_file.write_text("other: value\n")

        extractor = VariableExtractor(path=str(test_file), method="yaml_path", pattern="missing.path", default="default")

        value = extract_variable(extractor)
        assert value == "default"


class TestFileNotFound:
    """Test behavior when file doesn't exist."""

    def test_file_not_found_uses_default(self, tmp_path):
        """Test that default is used when file doesn't exist."""
        extractor = VariableExtractor(
            path=str(tmp_path / "nonexistent.txt"), method="regex", pattern=r"host:\s*(\S+)", default="localhost"
        )

        value = extract_variable(extractor)
        assert value == "localhost"

    def test_file_not_found_raises_without_default(self, tmp_path):
        """Test that FileNotFoundError is raised without default."""
        extractor = VariableExtractor(path=str(tmp_path / "nonexistent.txt"), method="regex", pattern=r"host:\s*(\S+)")

        with pytest.raises(FileNotFoundError):
            extract_variable(extractor)


class TestCatalogVariablesExtraction:
    """Test extracting multiple variables for a catalog."""

    def test_extract_multiple_variables(self, tmp_path):
        """Test extracting multiple variables at once."""
        # Create test files
        host_file = tmp_path / "host.txt"
        host_file.write_text("host: lumi\n")

        user_file = tmp_path / "user.txt"
        user_file.write_text("testuser\n")

        extractors = {
            "host": VariableExtractor(path=str(host_file), method="regex", pattern=r"host:\s*(\S+)"),
            "user": VariableExtractor(path=str(user_file), method="line", line_number=1),
        }

        variables = extract_catalog_variables(extractors)

        assert variables == {"host": "lumi", "user": "testuser"}

    def test_extract_with_expanduser(self, tmp_path, monkeypatch):
        """Test that ~ is expanded in file paths."""
        # Create a file in tmp_path
        test_file = tmp_path / "config.txt"
        test_file.write_text("host: lumi\n")

        # Monkeypatch expanduser to return our test file
        def mock_expanduser(self):
            if str(self).startswith("~"):
                return test_file
            return self

        monkeypatch.setattr(Path, "expanduser", mock_expanduser)

        extractor = VariableExtractor(path="~/config.txt", method="regex", pattern=r"host:\s*(\S+)")

        value = extract_variable(extractor)
        assert value == "lumi"


class TestVariableExtractorValidation:
    """Test Pydantic validation of VariableExtractor."""

    def test_regex_requires_pattern(self):
        """Test that regex method requires pattern."""
        with pytest.raises(ValueError, match="'pattern' is required when method is 'regex'"):
            VariableExtractor(path="/tmp/file.txt", method="regex")

    def test_line_requires_line_number(self):
        """Test that line method requires line_number."""
        with pytest.raises(ValueError, match="'line_number' is required when method is 'line'"):
            VariableExtractor(path="/tmp/file.txt", method="line")

    def test_yaml_path_requires_pattern(self):
        """Test that yaml_path method requires pattern."""
        with pytest.raises(ValueError, match="'pattern' \\(YAML path\\) is required when method is 'yaml_path'"):
            VariableExtractor(path="/tmp/file.yaml", method="yaml_path")

    def test_invalid_method(self):
        """Test that invalid method is rejected."""
        with pytest.raises(ValueError, match="Invalid method"):
            VariableExtractor(path="/tmp/file.txt", method="invalid")
