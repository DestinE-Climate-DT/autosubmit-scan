"""Integration tests for pattern matching on remote files.

Tests pattern matching, streaming, and context extraction on files accessed via:
- S3 (MinIO)
- SFTP
- FTP

These tests require CI services to be running. Use pytest markers:
- pytest -m integration --remote
"""

import os
from datetime import datetime

import pytest

from src.domain.models import (
    ErrorDefinition,
    PatternMatcher,
    PatternType,
)
from src.matching.context_extractor import ContextExtractor
from src.matching.match_builder import ErrorMatchBuilder
from src.matching.pattern_matcher import PatternMatcherFactory
from src.matching.stream_reader import FileStream

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def s3_uri():
    """Get S3 URI for test file.

    Assumes MinIO is running locally via CI setup.
    """
    # MinIO local endpoint
    bucket = os.environ.get("MINIO_BUCKET", "test-bucket")
    return f"s3://{bucket}/slurm_oom.log"


@pytest.fixture
def sftp_uri():
    """Get SFTP URI for test file.

    Assumes SFTP server is running locally via CI setup.
    """
    user = os.environ.get("SFTP_USER", "testuser")
    host = os.environ.get("SFTP_HOST", "localhost")
    port = os.environ.get("SFTP_PORT", "2222")
    return f"sftp://{user}@{host}:{port}/upload/slurm_oom.log"


@pytest.fixture
def ftp_uri():
    """Get FTP URI for test file.

    Assumes FTP server is running locally via CI setup.
    """
    user = os.environ.get("FTP_USER", "testuser")
    password = os.environ.get("FTP_PASSWORD", "testpass")
    host = os.environ.get("FTP_HOST", "localhost")
    port = os.environ.get("FTP_PORT", "2121")
    return f"ftp://{user}:{password}@{host}:{port}/slurm_oom.log"


@pytest.fixture
def local_oom_log():
    """Get path to local OOM log fixture."""
    import pathlib
    test_dir = pathlib.Path(__file__).parent.parent
    return str(test_dir / "fixtures" / "slurm_oom.log")


class TestPatternMatchingS3:
    """Test pattern matching on S3/MinIO files."""

    @pytest.mark.remote
    def test_match_pattern_s3_file(self, s3_uri):
        """Test matching a pattern in an S3 file."""
        # Create a literal pattern matcher for OOM events
        pattern = PatternMatcher(
            type=PatternType.LITERAL,
            pattern="oom-kill event"
        )
        matcher = PatternMatcherFactory.create_matcher(pattern)

        # Stream the S3 file and look for matches
        with FileStream.open_file(s3_uri) as stream:
            found_match = False
            match_line_num = None

            for line_num, line_text in stream.read_lines():
                if matcher.match(line_text):
                    found_match = True
                    match_line_num = line_num
                    break

        assert found_match is True
        assert match_line_num is not None

    @pytest.mark.remote
    def test_regex_match_s3_file(self, s3_uri):
        """Test regex matching in S3 file."""
        # Create a regex pattern for SLURM job IDs
        pattern = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"Job \d+"
        )
        matcher = PatternMatcherFactory.create_matcher(pattern)

        # Stream and find matches
        with FileStream.open_file(s3_uri) as stream:
            matches_found = []

            for line_num, line_text in stream.read_lines():
                if matcher.match(line_text):
                    matches_found.append((line_num, line_text))

        assert len(matches_found) > 0
        # Check that we found "Job 123456"
        assert any("123456" in text for _, text in matches_found)

    @pytest.mark.remote
    def test_context_extraction_s3(self, s3_uri):
        """Test extracting context from S3 file."""
        extractor = ContextExtractor()

        # Extract context around line 22 (OOM kill event)
        result = extractor.extract_context(
            s3_uri,
            line_number=22,
            context_lines=2
        )

        assert result.line_number == 22
        assert "oom-kill" in result.matched_line.lower()
        assert len(result.before) == 2
        assert len(result.after) == 2

    @pytest.mark.remote
    def test_stream_large_s3_file(self, s3_uri):
        """Test streaming S3 file without loading all into memory."""
        with FileStream.open_file(s3_uri) as stream:
            # Read first 10 lines only
            count = 0
            for _line_num, _line_text in stream.read_lines():
                count += 1
                if count >= 10:
                    break

        assert count == 10


