"""Integration tests for Snakemake workflow.

Tests the workflow components:
- File discovery checkpoint
- Fingerprinting checkpoint
- Pattern matching rule
- Match filtering checkpoint
- Context extraction rule
- Result aggregation rule
- End-to-end workflow execution
"""

import json
from datetime import datetime

from src.domain.models import ErrorCatalog, ErrorDefinition, PatternMatcher, PatternType
from src.orchestration.helpers import (
    expand_fsspec_patterns,
    get_error_definition,
    get_file_hash,
    get_fingerprint,
    read_manifest,
    write_manifest,
)
from src.orchestration.scanners import (
    extract_matches_with_context,
    scan_file_for_pattern,
)


class TestFileDiscovery:
    """Tests for file discovery checkpoint logic."""

    def test_discover_files_creates_manifest(self, tmp_path):
        """Should create manifest file with discovered file URIs."""
        # Create test files
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "file1.log").write_text("content1")
        (log_dir / "file2.log").write_text("content2")

        # Create error definition
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(log_dir / "*.log")],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Simulate discovery checkpoint
        discovered = expand_fsspec_patterns(error_def.files)

        # Write manifest (what the checkpoint would do)
        manifest_file = tmp_path / "manifest.txt"
        write_manifest(str(manifest_file), discovered)

        # Verify manifest was created
        assert manifest_file.exists()

        # Verify content
        uris = read_manifest(str(manifest_file))
        assert len(uris) == 2
        assert str(log_dir / "file1.log") in uris
        assert str(log_dir / "file2.log") in uris

    def test_discover_files_handles_recursive_patterns(self, tmp_path):
        """Should discover files in nested directories."""
        # Create nested structure
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir1" / "file1.log").write_text("content1")
        (tmp_path / "dir2").mkdir()
        (tmp_path / "dir2" / "file2.log").write_text("content2")

        # Create error definition with recursive pattern
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(tmp_path / "**/*.log")],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Discover files
        discovered = expand_fsspec_patterns(error_def.files)

        # Should find both files
        assert len(discovered) == 2


class TestFingerprinting:
    """Tests for file fingerprinting checkpoint logic."""

    def test_fingerprint_file_creates_json(self, tmp_path):
        """Should create fingerprint JSON for a file."""
        # Create test file
        test_file = tmp_path / "test.log"
        test_file.write_text("test content\n")

        # Get fingerprint
        fingerprint = get_fingerprint(str(test_file))

        # Write fingerprint JSON (what the checkpoint would do)
        fp_dir = tmp_path / "fingerprints"
        fp_dir.mkdir()
        file_hash = get_file_hash(str(test_file))
        fp_file = fp_dir / f"{file_hash}.json"

        with open(fp_file, "w") as f:
            json.dump(fingerprint, f, indent=2)

        # Verify file was created
        assert fp_file.exists()

        # Verify content
        with open(fp_file) as f:
            loaded_fp = json.load(f)

        assert loaded_fp["uri"] == str(test_file)
        assert loaded_fp["size"] == len(b"test content\n")
        assert "mtime" in loaded_fp
        assert "checksum" in loaded_fp


class TestPatternMatching:
    """Tests for pattern matching rule logic."""

    def test_match_pattern_finds_matches(self, tmp_path):
        """Should find pattern matches and save line numbers."""
        # Create test file
        test_file = tmp_path / "test.log"
        test_file.write_text("Line 1: normal\nLine 2: ERROR\nLine 3: normal\nLine 4: ERROR\n")

        # Create error definition
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Scan for matches
        line_numbers = scan_file_for_pattern(str(test_file), error_def.pattern)

        # Save match data (what the rule would do)
        match_data = {"file_uri": str(test_file), "error_id": "test_error", "match_line_numbers": line_numbers}

        matches_dir = tmp_path / "matches"
        matches_dir.mkdir()
        file_hash = get_file_hash(str(test_file))
        match_file = matches_dir / f"{file_hash}.json"

        with open(match_file, "w") as f:
            json.dump(match_data, f, indent=2)

        # Verify match file was created
        assert match_file.exists()

        # Verify content
        with open(match_file) as f:
            loaded_data = json.load(f)

        assert loaded_data["match_line_numbers"] == [2, 4]

    def test_match_pattern_handles_no_matches(self, tmp_path):
        """Should create match file with empty list when no matches."""
        # Create test file with no errors
        test_file = tmp_path / "test.log"
        test_file.write_text("Line 1: normal\nLine 2: normal\n")

        # Create error definition
        error_def = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=[str(test_file)],
            meaning="Test error",
            context_lines=2,
            suggestion="Fix it",
        )

        # Scan for matches
        line_numbers = scan_file_for_pattern(str(test_file), error_def.pattern)

        # Should be empty
        assert line_numbers == []


