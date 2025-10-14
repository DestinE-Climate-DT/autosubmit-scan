"""Unit tests for report aggregator.

Tests for loading, grouping, and calculating statistics on error matches.
"""

import json
from datetime import datetime

import pytest

from src.domain.models import ErrorMatch


@pytest.fixture
def sample_matches():
    """Sample error matches for testing."""
    now = datetime.now()
    return [
        ErrorMatch(
            error_id="slurm_oom",
            file_uri="s3://bucket/logs/job123.log",
            line_number=42,
            matched_text="Out of memory on node001",
            context_before=["Starting job", "Allocating resources"],
            context_after=["Job terminated"],
            timestamp=now,
            metadata={"host": "node001", "job_id": "123"},
        ),
        ErrorMatch(
            error_id="slurm_oom",
            file_uri="s3://bucket/logs/job124.log",
            line_number=56,
            matched_text="Out of memory on node002",
            context_before=["Starting job"],
            context_after=["Error handler triggered"],
            timestamp=now,
            metadata={"host": "node002", "job_id": "124"},
        ),
        ErrorMatch(
            error_id="slurm_timeout",
            file_uri="s3://bucket/logs/job125.log",
            line_number=100,
            matched_text="TIMEOUT reached",
            context_before=["Processing data"],
            context_after=["Job cancelled"],
            timestamp=now,
            metadata={"host": "node003", "job_id": "125"},
        ),
    ]


@pytest.fixture
def temp_match_files(tmp_path, sample_matches):
    """Create temporary JSON files with error matches."""
    files = []

    # Split matches into separate files
    for i, match in enumerate(sample_matches):
        file_path = tmp_path / f"matches_{i}.json"
        match_data = match.model_dump(mode="json")
        with open(file_path, "w") as f:
            json.dump(match_data, f)
        files.append(str(file_path))

    return files


