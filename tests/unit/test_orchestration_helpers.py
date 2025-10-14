"""Unit tests for orchestration helper functions.

Tests for:
- get_file_hash: URI hashing for cache keys
- expand_fsspec_patterns: Glob pattern expansion
- get_fingerprint: File metadata extraction
- read_manifest: Manifest file parsing
- get_error_definition: Error definition lookup
"""

import hashlib
from datetime import datetime
from pathlib import Path

import pytest

from src.domain.models import ErrorCatalog, ErrorDefinition, PatternMatcher, PatternType
from src.orchestration.helpers import (
    expand_fsspec_patterns,
    get_error_definition,
    get_file_hash,
    get_fingerprint,
    read_manifest,
    write_manifest,
)


class TestGetFileHash:
    """Tests for get_file_hash function."""

    def test_hash_same_uri_produces_same_hash(self):
        """Same URI should always produce the same hash."""
        uri = "s3://bucket/path/file.log"
        hash1 = get_file_hash(uri)
        hash2 = get_file_hash(uri)
        assert hash1 == hash2

    def test_hash_different_uris_produce_different_hashes(self):
        """Different URIs should produce different hashes."""
        uri1 = "s3://bucket/path/file1.log"
        uri2 = "s3://bucket/path/file2.log"
        hash1 = get_file_hash(uri1)
        hash2 = get_file_hash(uri2)
        assert hash1 != hash2

    def test_hash_is_valid_sha256(self):
        """Hash should be a valid SHA256 hex digest."""
        uri = "s3://bucket/path/file.log"
        file_hash = get_file_hash(uri)
        # SHA256 hex digest is 64 characters
        assert len(file_hash) == 64
        # Should be valid hex
        int(file_hash, 16)

    def test_hash_is_consistent_with_sha256(self):
        """Hash should match expected SHA256 of URI."""
        uri = "s3://bucket/path/file.log"
        expected_hash = hashlib.sha256(uri.encode("utf-8")).hexdigest()
        assert get_file_hash(uri) == expected_hash

    def test_hash_handles_special_characters(self):
        """Hash should handle URIs with special characters."""
        uri = "ssh://user@host:22/path/file with spaces.log"
        file_hash = get_file_hash(uri)
        assert len(file_hash) == 64


class TestExpandFsspecPatterns:
    """Tests for expand_fsspec_patterns function."""

    def test_expand_single_file(self, tmp_path):
        """Should return single file when pattern matches one file."""
        # Create a test file
        test_file = tmp_path / "test.log"
        test_file.write_text("test content")

        patterns = [str(test_file)]
        result = expand_fsspec_patterns(patterns)

        assert len(result) == 1
        assert str(test_file) in result

    def test_expand_glob_pattern(self, tmp_path):
        """Should expand glob pattern to matching files."""
        # Create test files
        (tmp_path / "file1.log").write_text("content1")
        (tmp_path / "file2.log").write_text("content2")
        (tmp_path / "file3.txt").write_text("content3")

        patterns = [str(tmp_path / "*.log")]
        result = expand_fsspec_patterns(patterns)

        assert len(result) == 2
        assert str(tmp_path / "file1.log") in result
        assert str(tmp_path / "file2.log") in result
        assert str(tmp_path / "file3.txt") not in result

    def test_expand_recursive_pattern(self, tmp_path):
        """Should expand recursive glob patterns."""
        # Create nested directory structure
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir1" / "file1.log").write_text("content1")
        (tmp_path / "dir2").mkdir()
        (tmp_path / "dir2" / "file2.log").write_text("content2")
        (tmp_path / "file3.log").write_text("content3")

        patterns = [str(tmp_path / "**/*.log")]
        result = expand_fsspec_patterns(patterns)

        assert len(result) == 3
        assert str(tmp_path / "dir1" / "file1.log") in result
        assert str(tmp_path / "dir2" / "file2.log") in result
        assert str(tmp_path / "file3.log") in result

    def test_expand_multiple_patterns(self, tmp_path):
        """Should expand multiple patterns and combine results."""
        # Create test files
        (tmp_path / "file1.log").write_text("content1")
        (tmp_path / "file2.err").write_text("content2")
        (tmp_path / "file3.txt").write_text("content3")

        patterns = [
            str(tmp_path / "*.log"),
            str(tmp_path / "*.err"),
        ]
        result = expand_fsspec_patterns(patterns)

        assert len(result) == 2
        assert str(tmp_path / "file1.log") in result
        assert str(tmp_path / "file2.err") in result

    def test_expand_no_matches_returns_empty_list(self, tmp_path):
        """Should return empty list when pattern matches no files."""
        patterns = [str(tmp_path / "*.nonexistent")]
        result = expand_fsspec_patterns(patterns)
        assert result == []

    def test_expand_handles_file_protocol(self, tmp_path):
        """Should handle file:// protocol URIs."""
        test_file = tmp_path / "test.log"
        test_file.write_text("test content")

        patterns = [f"file://{test_file}"]
        result = expand_fsspec_patterns(patterns)

        assert len(result) == 1
        # Result should normalize to file:// protocol
        assert result[0].startswith("file://")