class TestMatchFiltering:
    """Tests for match filtering checkpoint logic (funneling)."""

    def test_filter_matches_creates_filtered_list(self, tmp_path):
        """Should create list of only files with matches."""
        # Create match files (some with matches, some without)
        matches_dir = tmp_path / "matches"
        matches_dir.mkdir()

        # File 1: has matches
        match_data_1 = {"file_uri": "/path/file1.log", "error_id": "test_error", "match_line_numbers": [2, 4]}
        with open(matches_dir / "hash1.json", "w") as f:
            json.dump(match_data_1, f)

        # File 2: no matches
        match_data_2 = {"file_uri": "/path/file2.log", "error_id": "test_error", "match_line_numbers": []}
        with open(matches_dir / "hash2.json", "w") as f:
            json.dump(match_data_2, f)

        # File 3: has matches
        match_data_3 = {"file_uri": "/path/file3.log", "error_id": "test_error", "match_line_numbers": [1]}
        with open(matches_dir / "hash3.json", "w") as f:
            json.dump(match_data_3, f)

        # Filter matches (what the checkpoint would do)
        files_with_matches = []

        for match_file in matches_dir.glob("*.json"):
            with open(match_file) as f:
                match_data = json.load(f)

            if match_data["match_line_numbers"]:
                files_with_matches.append(match_data["file_uri"])

        # Write filtered manifest
        filtered_file = tmp_path / "filtered.txt"
        write_manifest(str(filtered_file), files_with_matches)

        # Verify filtered list
        filtered_uris = read_manifest(str(filtered_file))
        assert len(filtered_uris) == 2
        assert "/path/file1.log" in filtered_uris
        assert "/path/file3.log" in filtered_uris
        assert "/path/file2.log" not in filtered_uris


class TestContextExtraction:
    """Tests for context extraction rule logic."""

    def test_extract_context_creates_result(self, tmp_path):
        """Should extract context and create result JSON."""
        # Create test file
        test_file = tmp_path / "test.log"
        test_file.write_text("Line 1: context\nLine 2: ERROR\nLine 3: context\n")

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
        line_numbers = [2]
        matches = extract_matches_with_context(str(test_file), line_numbers, error_def)

        # Save results (what the rule would do)
        matches_json = [match.model_dump(mode="json") for match in matches]

        results_dir = tmp_path / "results"
        results_dir.mkdir()
        result_file = results_dir / "result.json"

        with open(result_file, "w") as f:
            json.dump(matches_json, f, indent=2)

        # Verify result file
        assert result_file.exists()

        # Verify content
        with open(result_file) as f:
            loaded_matches = json.load(f)

        assert len(loaded_matches) == 1
        assert loaded_matches[0]["line_number"] == 2
        assert "ERROR" in loaded_matches[0]["matched_text"]


class TestResultAggregation:
    """Tests for result aggregation rule logic."""

    def test_aggregate_results_combines_matches(self, tmp_path):
        """Should combine all match results into single file."""
        # Create multiple result files
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        # Result 1
        matches_1 = [
            {"error_id": "test_error", "line_number": 2},
            {"error_id": "test_error", "line_number": 4},
        ]
        with open(results_dir / "result1.json", "w") as f:
            json.dump(matches_1, f)

        # Result 2
        matches_2 = [
            {"error_id": "test_error", "line_number": 1},
        ]
        with open(results_dir / "result2.json", "w") as f:
            json.dump(matches_2, f)

        # Aggregate (what the rule would do)
        all_matches = []

        for result_file in results_dir.glob("*.json"):
            with open(result_file) as f:
                file_matches = json.load(f)
            all_matches.extend(file_matches)

        # Write aggregated result
        aggregated_file = tmp_path / "aggregated.json"
        with open(aggregated_file, "w") as f:
            json.dump(all_matches, f, indent=2)

        # Verify aggregation
        with open(aggregated_file) as f:
            loaded_matches = json.load(f)

        assert len(loaded_matches) == 3


class TestEndToEndWorkflow:
    """End-to-end workflow tests with sample catalog."""

    def test_workflow_components_integrate(self, tmp_path):
        """Should run all workflow components in sequence."""
        # Setup: Create test files
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        (log_dir / "job1.log").write_text("Starting job\nERROR: Out of memory\nJob failed\n")

        (log_dir / "job2.log").write_text("Starting job\nJob completed successfully\n")

        (log_dir / "job3.log").write_text("Starting job\nERROR: Disk full\nJob failed\n")

        # Create simple catalog
        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata={
                "name": "Test Catalog",
                "description": "Test",
                "author": "Test",
                "created": datetime.now(),
                "updated": datetime.now(),
            },
            errors={
                "test_error": ErrorDefinition(
                    id="test_error",
                    pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
                    files=[str(log_dir / "*.log")],
                    meaning="Test error",
                    context_lines=1,
                    suggestion="Fix it",
                ),
            },
        )

        # Step 1: File Discovery
        error_def = get_error_definition(catalog, "test_error")
        discovered_files = expand_fsspec_patterns(error_def.files)

        assert len(discovered_files) == 3

        # Step 2: Pattern Matching
        matches_by_file = {}
        for file_uri in discovered_files:
            line_numbers = scan_file_for_pattern(file_uri, error_def.pattern)
            if line_numbers:
                matches_by_file[file_uri] = line_numbers

        # Should find matches in job1 and job3
        assert len(matches_by_file) == 2

        # Step 3: Context Extraction
        all_matches = []
        for file_uri, line_numbers in matches_by_file.items():
            matches = extract_matches_with_context(file_uri, line_numbers, error_def)
            all_matches.extend(matches)

        # Should have 2 total matches
        assert len(all_matches) == 2

        # Verify match details
        assert all(match.error_id == "test_error" for match in all_matches)
        assert all("ERROR" in match.matched_text for match in all_matches)
        assert all(len(match.context_before) == 1 for match in all_matches)
        assert all(len(match.context_after) == 1 for match in all_matches)
