"""Unit tests for JSON-LD report generation.

These tests define the expected behavior of the report generator
following TDD principles.
"""

from datetime import datetime

import pytest

from src.domain.models import CatalogMetadata, ErrorCatalog, ErrorDefinition, ErrorMatch, PatternMatcher, PatternType


@pytest.fixture
def sample_catalog():
    """Sample error catalog for testing."""
    now = datetime.now()
    return ErrorCatalog(
        version="1.0.0",
        schema_version="1.0.0",
        metadata=CatalogMetadata(
            name="Test Catalog",
            description="Test error catalog",
            author="Test Author",
            created=now,
            updated=now
        ),
        errors={
            "slurm_oom": ErrorDefinition(
                id="slurm_oom",
                pattern=PatternMatcher(type=PatternType.REGEX, pattern=r"Out of memory"),
                files=["s3://bucket/logs/*.log"],
                meaning="Job exceeded memory limits",
                context_lines=3,
                suggestion="Increase --mem parameter"
            ),
            "slurm_timeout": ErrorDefinition(
                id="slurm_timeout",
                pattern=PatternMatcher(type=PatternType.REGEX, pattern=r"TIMEOUT"),
                files=["s3://bucket/logs/*.log"],
                meaning="Job exceeded time limit",
                context_lines=2,
                suggestion="Increase --time parameter"
            )
        }
    )


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
            context_before=["Starting job", "Allocating resources", "Running application"],
            context_after=["Job terminated", "Cleanup initiated"],
            timestamp=now,
            metadata={"host": "node001", "job_id": "123"}
        ),
        ErrorMatch(
            error_id="slurm_oom",
            file_uri="s3://bucket/logs/job124.log",
            line_number=56,
            matched_text="Out of memory on node002",
            context_before=["Starting job", "Loading data"],
            context_after=["Error handler triggered"],
            timestamp=now,
            metadata={"host": "node002", "job_id": "124"}
        ),
        ErrorMatch(
            error_id="slurm_timeout",
            file_uri="s3://bucket/logs/job125.log",
            line_number=100,
            matched_text="TIMEOUT reached",
            context_before=["Processing data"],
            context_after=["Job cancelled"],
            timestamp=now,
            metadata={"host": "node003", "job_id": "125"}
        )
    ]


class TestReportStructure:
    """Test JSON-LD report structure."""

    def test_generate_report_basic_structure(self, sample_matches, sample_catalog):
        """Test that generate_report creates proper JSON-LD structure."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {
            "author": {"name": "John Doe", "email": "john@example.com"},
            "scan_date": datetime.now().isoformat()
        }

        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        # Check basic JSON-LD structure
        assert "@context" in report
        assert "@type" in report
        assert report["@type"] == "ErrorReport"
        assert "@id" in report
        assert report["@id"].startswith("urn:uuid:")

        # Check version and metadata
        assert "version" in report
        assert "dateCreated" in report
        assert "author" in report

        # Check summary
        assert "summary" in report
        assert "hasPart" in report

    def test_report_context_structure(self, sample_matches, sample_catalog):
        """Test JSON-LD @context follows Schema.org."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        context = report["@context"]
        assert "@vocab" in context
        assert context["@vocab"] == "https://schema.org/"
        assert "error_scan" in context
        assert context["error_scan"] == "https://destine.example/error-scan/schema#"

    def test_report_has_unique_id(self, sample_matches, sample_catalog):
        """Test that each report gets a unique UUID."""
        import uuid

        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}

        report1 = generator.generate_report(sample_matches, sample_catalog, metadata)
        report2 = generator.generate_report(sample_matches, sample_catalog, metadata)

        assert report1["@id"] != report2["@id"]

        # Verify they are valid UUIDs
        uuid1 = report1["@id"].replace("urn:uuid:", "")
        uuid2 = report2["@id"].replace("urn:uuid:", "")
        assert uuid.UUID(uuid1)
        assert uuid.UUID(uuid2)


