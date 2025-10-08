"""View command implementation.

Launches the Textual TUI for interactive report viewing.
"""

import sys
from pathlib import Path

import click
from loguru import logger

from src.reporting.tui import ErrorReportApp


@click.command()
@click.argument(
    "report_path",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
def view(report_path):
    """Launch TUI to view error report interactively.

    Opens a terminal user interface for browsing error matches with:
    - Hierarchical tree view (by error type and file)
    - Detail panel with match context
    - Keyboard navigation

    \b
    Navigation:
    - Arrow keys: Navigate tree
    - Enter: Expand/collapse nodes
    - q: Quit
    - /: Search (future)
    - f: Filter (future)

    Example:
        $ autosubmit-scan view ./output/report.json
    """
    try:
        # Validate report file
        report_file = Path(report_path)
        if not report_file.exists():
            logger.error(f"Report file not found: {report_path}")
            logger.info("Use 'autosubmit-scan scan' to generate a report first")
            sys.exit(1)

        # Check if it's a JSON file
        if report_file.suffix.lower() not in [".json", ".jsonld"]:
            logger.error(f"Report must be a JSON file, got: {report_file.suffix}")
            sys.exit(1)

        # Try to validate it's a valid JSON
        import json
        try:
            with open(report_file, "r") as f:
                data = json.load(f)

            # Check if it looks like a report
            if "@type" not in data or data.get("@type") != "ErrorReport":
                logger.warning("File doesn't appear to be an error report (missing @type: ErrorReport)")
                logger.info("Attempting to display anyway...")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON file: {e}")
            sys.exit(1)

        # Launch TUI
        logger.info(f"Loading report from {report_path}")
        app = ErrorReportApp(str(report_path))

        try:
            app.run()
        except KeyboardInterrupt:
            logger.info("TUI closed by user")

    except KeyboardInterrupt:
        logger.info("View interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Failed to view report: {e}")
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)
