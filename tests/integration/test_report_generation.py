"""Integration tests for end-to-end report generation.

Tests the complete workflow from error matches to reports.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from src.domain.models import CatalogMetadata, ErrorCatalog, ErrorDefinition, ErrorMatch, PatternMatcher, PatternType
from src.reporting.aggregator import ReportAggregator
from src.reporting.jsonld import ReportGenerator
from src.reporting.templates import TemplateRenderer


@pytest.fixture
def sample_catalog():
    """Sample error catalog."""
    now = datetime.now()
    return ErrorCatalog(
        version="1.0.0",
        schema_version="1.0.0",
        metadata=CatalogMetadata(
            name="Test Catalog", description="Test catalog for integration tests", author="Test Author", created=now, updated=now
        ),
        errors={
            "slurm_oom": ErrorDefinition(
                id="slurm_oom",
                pattern=PatternMatcher(type=PatternType.REGEX, pattern=r"Out of memory"),
                files=["s3://bucket/logs/*.log"],
                meaning="Job exceeded memory limits",
                context_lines=3,
                suggestion="Increase --mem parameter",
            ),
            "slurm_timeout": ErrorDefinition(
                id="slurm_timeout",
                pattern=PatternMatcher(type=PatternType.REGEX, pattern=r"TIMEOUT"),
                files=["s3://bucket/logs/*.log"],
                meaning="Job exceeded time limit",
                context_lines=2,
                suggestion="Increase --time parameter",
            ),
        },
    )


@pytest.fixture
def sample_matches():
    """Sample error matches."""
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


@pytest.mark.integration
class TestEndToEndReportGeneration:
    """Test complete report generation workflow."""

    def test_generate_jsonld_report_from_matches(self, sample_matches, sample_catalog, tmp_path):
        """Test generating JSON-LD report from matches."""
        generator = ReportGenerator()

        metadata = {"author": {"name": "Test User", "email": "test@example.com"}}

        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        # Verify report structure
        assert report["@type"] == "ErrorReport"
        assert report["summary"]["totalMatches"] == 3
        assert report["summary"]["errorTypes"] == 2
        assert len(report["hasPart"]) == 3

        # Save report
        report_path = tmp_path / "report.jsonld"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        assert report_path.exists()

    def test_load_and_aggregate_matches(self, sample_matches, tmp_path):
        """Test loading matches from files and aggregating."""
        # Save matches to individual files
        match_files = []
        for i, match in enumerate(sample_matches):
            match_file = tmp_path / f"match_{i}.json"
            with open(match_file, "w", encoding="utf-8") as f:
                json.dump(match.model_dump(mode="json"), f)
            match_files.append(str(match_file))

        # Load and aggregate
        aggregator = ReportAggregator()
        loaded_matches = aggregator.load_matches_from_files(match_files)

        assert len(loaded_matches) == 3

        # Test grouping
        by_error = aggregator.group_by_error(loaded_matches)
        assert len(by_error) == 2
        assert len(by_error["slurm_oom"]) == 2

        by_file = aggregator.group_by_file(loaded_matches)
        assert len(by_file) == 3

        # Test statistics
        stats = aggregator.calculate_statistics(loaded_matches)
        assert stats["total_matches"] == 3
        assert stats["unique_errors"] == 2
        assert stats["unique_hosts"] == 3

    def test_full_workflow_jsonld_to_templates(self, sample_matches, sample_catalog, tmp_path):
        """Test complete workflow: matches -> JSON-LD -> templates."""
        # Step 1: Generate JSON-LD report
        generator = ReportGenerator()
        metadata = {"author": {"name": "Integration Test", "email": "test@example.com"}}
        report = generator.generate_report(sample_matches, sample_catalog, metadata)

        # Save JSON-LD report
        jsonld_path = tmp_path / "report.jsonld"
        with open(jsonld_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Step 2: Prepare data for templates
        template_data = {
            "title": "Error Scan Report",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": report["summary"],
            "errors_by_type": {},
        }

        # Group matches for template
        for match in report["hasPart"]:
            error_type = match["errorDefinition"]
            if error_type not in template_data["errors_by_type"]:
                template_data["errors_by_type"][error_type] = []

            template_data["errors_by_type"][error_type].append(
                {"file": Path(match["url"]).name, "line": match["position"], "text": match["text"]}
            )

        # Step 3: Render templates
        renderer = TemplateRenderer()

        # Render Markdown
        md_path = tmp_path / "report.md"
        renderer.render("report.md.j2", template_data, str(md_path))
        assert md_path.exists()
        md_content = md_path.read_text()
        assert "Error Scan Report" in md_content
        assert "slurm_oom" in md_content

        # Render HTML
        html_path = tmp_path / "report.html"
        renderer.render("report.html.j2", template_data, str(html_path))
        assert html_path.exists()
        html_content = html_path.read_text()
        assert "<!DOCTYPE html>" in html_content
        assert "slurm_oom" in html_content

        # Render text
        txt_path = tmp_path / "summary.txt"
        renderer.render("summary.txt.j2", template_data, str(txt_path))
        assert txt_path.exists()
        txt_content = txt_path.read_text()
        assert "Error Scan Report" in txt_content
        assert "Total Matches: 3" in txt_content

    def test_aggregator_to_jsonld_integration(self, sample_matches, sample_catalog, tmp_path):
        """Test integration between aggregator and JSON-LD generator."""
        # Save matches to files
        match_files = []
        for i, match in enumerate(sample_matches):
            match_file = tmp_path / f"match_{i}.json"
            with open(match_file, "w", encoding="utf-8") as f:
                json.dump(match.model_dump(mode="json"), f)
            match_files.append(str(match_file))

        # Load matches
        aggregator = ReportAggregator()
        loaded_matches = aggregator.load_matches_from_files(match_files)

        # Generate report
        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        report = generator.generate_report(loaded_matches, sample_catalog, metadata)

        # Verify report
        assert report["@type"] == "ErrorReport"
        assert report["summary"]["totalMatches"] == 3

        # Verify grouping functions work on loaded matches
        by_error = generator.group_by_error(loaded_matches)
        assert len(by_error) == 2

        by_file = generator.group_by_file(loaded_matches)
        assert len(by_file) == 3

    def test_cli_export_command_integration(self, sample_matches, sample_catalog, tmp_path):
        """Test CLI export command with real data."""
        # Generate and save report with template-friendly structure
        template_data = {
            "title": "Error Scan Report",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": {"totalMatches": 3, "errorTypes": 2, "filesScanned": 3},
            "errors_by_type": {
                "slurm_oom": [{"file": "job123.log", "line": 42, "text": "Out of memory"}],
                "slurm_timeout": [{"file": "job125.log", "line": 100, "text": "TIMEOUT"}],
            },
        }

        report_path = tmp_path / "report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(template_data, f, indent=2)

        # Use export command
        from src.reporting.cli_commands import export_command

        output_path = tmp_path / "exported_report.md"
        export_command(str(report_path), "markdown", str(output_path))

        # Verify export
        assert output_path.exists()
        content = output_path.read_text()
        assert len(content) > 0
        assert "Error Scan Report" in content

    def test_error_handling_missing_files(self, tmp_path):
        """Test error handling when files are missing."""
        from src.reporting.cli_commands import export_command, view_command

        # Test export with missing report
        with pytest.raises(FileNotFoundError):
            export_command("/nonexistent/report.jsonld", "markdown", str(tmp_path / "out.md"))

        # Test view with missing report
        with pytest.raises(FileNotFoundError):
            view_command("/nonexistent/report.jsonld")

    def test_round_trip_serialization(self, sample_matches, sample_catalog, tmp_path):
        """Test that data survives round-trip serialization."""
        # Generate report
        generator = ReportGenerator()
        metadata = {"author": {"name": "Test", "email": "test@example.com"}}
        original_report = generator.generate_report(sample_matches, sample_catalog, metadata)

        # Save to file
        report_path = tmp_path / "report.jsonld"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(original_report, f, indent=2)

        # Load back
        with open(report_path, encoding="utf-8") as f:
            loaded_report = json.load(f)

        # Verify structure is preserved
        assert loaded_report["@type"] == original_report["@type"]
        assert loaded_report["summary"] == original_report["summary"]
        assert len(loaded_report["hasPart"]) == len(original_report["hasPart"])


@pytest.mark.unit
class TestReportingModuleExports:
    """Test that reporting module exports expected components."""

    def test_module_exports(self):
        """Test that reporting module exports main classes."""
        from src.reporting import ReportAggregator, ReportGenerator, TemplateRenderer

        assert ReportGenerator is not None
        assert ReportAggregator is not None
        assert TemplateRenderer is not None