class TestReportSummary:
    """Test summary statistics in report."""

    def test_summary_statistics_calculation(self, sample_matches, sample_catalog):
        """Test that summary statistics are calculated correctly."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        summary = report["summary"]
        assert summary["totalMatches"] == 3
        assert summary["errorTypes"] == 2  # slurm_oom and slurm_timeout
        assert summary["filesScanned"] == 3  # 3 unique files

    def test_summary_hosts_scanned(self, sample_matches, sample_catalog):
        """Test that hostsScanned is extracted from metadata."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        summary = report["summary"]
        assert "hostsScanned" in summary
        hosts = summary["hostsScanned"]
        assert len(hosts) == 3
        assert "node001" in hosts
        assert "node002" in hosts
        assert "node003" in hosts

    def test_empty_matches_summary(self, sample_catalog):
        """Test summary with no matches."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report([], sample_catalog, metadata)

        summary = report["summary"]
        assert summary["totalMatches"] == 0
        assert summary["errorTypes"] == 0
        assert summary["filesScanned"] == 0
        assert summary["hostsScanned"] == []


class TestErrorMatchConversion:
    """Test conversion of ErrorMatch to JSON-LD."""

    def test_error_match_jsonld_structure(self, sample_matches, sample_catalog):
        """Test that ErrorMatch is converted to proper JSON-LD structure."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        matches = report["hasPart"]
        assert len(matches) == 3

        first_match = matches[0]
        assert first_match["@type"] == "ErrorMatch"
        assert "@id" in first_match
        assert first_match["@id"].startswith("urn:uuid:")
        assert "errorDefinition" in first_match
        assert "url" in first_match
        assert "position" in first_match
        assert "text" in first_match
        assert "dateFound" in first_match

    def test_error_match_with_context(self, sample_matches, sample_catalog):
        """Test that context lines are included in JSON-LD."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        first_match = report["hasPart"][0]
        assert "context" in first_match
        assert "before" in first_match["context"]
        assert "after" in first_match["context"]
        assert len(first_match["context"]["before"]) == 3
        assert len(first_match["context"]["after"]) == 2

    def test_error_match_about_section(self, sample_matches, sample_catalog):
        """Test that 'about' section includes error definition details."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        first_match = report["hasPart"][0]
        assert "about" in first_match
        assert first_match["about"]["@type"] == "CreativeWork"
        assert "headline" in first_match["about"]
        assert "description" in first_match["about"]
        assert first_match["about"]["headline"] == "Job exceeded memory limits"
        assert first_match["about"]["description"] == "Increase --mem parameter"


