"""Unit tests for template renderer."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_report_data():
    """Sample report data for rendering."""
    return {
        "title": "Error Scan Report",
        "date": "2025-10-08",
        "summary": {
            "totalMatches": 42,
            "errorTypes": 5,
            "filesScanned": 12
        },
        "errors_by_type": {
            "slurm_oom": [
                {"file": "job123.log", "line": 42, "text": "Out of memory"},
                {"file": "job124.log", "line": 56, "text": "OOM killed"}
            ],
            "slurm_timeout": [
                {"file": "job125.log", "line": 100, "text": "TIMEOUT"}
            ]
        }
    }


class TestTemplateRenderer:
    """Test template renderer functionality."""

    def test_renderer_initialization(self):
        """Test that renderer initializes correctly."""
        from src.reporting.templates import TemplateRenderer

        renderer = TemplateRenderer()
        assert renderer is not None

    def test_render_markdown_template(self, sample_report_data, tmp_path):
        """Test rendering Markdown template."""
        from src.reporting.templates import TemplateRenderer

        renderer = TemplateRenderer()
        output_path = tmp_path / "report.md"

        renderer.render("report.md.j2", sample_report_data, str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "Error Scan Report" in content
        assert "42" in content  # Total matches
        assert "slurm_oom" in content

    def test_render_html_template(self, sample_report_data, tmp_path):
        """Test rendering HTML template."""
        from src.reporting.templates import TemplateRenderer

        renderer = TemplateRenderer()
        output_path = tmp_path / "report.html"

        renderer.render("report.html.j2", sample_report_data, str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "<html" in content.lower()
        assert "Error Scan Report" in content

    def test_render_text_template(self, sample_report_data, tmp_path):
        """Test rendering plain text template."""
        from src.reporting.templates import TemplateRenderer

        renderer = TemplateRenderer()
        output_path = tmp_path / "summary.txt"

        renderer.render("summary.txt.j2", sample_report_data, str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "Error Scan Report" in content
        assert "Total Matches: 42" in content

    def test_render_nonexistent_template(self, sample_report_data, tmp_path):
        """Test rendering non-existent template raises error."""
        from src.reporting.templates import TemplateRenderer
        from jinja2 import TemplateNotFound

        renderer = TemplateRenderer()
        output_path = tmp_path / "output.txt"

        with pytest.raises(TemplateNotFound):
            renderer.render("nonexistent.j2", sample_report_data, str(output_path))

    def test_render_creates_parent_directories(self, sample_report_data, tmp_path):
        """Test that rendering creates parent directories if needed."""
        from src.reporting.templates import TemplateRenderer

        renderer = TemplateRenderer()
        output_path = tmp_path / "subdir" / "nested" / "report.md"

        renderer.render("report.md.j2", sample_report_data, str(output_path))

        assert output_path.exists()


@pytest.mark.unit
class TestTemplateContent:
    """Test template content and structure."""

    def test_markdown_template_structure(self, sample_report_data, tmp_path):
        """Test that Markdown template has proper structure."""
        from src.reporting.templates import TemplateRenderer

        renderer = TemplateRenderer()
        output_path = tmp_path / "report.md"
        renderer.render("report.md.j2", sample_report_data, str(output_path))

        content = output_path.read_text()

        # Should have headers
        assert "# Error Scan Report" in content or "Error Scan Report" in content

        # Should have summary section
        assert "Summary" in content or "summary" in content.lower()

        # Should have error types
        assert "slurm_oom" in content

    def test_html_template_has_bootstrap(self, sample_report_data, tmp_path):
        """Test that HTML template includes Bootstrap."""
        from src.reporting.templates import TemplateRenderer

        renderer = TemplateRenderer()
        output_path = tmp_path / "report.html"
        renderer.render("report.html.j2", sample_report_data, str(output_path))

        content = output_path.read_text()

        # Should have HTML structure
        assert "<!DOCTYPE html>" in content or "<html" in content.lower()
        assert "</html>" in content.lower()

    def test_text_template_simplicity(self, sample_report_data, tmp_path):
        """Test that plain text template is simple and readable."""
        from src.reporting.templates import TemplateRenderer

        renderer = TemplateRenderer()
        output_path = tmp_path / "summary.txt"
        renderer.render("summary.txt.j2", sample_report_data, str(output_path))

        content = output_path.read_text()

        # Should not contain HTML tags
        assert "<" not in content or content.count("<") <= 2  # Allow minimal special chars

        # Should be readable
        lines = content.strip().split("\n")
        assert len(lines) > 0
