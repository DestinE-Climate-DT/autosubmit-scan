"""Export command implementation.

Exports error reports using Jinja2 templates.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import click
from jinja2 import TemplateNotFound
from loguru import logger

from src.reporting.templates import TemplateRenderer


@click.command()
@click.argument("report_path", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option(
    "--template",
    type=click.Choice(["markdown", "html", "text"], case_sensitive=False),
    default="markdown",
    help="Output template format [default: markdown]",
)
@click.option(
    "--output", type=click.Path(dir_okay=False, resolve_path=True), help="Output file path (default: report.<extension>)"
)
def export(report_path, template, output):
    """Export error report using a template.

    Renders the JSON-LD report using the specified template format.
    Available templates:

    \b
    - markdown: Markdown format (.md)
    - html:     HTML format (.html)
    - text:     Plain text summary (.txt)

    Example:
        $ autosubmit-scan export ./output/report.json --template markdown --output report.md
        $ autosubmit-scan export ./output/report.json --template html
    """
    try:
        # Validate report file
        report_file = Path(report_path)
        if not report_file.exists():
            logger.error(f"Report file not found: {report_path}")
            logger.info("Use 'autosubmit-scan scan' to generate a report first")
            sys.exit(1)

        # Load report
        logger.info(f"Loading report from {report_path}")
        try:
            with open(report_file) as f:
                report_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON file: {e}")
            sys.exit(1)

        # Validate report structure
        if "@type" not in report_data or report_data.get("@type") != "ErrorReport":
            logger.error("File doesn't appear to be an error report (missing @type: ErrorReport)")
            sys.exit(1)

        # Determine output path
        if output is None:
            extensions = {"markdown": "md", "html": "html", "text": "txt"}
            output = report_file.parent / f"report.{extensions[template]}"
        else:
            output = Path(output)

        # Determine template file
        template_files = {"markdown": "report.md.j2", "html": "report.html.j2", "text": "summary.txt.j2"}
        template_file = template_files[template]

        logger.info(f"Using template: {template_file}")

        # Parse report data for template
        # Extract matches
        matches_data = []
        if "hasPart" in report_data:
            for match in report_data["hasPart"]:
                # Extract key information
                match_info = {
                    "error_id": match.get("errorDefinition", "unknown"),
                    "file_uri": match.get("url", "unknown"),
                    "line_number": match.get("position", 0),
                    "matched_text": match.get("text", ""),
                    "date_found": match.get("dateFound", ""),
                    "context_before": match.get("context", {}).get("before", []),
                    "context_after": match.get("context", {}).get("after", []),
                    "meaning": match.get("about", {}).get("headline", ""),
                    "suggestion": match.get("about", {}).get("description", ""),
                }
                matches_data.append(match_info)

        # Group matches by error type
        matches_by_error = {}
        for match in matches_data:
            error_id = match["error_id"]
            if error_id not in matches_by_error:
                matches_by_error[error_id] = []
            matches_by_error[error_id].append(match)

        # Prepare template data
        template_data = {
            "report": report_data,
            "summary": report_data.get("summary", {}),
            "matches": matches_data,
            "matches_by_error": matches_by_error,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_date": report_data.get("dateCreated", ""),
                "author": report_data.get("author", {}).get("name", "Unknown"),
            },
        }

        # Render template
        logger.info(f"Rendering {template} template")
        try:
            renderer = TemplateRenderer()
            renderer.render(template_file, template_data, str(output))
        except TemplateNotFound:
            logger.error(f"Template not found: {template_file}")
            logger.info("Available templates: markdown, html, text")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            logger.debug("Full traceback:", exc_info=True)
            sys.exit(1)

        logger.success(f"Report exported to {output}")

        # Show file size
        file_size = output.stat().st_size
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"

        logger.info(f"File size: {size_str}")

    except KeyboardInterrupt:
        logger.warning("Export interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error during export: {e}")
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)
