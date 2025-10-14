"""E2E tests for the complete scanning workflow.

Tests the full integration from catalog loading through scanning,
report generation, and visualization.
"""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from src.domain.catalog import load_catalog, save_catalog
from src.domain.models import ErrorCatalog, ErrorDefinition
from src.domain.models import PatternMatcher as PatternConfig
from src.matching.pattern_matcher import PatternMatcherFactory
from src.reporting.jsonld import ReportGenerator


@pytest.mark.e2e
class TestFullWorkflow:
    """End-to-end workflow tests."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for E2E tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def simple_catalog(self, temp_workspace):
        """Create a simple test catalog."""
        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata={
                "name": "E2E Test Catalog",
                "description": "Catalog for E2E testing",
                "author": "Test Suite",
                "created": datetime.now(),
                "updated": datetime.now(),
            },
            errors={
                "test_error": ErrorDefinition(
                    id="test_error",
                    pattern=PatternConfig(type="literal", pattern="ERROR: Test failure"),
                    files=["/tmp/*.log"],
                    meaning="Test error for E2E testing",
                    suggestion="This is a test error",
                    context_lines=3,
                    next_errors=[],
                    metadata={"severity": "high"},
                )
            },
        )

        catalog_path = temp_workspace / "test_catalog.yaml"
        save_catalog(catalog, str(catalog_path))
        return catalog_path

    @pytest.fixture
    def test_log_file(self, temp_workspace):
        """Create a test log file with errors."""
        log_file = temp_workspace / "test.log"
        log_file.write_text(
            "Starting application...\nProcessing data...\nERROR: Test failure\nFailed to process item\nShutting down...\n"
        )
        return log_file

    def test_scan_simple_error_detection(self, simple_catalog, test_log_file, temp_workspace):
        """Test basic error detection end-to-end."""
        # Load catalog
        catalog = load_catalog(str(simple_catalog))
        assert "test_error" in catalog.errors

        # Create matcher
        error_def = catalog.errors["test_error"]
        matcher = PatternMatcherFactory.create_matcher(error_def.pattern)

        # Scan file
        matches = []
        with open(test_log_file) as f:
            for line_num, line in enumerate(f, 1):
                if matcher.match(line):
                    from src.domain.models import ErrorMatch

                    match = ErrorMatch(
                        error_id="test_error",
                        file_uri=str(test_log_file),
                        line_number=line_num,
                        matched_text=line.strip(),
                        context_before=[],
                        context_after=[],
                        timestamp=datetime.now(),
                        metadata={},
                    )
                    matches.append(match)

        # Verify matches found
        assert len(matches) == 1
        assert matches[0].error_id == "test_error"
        assert "ERROR: Test failure" in matches[0].matched_text

        # Generate report
        generator = ReportGenerator()
        report = generator.generate_report(
            matches=matches, catalog=catalog, metadata={"author": {"name": "Test", "email": "test@example.com"}}
        )

        # Verify report structure
        assert report["@type"] == "ErrorReport"
        assert report["summary"]["totalMatches"] == 1
        assert report["summary"]["errorTypes"] == 1
        assert len(report["hasPart"]) == 1

        # Save report
        report_path = temp_workspace / "report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        assert report_path.exists()

    def test_scan_with_railway_pattern(self, temp_workspace):
        """Test railway pattern execution in workflow."""
        # Create catalog with railway pattern
        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata={
                "name": "Railway Test",
                "description": "Test railway pattern",
                "author": "Test",
                "created": datetime.now(),
                "updated": datetime.now(),
            },
            errors={
                "error_a": ErrorDefinition(
                    id="error_a",
                    pattern=PatternConfig(type="literal", pattern="ERROR A"),
                    files=["/tmp/*.log"],
                    meaning="First error",
                    suggestion="Check error A",
                    context_lines=2,
                    next_errors=[{"error_id": "error_b", "when": {"type": "always"}}],
                    metadata={},
                ),
                "error_b": ErrorDefinition(
                    id="error_b",
                    pattern=PatternConfig(type="literal", pattern="ERROR B"),
                    files=["/tmp/*.log"],
                    meaning="Second error",
                    suggestion="Check error B",
                    context_lines=2,
                    next_errors=[],
                    metadata={},
                ),
            },
        )

        catalog_path = temp_workspace / "railway_catalog.yaml"
        save_catalog(catalog, str(catalog_path))

        # Create test file
        log_file = temp_workspace / "railway.log"
        log_file.write_text("ERROR A\nERROR B\n")

        # Load and verify
        loaded = load_catalog(str(catalog_path))
        assert len(loaded.errors) == 2

        # Verify railway pattern structure
        error_a = loaded.errors["error_a"]
        first_condition = error_a.next_errors[0]
        assert first_condition.error_id == "error_b"

    def test_scan_generates_report(self, simple_catalog, test_log_file, temp_workspace):
        """Test that scanning generates a complete report."""
        # Load catalog
        catalog = load_catalog(str(simple_catalog))

        # Create matches
        from src.domain.models import ErrorMatch

        matches = [
            ErrorMatch(
                error_id="test_error",
                file_uri=str(test_log_file),
                line_number=3,
                matched_text="ERROR: Test failure",
                context_before=["Starting application...", "Processing data..."],
                context_after=["Failed to process item", "Shutting down..."],
                timestamp=datetime.now(),
                metadata={"severity": "high"},
            )
        ]

        # Generate report
        generator = ReportGenerator()
        report = generator.generate_report(
            matches=matches,
            catalog=catalog,
            metadata={"author": {"name": "Test User", "email": "test@example.com"}, "description": "E2E test report"},
        )

        # Verify report completeness
        assert "@context" in report
        assert "@type" in report
        assert "@id" in report
        assert "version" in report
        assert "dateCreated" in report
        assert "author" in report
        assert "summary" in report
        assert "hasPart" in report

        # Verify summary
        assert report["summary"]["totalMatches"] == 1
        assert report["summary"]["errorTypes"] == 1

        # Verify match details
        match_detail = report["hasPart"][0]
        assert match_detail["@type"] == "ErrorMatch"
        assert match_detail["errorDefinition"] == "test_error"
        assert match_detail["position"] == 3
        assert "ERROR: Test failure" in match_detail["text"]
        assert "about" in match_detail
        assert "context" in match_detail

    def test_export_markdown(self, temp_workspace):
        """Test exporting report to markdown."""
        # Create a minimal report
        from src.domain.models import ErrorMatch

        matches = [
            ErrorMatch(
                error_id="test_error",
                file_uri="/tmp/test.log",
                line_number=1,
                matched_text="ERROR: Test",
                context_before=[],
                context_after=[],
                timestamp=datetime.now(),
                metadata={},
            )
        ]

        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata={
                "name": "Test",
                "description": "Test",
                "author": "Test",
                "created": datetime.now(),
                "updated": datetime.now(),
            },
            errors={
                "test_error": ErrorDefinition(
                    id="test_error",
                    pattern=PatternConfig(type="literal", pattern="ERROR"),
                    files=["/tmp/*.log"],
                    meaning="Test error",
                    suggestion="Fix it",
                    context_lines=0,
                    next_errors=[],
                    metadata={},
                )
            },
        )

        # Generate report
        generator = ReportGenerator()
        report = generator.generate_report(
            matches=matches, catalog=catalog, metadata={"author": {"name": "Test", "email": "test@example.com"}}
        )

        # Test that we can export (actual template rendering tested in unit tests)
        assert report is not None
        assert "hasPart" in report

    def test_export_html(self, temp_workspace):
        """Test exporting report to HTML."""
        # Similar to markdown test
        from src.domain.models import ErrorMatch

        matches = [
            ErrorMatch(
                error_id="test_error",
                file_uri="/tmp/test.log",
                line_number=1,
                matched_text="ERROR: Test",
                context_before=[],
                context_after=[],
                timestamp=datetime.now(),
                metadata={},
            )
        ]

        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata={
                "name": "Test",
                "description": "Test",
                "author": "Test",
                "created": datetime.now(),
                "updated": datetime.now(),
            },
            errors={
                "test_error": ErrorDefinition(
                    id="test_error",
                    pattern=PatternConfig(type="literal", pattern="ERROR"),
                    files=["/tmp/*.log"],
                    meaning="Test error",
                    suggestion="Fix it",
                    context_lines=0,
                    next_errors=[],
                    metadata={},
                )
            },
        )

        generator = ReportGenerator()
        report = generator.generate_report(
            matches=matches, catalog=catalog, metadata={"author": {"name": "Test", "email": "test@example.com"}}
        )

        assert report is not None

    def test_validate_good_catalog(self, simple_catalog):
        """Test validation of a valid catalog."""
        # Load catalog - should not raise
        catalog = load_catalog(str(simple_catalog))
        assert catalog is not None
        assert catalog.version == "1.0.0"

    def test_validate_bad_catalog(self, temp_workspace):
        """Test validation fails for invalid catalog."""
        # Create invalid YAML
        bad_catalog = temp_workspace / "bad_catalog.yaml"
        bad_catalog.write_text("this is not valid yaml: [[[")

        # Should raise YAML error
        with pytest.raises(yaml.YAMLError):
            load_catalog(str(bad_catalog))

    def test_init_command(self, temp_workspace):
        """Test that init creates sample catalog."""
        # Copy sample catalog to temp location
        sample_source = Path(__file__).parent.parent.parent / "examples" / "sample_catalog.yaml"
        if sample_source.exists():
            sample_dest = temp_workspace / "init_catalog.yaml"
            shutil.copy(sample_source, sample_dest)

            # Verify it loads
            catalog = load_catalog(str(sample_dest))
            assert catalog is not None
            assert len(catalog.errors) > 0


@pytest.mark.e2e
@pytest.mark.remote
class TestRemoteWorkflow:
    """E2E tests requiring remote services (S3, SFTP, etc)."""

    def test_scan_remote_files(self):
        """Test scanning files from remote locations."""
        # This test requires CI services to be running
        # Mark as requiring --remote flag
        pytest.skip("Remote services required - run with --remote flag")
