"""CLI command stubs for report viewing and export.

These commands will be integrated into the main CLI in Iteration 6.
"""

from pathlib import Path


def view_command(report_path: str) -> None:
    """Launch TUI to view error report interactively.

    Args:
        report_path: Path to JSON-LD report file

    Raises:
        FileNotFoundError: If report file doesn't exist
    """
    path = Path(report_path)

    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    # Import here to avoid circular dependencies
    from src.reporting.tui import ErrorReportApp

    # Load report and launch TUI
    app = ErrorReportApp(report_path)
    app.run()


def export_command(report_path: str, template: str, output: str, format: str | None = None) -> None:
    """Export error report using a template.

    Args:
        report_path: Path to JSON-LD report file
        template: Name of template to use (or path to custom template)
        output: Path for output file
        format: Output format (markdown, html, text). If None, inferred from template

    Raises:
        FileNotFoundError: If report or template file doesn't exist
    """
    path = Path(report_path)

    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    # Import here to avoid circular dependencies
    import json

    from src.reporting.templates import TemplateRenderer

    # Load report
    with open(path, encoding="utf-8") as f:
        report_data = json.load(f)

    # Determine template name
    if not template.endswith(".j2"):
        # Map common names to template files
        template_map = {
            "markdown": "report.md.j2",
            "md": "report.md.j2",
            "html": "report.html.j2",
            "text": "summary.txt.j2",
            "txt": "summary.txt.j2",
        }
        template_name = template_map.get(template, f"{template}.j2")
    else:
        template_name = template

    # Render template
    renderer = TemplateRenderer()
    renderer.render(template_name, report_data, output)

    print(f"Report exported to: {output}")