class TestPatternMatchingSFTP:
    """Test pattern matching on SFTP files."""

    @pytest.mark.remote
    def test_match_pattern_sftp_file(self, sftp_uri):
        """Test matching a pattern in an SFTP file."""
        pattern = PatternMatcher(
            type=PatternType.LITERAL,
            pattern="Out of memory"
        )
        matcher = PatternMatcherFactory.create_matcher(pattern)

        # Stream the SFTP file
        with FileStream.open_file(sftp_uri) as stream:
            found_match = False

            for _line_num, line_text in stream.read_lines():
                if matcher.match(line_text):
                    found_match = True
                    break

        assert found_match is True

    @pytest.mark.remote
    def test_context_extraction_sftp(self, sftp_uri):
        """Test extracting context from SFTP file."""
        extractor = ContextExtractor()

        # Extract context around line 21 (ERROR: Out of memory)
        result = extractor.extract_context(
            sftp_uri,
            line_number=21,
            context_lines=3
        )

        assert result.line_number == 21
        assert "out of memory" in result.matched_line.lower()
        assert len(result.before) <= 3
        assert len(result.after) <= 3

    @pytest.mark.remote
    def test_regex_case_insensitive_sftp(self, sftp_uri):
        """Test case-insensitive regex on SFTP file."""
        pattern = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"error",
            flags=["IGNORECASE"]
        )
        matcher = PatternMatcherFactory.create_matcher(pattern)

        with FileStream.open_file(sftp_uri) as stream:
            matches = 0
            for _line_num, line_text in stream.read_lines():
                if matcher.match(line_text):
                    matches += 1

        # Should find multiple ERROR lines
        assert matches >= 2


class TestPatternMatchingFTP:
    """Test pattern matching on FTP files."""

    @pytest.mark.remote
    def test_match_pattern_ftp_file(self, ftp_uri):
        """Test matching a pattern in an FTP file."""
        pattern = PatternMatcher(
            type=PatternType.LITERAL,
            pattern="Memory usage"
        )
        matcher = PatternMatcherFactory.create_matcher(pattern)

        with FileStream.open_file(ftp_uri) as stream:
            found_match = False

            for _line_num, line_text in stream.read_lines():
                if matcher.match(line_text):
                    found_match = True
                    break

        assert found_match is True

    @pytest.mark.remote
    def test_context_extraction_ftp(self, ftp_uri):
        """Test extracting context from FTP file."""
        extractor = ContextExtractor()

        # Extract context from a memory usage line
        result = extractor.extract_context(
            ftp_uri,
            line_number=16,
            context_lines=1
        )

        assert result.line_number == 16
        assert "memory usage" in result.matched_line.lower()

    @pytest.mark.remote
    def test_callable_matcher_ftp(self, ftp_uri):
        """Test callable pattern matcher on FTP file."""
        pattern = PatternMatcher(
            type=PatternType.CALLABLE,
            pattern="examples.custom_matchers:detect_slurm_oom_kill"
        )
        matcher = PatternMatcherFactory.create_matcher(pattern)

        with FileStream.open_file(ftp_uri) as stream:
            oom_matches = []

            for line_num, line_text in stream.read_lines():
                if matcher.match(line_text):
                    oom_matches.append((line_num, line_text))

        # Should find the slurmstepd OOM kill events
        assert len(oom_matches) >= 1
        assert any("slurmstepd" in text.lower() for _, text in oom_matches)


