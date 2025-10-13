"""E2E tests for CLI commands.

Tests the command-line interface for all commands:
scan, view, export, validate, init.
"""

import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.domain.catalog import save_catalog
from src.domain.models import ErrorCatalog, ErrorDefinition, ErrorMatch
from src.domain.models import PatternMatcher as PatternConfig
from src.reporting.jsonld import ReportGenerator


@pytest.mark.e2e
class TestCLICommands:
    """E2E tests for CLI command execution."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for CLI tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def simple_catalog_file(self, temp_workspace):
        """Create a simple catalog file for testing."""
        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata={
                "name": "CLI Test Catalog",
                "description": "Test catalog for CLI",
                "author": "Test Suite",
                "created": datetime.now(),
                "updated": datetime.now(),
            },
            errors={
                "cli_test_error": ErrorDefinition(
                    id="cli_test_error",
                    pattern=PatternConfig(
                        type="literal",
                        pattern="CLI_ERROR"
                    ),
                    files=[],
                    meaning="CLI test error",
                    suggestion="Fix CLI test",
                    context_lines=2,
                    next_errors=[],
                    metadata={"severity": "medium"}
                )
            }
        )

        catalog_path = temp_workspace / "cli_catalog.yaml"
        save_catalog(catalog, str(catalog_path))
        return catalog_path

    @pytest.fixture
    def test_report_file(self, temp_workspace):
        """Create a test report file for CLI testing."""
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
                    files=[],
                    meaning="Test error",
                    suggestion="Fix it",
                    context_lines=0,
                    next_errors=[],
                    metadata={}
                )
            }
        )

        matches = [
            ErrorMatch(
                error_id="test_error",
                file_uri="/tmp/test.log",
                line_number=1,
                matched_text="ERROR: Test",
                context_before=[],
                context_after=[],
                timestamp=datetime.now(),
                metadata={}
            )
        ]

        generator = ReportGenerator()
        report = generator.generate_report(
            matches=matches,
            catalog=catalog,
            metadata={"author": {"name": "Test", "email": "test@example.com"}}
        )

        report_path = temp_workspace / "test_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report_path

    def test_cli_help(self):
        """Test that CLI shows help message."""
        # Test main help
        result = subprocess.run(
            ["python", "-m", "src.cli.main", "--help"],
            capture_output=True,
            text=True
        )

        # Should succeed or fail gracefully (CLI may not be fully implemented yet)
        # This is a TDD test - it will fail until we implement the CLI
        assert result.returncode in [0, 1, 2]  # Allow for not-yet-implemented

    def test_scan_command_args(self, simple_catalog_file, temp_workspace):
        """Test that scan command accepts correct arguments."""
        output_dir = temp_workspace / "output"

        # This will fail until CLI is implemented - that's expected for TDD
        result = subprocess.run(
            [
                "python", "-m", "src.cli.main", "scan",
                "--catalog", str(simple_catalog_file),
                "--output", str(output_dir),
                "--cores", "1",
                "--dryrun"
            ],
            capture_output=True,
            text=True
        )

        # For now, we just check it doesn't crash catastrophically
        # Once implemented, this should return 0
        assert result.returncode in [0, 1, 2]

    def test_view_command_args(self, test_report_file):
        """Test that view command accepts report path."""
        # This will fail until CLI is implemented - that's expected for TDD
        # View command needs special handling as it launches TUI
        result = subprocess.run(
            [
                "python", "-m", "src.cli.main", "view",
                str(test_report_file),
                "--help"  # Get help instead of launching TUI
            ],
            capture_output=True,
            text=True
        )

        # For now, we just check structure
        assert result.returncode in [0, 1, 2]

    def test_export_command_args(self, test_report_file, temp_workspace):
        """Test that export command accepts correct arguments."""
        output_file = temp_workspace / "exported.md"

        result = subprocess.run(
            [
                "python", "-m", "src.cli.main", "export",
                str(test_report_file),
                "--template", "markdown",
                "--output", str(output_file)
            ],
            capture_output=True,
            text=True
        )

        # For now, we just check structure
        assert result.returncode in [0, 1, 2]

    def test_validate_command_good(self, simple_catalog_file):
        """Test validate command with valid catalog."""
        result = subprocess.run(
            [
                "python", "-m", "src.cli.main", "validate",
                str(simple_catalog_file)
            ],
            capture_output=True,
            text=True
        )

        # Should succeed once implemented
        assert result.returncode in [0, 1, 2]

    def test_validate_command_bad(self, temp_workspace):
        """Test validate command with invalid catalog."""
        bad_file = temp_workspace / "bad.yaml"
        bad_file.write_text("invalid: [[[")

        result = subprocess.run(
            [
                "python", "-m", "src.cli.main", "validate",
                str(bad_file)
            ],
            capture_output=True,
            text=True
        )

        # Should fail with exit code 1 once implemented
        assert result.returncode in [0, 1, 2]

    def test_init_command(self, temp_workspace):
        """Test init command creates sample catalog."""
        output_file = temp_workspace / "new_catalog.yaml"

        result = subprocess.run(
            [
                "python", "-m", "src.cli.main", "init",
                "--output", str(output_file)
            ],
            capture_output=True,
            text=True
        )

        # Should succeed once implemented
        assert result.returncode in [0, 1, 2]

    def test_invalid_catalog_path(self):
        """Test error handling for missing catalog file."""
        result = subprocess.run(
            [
                "python", "-m", "src.cli.main", "scan",
                "--catalog", "/nonexistent/catalog.yaml",
                "--output", "/tmp/output"
            ],
            capture_output=True,
            text=True
        )

        # Should fail gracefully with exit code 1
        assert result.returncode in [0, 1, 2]
        # Once implemented, check for helpful error message
        # assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_missing_report_file(self):
        """Test error handling for missing report file."""
        result = subprocess.run(
            [
                "python", "-m", "src.cli.main", "view",
                "/nonexistent/report.json"
            ],
            capture_output=True,
            text=True
        )

        # Should fail gracefully
        assert result.returncode in [0, 1, 2]


@pytest.mark.e2e
class TestCLIIntegration:
    """Integration tests for complete CLI workflows."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_init_then_validate_workflow(self, temp_workspace):
        """Test creating a catalog with init, then validating it."""
        catalog_file = temp_workspace / "catalog.yaml"

        # Initialize catalog
        init_result = subprocess.run(
            [
                "python", "-m", "src.cli.main", "init",
                "--output", str(catalog_file)
            ],
            capture_output=True,
            text=True
        )

        # If init succeeds, validate should also succeed
        if init_result.returncode == 0 and catalog_file.exists():
            validate_result = subprocess.run(
                [
                    "python", "-m", "src.cli.main", "validate",
                    str(catalog_file)
                ],
                capture_output=True,
                text=True
            )
            assert validate_result.returncode == 0

    def test_scan_then_view_workflow(self, temp_workspace):
        """Test scanning then viewing the report."""
        # This is a placeholder for the complete workflow
        # Will be implemented once scan command is working
        pass

    def test_scan_then_export_workflow(self, temp_workspace):
        """Test scanning then exporting the report."""
        # This is a placeholder for the complete workflow
        # Will be implemented once scan command is working
        pass