class TestGetFingerprint:
    """Tests for get_fingerprint function."""

    def test_fingerprint_contains_required_fields(self, tmp_path):
        """Fingerprint should contain uri, size, mtime, and fingerprinted_at."""
        test_file = tmp_path / "test.log"
        test_file.write_text("test content\n")

        fingerprint = get_fingerprint(str(test_file))

        assert "uri" in fingerprint
        assert "size" in fingerprint
        assert "mtime" in fingerprint
        assert "fingerprinted_at" in fingerprint

    def test_fingerprint_uri_matches_input(self, tmp_path):
        """Fingerprint URI should match input URI."""
        test_file = tmp_path / "test.log"
        test_file.write_text("test content\n")

        uri = str(test_file)
        fingerprint = get_fingerprint(uri)

        assert fingerprint["uri"] == uri

    def test_fingerprint_size_is_correct(self, tmp_path):
        """Fingerprint size should match actual file size."""
        test_file = tmp_path / "test.log"
        content = "test content\n"
        test_file.write_text(content)

        fingerprint = get_fingerprint(str(test_file))

        assert fingerprint["size"] == len(content.encode("utf-8"))

    def test_fingerprint_mtime_is_valid_timestamp(self, tmp_path):
        """Fingerprint mtime should be a valid ISO timestamp."""
        test_file = tmp_path / "test.log"
        test_file.write_text("test content\n")

        fingerprint = get_fingerprint(str(test_file))

        # Should be able to parse as datetime
        mtime = datetime.fromisoformat(fingerprint["mtime"].replace("Z", "+00:00"))
        assert isinstance(mtime, datetime)

    def test_fingerprint_includes_checksum_for_local_files(self, tmp_path):
        """Fingerprint should include MD5 checksum for local files."""
        test_file = tmp_path / "test.log"
        content = "test content\n"
        test_file.write_text(content)

        fingerprint = get_fingerprint(str(test_file))

        assert "checksum" in fingerprint
        # Check if checksum format is correct
        assert fingerprint["checksum"].startswith("md5:")

    def test_fingerprint_is_deterministic(self, tmp_path):
        """Fingerprint should be deterministic for same file state."""
        test_file = tmp_path / "test.log"
        test_file.write_text("test content\n")

        fp1 = get_fingerprint(str(test_file))
        fp2 = get_fingerprint(str(test_file))

        # Size and checksum should be identical
        assert fp1["size"] == fp2["size"]
        assert fp1["checksum"] == fp2["checksum"]

    def test_fingerprint_changes_when_file_modified(self, tmp_path):
        """Fingerprint should change when file is modified."""
        import time

        test_file = tmp_path / "test.log"
        test_file.write_text("original content\n")

        fp1 = get_fingerprint(str(test_file))

        # Small delay to ensure mtime changes
        time.sleep(0.01)

        # Modify file with different content
        test_file.write_text("modified content that is different\n")

        fp2 = get_fingerprint(str(test_file))

        # Size and checksum should differ
        assert fp1["size"] != fp2["size"]
        assert fp1["checksum"] != fp2["checksum"]