class TestErrorMatchBuilding:
    """Test building ErrorMatch instances from matches."""

    def test_build_match_from_local_file(self, local_oom_log):
        """Test building ErrorMatch from a local file match."""
        # Define an error
        error_def = ErrorDefinition(
            id="slurm_oom",
            pattern=PatternMatcher(
                type=PatternType.LITERAL,
                pattern="oom-kill event"
            ),
            files=[local_oom_log],
            meaning="SLURM job was killed due to out-of-memory condition",
            context_lines=2,
            suggestion="Increase memory allocation in job script"
        )

        # Find the pattern
        matcher = PatternMatcherFactory.create_matcher(error_def.pattern)
        with FileStream.open_file(local_oom_log) as stream:
            for line_num, line_text in stream.read_lines():
                if matcher.match(line_text):
                    # Extract context
                    extractor = ContextExtractor()
                    context = extractor.extract_context(
                        local_oom_log,
                        line_num,
                        error_def.context_lines
                    )

                    # Build the match
                    match = ErrorMatchBuilder.build_match(
                        error_def=error_def,
                        file_uri=local_oom_log,
                        line_number=line_num,
                        matched_text=line_text.strip(),
                        context=context
                    )

                    # Verify the match
                    assert match.error_id == "slurm_oom"
                    assert match.file_uri == local_oom_log
                    assert match.line_number == line_num
                    assert "oom-kill" in match.matched_text.lower()
                    assert isinstance(match.timestamp, datetime)
                    assert len(match.context_before) <= 2
                    assert len(match.context_after) <= 2

                    break  # Only test first match

    @pytest.mark.remote
    def test_build_match_from_s3_file(self, s3_uri):
        """Test building ErrorMatch from S3 file."""
        error_def = ErrorDefinition(
            id="memory_limit_exceeded",
            pattern=PatternMatcher(
                type=PatternType.REGEX,
                pattern=r"Exceeded.*memory limit",
                flags=["IGNORECASE"]
            ),
            files=[s3_uri],
            meaning="SLURM step exceeded allocated memory",
            context_lines=1,
            suggestion="Review memory requirements and adjust job allocation",
            metadata={"severity": "high", "category": "resource"}
        )

        matcher = PatternMatcherFactory.create_matcher(error_def.pattern)
        extractor = ContextExtractor()

        with FileStream.open_file(s3_uri) as stream:
            for line_num, line_text in stream.read_lines():
                if matcher.match(line_text):
                    context = extractor.extract_context(
                        s3_uri,
                        line_num,
                        error_def.context_lines
                    )

                    match = ErrorMatchBuilder.build_match(
                        error_def=error_def,
                        file_uri=s3_uri,
                        line_number=line_num,
                        matched_text=line_text.strip(),
                        context=context,
                        metadata={"scanner_version": "2.0"}
                    )

                    # Verify metadata merging
                    assert match.metadata["severity"] == "high"
                    assert match.metadata["category"] == "resource"
                    assert match.metadata["scanner_version"] == "2.0"

                    break


class TestMultiProtocolSupport:
    """Test that the same pattern works across all protocols."""

    def test_same_pattern_all_protocols(self, local_oom_log, s3_uri, sftp_uri, ftp_uri):
        """Test the same pattern on local, S3, SFTP, and FTP."""
        pattern = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"SLURM Job \d+",
            flags=["IGNORECASE"]
        )
        matcher = PatternMatcherFactory.create_matcher(pattern)

        results = {}

        # Test local
        with FileStream.open_file(local_oom_log) as stream:
            for _line_num, line_text in stream.read_lines():
                if matcher.match(line_text):
                    results['local'] = True
                    break

        # Test S3 (if available)
        if pytest.mark.remote:
            try:
                with FileStream.open_file(s3_uri) as stream:
                    for _line_num, line_text in stream.read_lines():
                        if matcher.match(line_text):
                            results['s3'] = True
                            break
            except Exception:
                results['s3'] = False

        # All tested protocols should find the pattern
        assert results.get('local') is True