class TestLoadMatchesFromFiles:
    """Test loading matches from JSON files."""

    def test_load_single_file(self, temp_match_files, sample_matches):
        """Test loading a single match file."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        matches = aggregator.load_matches_from_files([temp_match_files[0]])

        assert len(matches) == 1
        assert matches[0].error_id == sample_matches[0].error_id
        assert matches[0].file_uri == sample_matches[0].file_uri
        assert matches[0].line_number == sample_matches[0].line_number

    def test_load_multiple_files(self, temp_match_files, sample_matches):
        """Test loading multiple match files."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        matches = aggregator.load_matches_from_files(temp_match_files)

        assert len(matches) == 3
        assert all(isinstance(m, ErrorMatch) for m in matches)

    def test_load_empty_file_list(self):
        """Test loading with empty file list."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        matches = aggregator.load_matches_from_files([])

        assert matches == []

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file raises error."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        with pytest.raises(FileNotFoundError):
            aggregator.load_matches_from_files(["/nonexistent/file.json"])

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises error."""
        from src.reporting.aggregator import ReportAggregator

        # Create file with invalid JSON
        file_path = tmp_path / "invalid.json"
        with open(file_path, "w") as f:
            f.write("{invalid json")

        aggregator = ReportAggregator()
        with pytest.raises(json.JSONDecodeError):
            aggregator.load_matches_from_files([str(file_path)])

    def test_load_preserves_datetime(self, temp_match_files):
        """Test that datetime fields are preserved correctly."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        matches = aggregator.load_matches_from_files([temp_match_files[0]])

        assert isinstance(matches[0].timestamp, datetime)


class TestGroupByError:
    """Test grouping matches by error type."""

    def test_group_by_error_basic(self, sample_matches):
        """Test basic error grouping."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        grouped = aggregator.group_by_error(sample_matches)

        assert "slurm_oom" in grouped
        assert "slurm_timeout" in grouped
        assert len(grouped["slurm_oom"]) == 2
        assert len(grouped["slurm_timeout"]) == 1

    def test_group_by_error_empty(self):
        """Test grouping empty list."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        grouped = aggregator.group_by_error([])

        assert grouped == {}

    def test_group_by_error_single_type(self):
        """Test grouping with single error type."""
        from src.reporting.aggregator import ReportAggregator

        now = datetime.now()
        matches = [
            ErrorMatch(
                error_id="error1",
                file_uri="/tmp/file1.log",
                line_number=1,
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={},
            ),
            ErrorMatch(
                error_id="error1",
                file_uri="/tmp/file2.log",
                line_number=2,
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={},
            ),
        ]

        aggregator = ReportAggregator()
        grouped = aggregator.group_by_error(matches)

        assert len(grouped) == 1
        assert "error1" in grouped
        assert len(grouped["error1"]) == 2


class TestGroupByFile:
    """Test grouping matches by file."""

    def test_group_by_file_basic(self, sample_matches):
        """Test basic file grouping."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        grouped = aggregator.group_by_file(sample_matches)

        assert len(grouped) == 3
        assert "s3://bucket/logs/job123.log" in grouped
        assert "s3://bucket/logs/job124.log" in grouped
        assert "s3://bucket/logs/job125.log" in grouped

    def test_group_by_file_multiple_matches_per_file(self):
        """Test grouping when multiple matches occur in same file."""
        from src.reporting.aggregator import ReportAggregator

        now = datetime.now()
        matches = [
            ErrorMatch(
                error_id="error1",
                file_uri="/tmp/file1.log",
                line_number=10,
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={},
            ),
            ErrorMatch(
                error_id="error2",
                file_uri="/tmp/file1.log",
                line_number=20,
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={},
            ),
            ErrorMatch(
                error_id="error1",
                file_uri="/tmp/file1.log",
                line_number=15,
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={},
            ),
        ]

        aggregator = ReportAggregator()
        grouped = aggregator.group_by_file(matches)

        assert len(grouped) == 1
        assert "/tmp/file1.log" in grouped
        assert len(grouped["/tmp/file1.log"]) == 3

    def test_group_by_file_sorts_by_line_number(self):
        """Test that matches within a file are sorted by line number."""
        from src.reporting.aggregator import ReportAggregator

        now = datetime.now()
        matches = [
            ErrorMatch(
                error_id="error1",
                file_uri="/tmp/file1.log",
                line_number=30,
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={},
            ),
            ErrorMatch(
                error_id="error2",
                file_uri="/tmp/file1.log",
                line_number=10,
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={},
            ),
            ErrorMatch(
                error_id="error3",
                file_uri="/tmp/file1.log",
                line_number=20,
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={},
            ),
        ]

        aggregator = ReportAggregator()
        grouped = aggregator.group_by_file(matches)

        line_numbers = [m.line_number for m in grouped["/tmp/file1.log"]]
        assert line_numbers == [10, 20, 30]

    def test_group_by_file_empty(self):
        """Test grouping empty list by file."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        grouped = aggregator.group_by_file([])

        assert grouped == {}


class TestCalculateStatistics:
    """Test statistics calculation."""

    def test_calculate_basic_statistics(self, sample_matches):
        """Test basic statistics calculation."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        stats = aggregator.calculate_statistics(sample_matches)

        assert stats["total_matches"] == 3
        assert stats["unique_errors"] == 2
        assert stats["unique_files"] == 3
        assert stats["unique_hosts"] == 3

    def test_calculate_statistics_with_errors_by_type(self, sample_matches):
        """Test that statistics include error counts by type."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        stats = aggregator.calculate_statistics(sample_matches)

        assert "errors_by_type" in stats
        assert stats["errors_by_type"]["slurm_oom"] == 2
        assert stats["errors_by_type"]["slurm_timeout"] == 1

    def test_calculate_statistics_with_files_by_error(self, sample_matches):
        """Test that statistics include files affected by each error."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        stats = aggregator.calculate_statistics(sample_matches)

        assert "files_by_error" in stats
        assert len(stats["files_by_error"]["slurm_oom"]) == 2
        assert len(stats["files_by_error"]["slurm_timeout"]) == 1

    def test_calculate_statistics_empty(self):
        """Test statistics calculation with empty list."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()
        stats = aggregator.calculate_statistics([])

        assert stats["total_matches"] == 0
        assert stats["unique_errors"] == 0
        assert stats["unique_files"] == 0
        assert stats["unique_hosts"] == 0
        assert stats["errors_by_type"] == {}
        assert stats["files_by_error"] == {}

    def test_calculate_statistics_without_host_metadata(self):
        """Test statistics when matches don't have host metadata."""
        from src.reporting.aggregator import ReportAggregator

        now = datetime.now()
        matches = [
            ErrorMatch(
                error_id="error1",
                file_uri="/tmp/file1.log",
                line_number=1,
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={},  # No host
            )
        ]

        aggregator = ReportAggregator()
        stats = aggregator.calculate_statistics(matches)

        assert stats["unique_hosts"] == 0