class TestReadManifest:
    """Tests for read_manifest and write_manifest functions."""

    def test_read_manifest_returns_list_of_uris(self, tmp_path):
        """Should read manifest file and return list of URIs."""
        manifest_file = tmp_path / "manifest.txt"
        uris = [
            "s3://bucket/file1.log",
            "s3://bucket/file2.log",
            "ssh://host/path/file3.log",
        ]
        manifest_file.write_text("\n".join(uris))

        result = read_manifest(str(manifest_file))

        assert result == uris

    def test_read_manifest_strips_whitespace(self, tmp_path):
        """Should strip whitespace from URIs."""
        manifest_file = tmp_path / "manifest.txt"
        manifest_file.write_text("  s3://bucket/file1.log  \ns3://bucket/file2.log\n  ssh://host/path/file3.log\n")

        result = read_manifest(str(manifest_file))

        assert result == [
            "s3://bucket/file1.log",
            "s3://bucket/file2.log",
            "ssh://host/path/file3.log",
        ]

    def test_read_manifest_skips_empty_lines(self, tmp_path):
        """Should skip empty lines in manifest."""
        manifest_file = tmp_path / "manifest.txt"
        manifest_file.write_text("s3://bucket/file1.log\n\ns3://bucket/file2.log\n  \nssh://host/path/file3.log\n")

        result = read_manifest(str(manifest_file))

        assert result == [
            "s3://bucket/file1.log",
            "s3://bucket/file2.log",
            "ssh://host/path/file3.log",
        ]

    def test_read_manifest_handles_comments(self, tmp_path):
        """Should skip lines starting with # (comments)."""
        manifest_file = tmp_path / "manifest.txt"
        manifest_file.write_text("# This is a comment\ns3://bucket/file1.log\n# Another comment\ns3://bucket/file2.log\n")

        result = read_manifest(str(manifest_file))

        assert result == [
            "s3://bucket/file1.log",
            "s3://bucket/file2.log",
        ]

    def test_write_manifest_creates_file(self, tmp_path):
        """Should write URIs to manifest file."""
        manifest_file = tmp_path / "manifest.txt"
        uris = [
            "s3://bucket/file1.log",
            "s3://bucket/file2.log",
        ]

        write_manifest(str(manifest_file), uris)

        assert manifest_file.exists()
        content = manifest_file.read_text()
        assert "s3://bucket/file1.log" in content
        assert "s3://bucket/file2.log" in content

    def test_write_and_read_manifest_roundtrip(self, tmp_path):
        """Should be able to write and read manifest."""
        manifest_file = tmp_path / "manifest.txt"
        uris = [
            "s3://bucket/file1.log",
            "s3://bucket/file2.log",
            "ssh://host/path/file3.log",
        ]

        write_manifest(str(manifest_file), uris)
        result = read_manifest(str(manifest_file))

        assert result == uris


class TestGetErrorDefinition:
    """Tests for get_error_definition function."""

    def test_get_error_definition_returns_correct_definition(self):
        """Should return the correct error definition by ID."""
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
                "error1": ErrorDefinition(
                    id="error1",
                    pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
                    files=["/var/log/*.log"],
                    meaning="Test error",
                    context_lines=5,
                    suggestion="Fix it",
                ),
                "error2": ErrorDefinition(
                    id="error2",
                    pattern=PatternMatcher(type=PatternType.LITERAL, pattern="WARNING"),
                    files=["/var/log/*.log"],
                    meaning="Test warning",
                    context_lines=3,
                    suggestion="Check it",
                ),
            },
        )

        error_def = get_error_definition(catalog, "error1")

        assert error_def.id == "error1"
        assert error_def.pattern.pattern == "ERROR"

    def test_get_error_definition_raises_on_missing_id(self):
        """Should raise KeyError when error ID doesn't exist."""
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
            errors={},
        )

        with pytest.raises(KeyError) as exc_info:
            get_error_definition(catalog, "nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_get_error_definition_works_with_loaded_catalog(self, tmp_path):
        """Should work with a catalog loaded from YAML."""
        from src.domain.catalog import load_catalog

        # Use the sample catalog from examples
        catalog_path = Path(__file__).parent.parent.parent / "examples" / "sample_catalog.yaml"
        catalog = load_catalog(str(catalog_path))

        # Get one of the errors from the sample catalog
        error_def = get_error_definition(catalog, "slurm_oom")

        assert error_def.id == "slurm_oom"
        assert error_def.pattern.pattern == "OOM killed"