class TestHierarchicalGrouping:
    """Test hierarchical grouping of matches."""

    def test_grouping_by_error_id(self, sample_matches, sample_catalog):
        """Test that matches are grouped by error_id."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        grouped = generator.group_by_error(sample_matches)

        assert "slurm_oom" in grouped
        assert "slurm_timeout" in grouped
        assert len(grouped["slurm_oom"]) == 2
        assert len(grouped["slurm_timeout"]) == 1

    def test_grouping_by_file_uri(self, sample_matches, sample_catalog):
        """Test that matches are grouped by file_uri."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        grouped = generator.group_by_file(sample_matches)

        assert "s3://bucket/logs/job123.log" in grouped
        assert "s3://bucket/logs/job124.log" in grouped
        assert "s3://bucket/logs/job125.log" in grouped
        assert len(grouped["s3://bucket/logs/job123.log"]) == 1
        assert len(grouped["s3://bucket/logs/job124.log"]) == 1
        assert len(grouped["s3://bucket/logs/job125.log"]) == 1

    def test_grouping_by_line_number(self, sample_matches, sample_catalog):
        """Test that matches are grouped by line_number within file."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        file_groups = generator.group_by_file(sample_matches)

        # Within each file, matches should be sorted by line number
        for _file_uri, matches in file_groups.items():
            line_numbers = [m.line_number for m in matches]
            assert line_numbers == sorted(line_numbers)


class TestReportMetadata:
    """Test report metadata handling."""

    def test_author_metadata(self, sample_matches, sample_catalog):
        """Test that author metadata is included."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {
            "author": {
                "name": "Jane Smith",
                "email": "jane@example.com"
            }
        }
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        assert "author" in report
        assert report["author"]["@type"] == "Person"
        assert report["author"]["name"] == "Jane Smith"
        assert report["author"]["email"] == "jane@example.com"

    def test_date_created(self, sample_matches, sample_catalog):
        """Test that dateCreated is in ISO format."""
        from datetime import datetime

        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        assert "dateCreated" in report
        # Should be able to parse as ISO datetime
        dt = datetime.fromisoformat(report["dateCreated"].replace("Z", "+00:00"))
        assert isinstance(dt, datetime)

    def test_version_included(self, sample_matches, sample_catalog):
        """Test that report version is included."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        assert "version" in report
        assert report["version"] == "1.0.0"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_matches_list(self, sample_catalog):
        """Test report generation with empty matches list."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report([], sample_catalog, metadata)

        assert report["@type"] == "ErrorReport"
        assert report["summary"]["totalMatches"] == 0
        assert report["hasPart"] == []

    def test_matches_without_host_metadata(self, sample_catalog):
        """Test matches that don't have host metadata."""
        from src.reporting.jsonld import ReportGenerator

        now = datetime.now()
        matches = [
            ErrorMatch(
                error_id="slurm_oom",
                file_uri="s3://bucket/logs/job123.log",
                line_number=42,
                matched_text="Out of memory",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={}  # No host metadata
            )
        ]

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(matches, sample_catalog, metadata)

        assert report["summary"]["hostsScanned"] == []

    def test_matches_with_missing_error_definitions(self, sample_catalog):
        """Test matches that reference non-existent error definitions."""
        from src.reporting.jsonld import ReportGenerator

        now = datetime.now()
        matches = [
            ErrorMatch(
                error_id="non_existent_error",
                file_uri="s3://bucket/logs/job123.log",
                line_number=42,
                matched_text="Some error",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={}
            )
        ]

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(matches, sample_catalog, metadata)

        # Should still create report, but with generic about section
        assert len(report["hasPart"]) == 1
        match = report["hasPart"][0]
        assert "about" in match
        assert match["about"]["@type"] == "CreativeWork"


class TestSchemaOrgCompliance:
    """Test Schema.org compliance."""

    def test_report_uses_schema_org_types(self, sample_matches, sample_catalog):
        """Test that report uses Schema.org types."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        # Report should use ErrorReport type (custom extension)
        assert report["@type"] == "ErrorReport"

        # Author should use Person type
        assert report["author"]["@type"] == "Person"

        # Matches should use ErrorMatch type (custom extension)
        for match in report["hasPart"]:
            assert match["@type"] == "ErrorMatch"
            assert match["about"]["@type"] == "CreativeWork"

    def test_report_uses_schema_org_properties(self, sample_matches, sample_catalog):
        """Test that report uses Schema.org property names."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        # Should use Schema.org property names
        assert "dateCreated" in report  # Not 'created' or 'date_created'
        assert "author" in report
        assert "hasPart" in report  # Not 'matches' or 'parts'

        # Match should use Schema.org properties
        match = report["hasPart"][0]
        assert "url" in match  # File URI
        assert "text" in match  # Matched text
        assert "dateFound" in match  # Timestamp
        assert "about" in match  # Error definition


@pytest.mark.unit
class TestReportGeneration:
    """Integration tests for report generation."""

    def test_full_report_generation(self, sample_matches, sample_catalog):
        """Test complete report generation workflow."""
        from src.reporting.jsonld import ReportGenerator

        generator = ReportGenerator()
        metadata = {
            "author": {"name": "John Doe", "email": "john@example.com"},
            "scan_description": "Weekly error scan"
        }

        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        # Verify all major components
        assert "@context" in report
        assert "@type" in report
        assert "@id" in report
        assert "version" in report
        assert "dateCreated" in report
        assert "author" in report
        assert "summary" in report
        assert "hasPart" in report

        # Verify summary
        assert report["summary"]["totalMatches"] == 3
        assert report["summary"]["errorTypes"] == 2
        assert report["summary"]["filesScanned"] == 3

        # Verify matches
        assert len(report["hasPart"]) == 3
        for match in report["hasPart"]:
            assert "@type" in match
            assert "@id" in match
            assert "errorDefinition" in match
            assert "url" in match
            assert "position" in match
            assert "text" in match
            assert "about" in match
            assert "context" in match