class TestAggregatorIntegration:
    """Integration tests for aggregator."""

    def test_load_and_group_workflow(self, temp_match_files):
        """Test complete workflow: load files, group, calculate stats."""
        from src.reporting.aggregator import ReportAggregator

        aggregator = ReportAggregator()

        # Load matches
        matches = aggregator.load_matches_from_files(temp_match_files)
        assert len(matches) == 3

        # Group by error
        error_groups = aggregator.group_by_error(matches)
        assert len(error_groups) == 2

        # Group by file
        file_groups = aggregator.group_by_file(matches)
        assert len(file_groups) == 3

        # Calculate statistics
        stats = aggregator.calculate_statistics(matches)
        assert stats["total_matches"] == 3
        assert stats["unique_errors"] == 2

    def test_load_from_directory_pattern(self, tmp_path, sample_matches):
        """Test loading matches from files matching a pattern."""
        import glob

        from src.reporting.aggregator import ReportAggregator

        # Create multiple match files
        for i, match in enumerate(sample_matches):
            file_path = tmp_path / f"match_{i}.json"
            match_data = match.model_dump(mode="json")
            with open(file_path, "w") as f:
                json.dump(match_data, f)

        # Use glob to find all match files
        pattern = str(tmp_path / "match_*.json")
        match_files = glob.glob(pattern)

        aggregator = ReportAggregator()
        matches = aggregator.load_matches_from_files(match_files)

        assert len(matches) == 3


@pytest.mark.unit
class TestAggregatorEdgeCases:
    """Test edge cases for aggregator."""

    def test_large_match_list(self):
        """Test handling large number of matches."""
        from src.reporting.aggregator import ReportAggregator

        now = datetime.now()
        matches = [
            ErrorMatch(
                error_id=f"error_{i % 10}",
                file_uri=f"/tmp/file_{i % 5}.log",
                line_number=i + 1,  # Line numbers must be >= 1
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={"host": f"node{i % 3}"},
            )
            for i in range(1000)
        ]

        aggregator = ReportAggregator()

        # Should handle large lists without issues
        error_groups = aggregator.group_by_error(matches)
        assert len(error_groups) == 10

        file_groups = aggregator.group_by_file(matches)
        assert len(file_groups) == 5

        stats = aggregator.calculate_statistics(matches)
        assert stats["total_matches"] == 1000

    def test_unicode_in_matches(self, tmp_path):
        """Test handling unicode characters in match data."""
        from src.reporting.aggregator import ReportAggregator

        now = datetime.now()
        match = ErrorMatch(
            error_id="unicode_error",
            file_uri="s3://bucket/logs/日本語.log",
            line_number=1,
            matched_text="Error: 文字化け",
            context_before=["Context: 前"],
            context_after=["Context: 後"],
            timestamp=now,
            metadata={"description": "Unicode test: 日本語"},
        )

        # Save to file
        file_path = tmp_path / "unicode_match.json"
        match_data = match.model_dump(mode="json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(match_data, f, ensure_ascii=False)

        # Load and verify
        aggregator = ReportAggregator()
        matches = aggregator.load_matches_from_files([str(file_path)])

        assert len(matches) == 1
        assert matches[0].file_uri == "s3://bucket/logs/日本語.log"
        assert matches[0].matched_text == "Error: 文字化け"

    def test_duplicate_matches(self):
        """Test handling duplicate matches."""
        from src.reporting.aggregator import ReportAggregator

        now = datetime.now()
        # Create identical matches
        matches = [
            ErrorMatch(
                error_id="error1",
                file_uri="/tmp/file1.log",
                line_number=1,
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={},
            ),
            ErrorMatch(
                error_id="error1",
                file_uri="/tmp/file1.log",
                line_number=1,
                matched_text="error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={},
            ),
        ]

        aggregator = ReportAggregator()
        stats = aggregator.calculate_statistics(matches)

        # Should count duplicates
        assert stats["total_matches"] == 2
