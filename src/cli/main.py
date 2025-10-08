"""Main CLI entry point for autosubmit-scan.

Provides commands for scanning, viewing, exporting, validating, and initializing
error catalogs.
"""

import sys
import click
from loguru import logger

# Configure loguru for CLI
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True
)


@click.group()
@click.version_option(version="0.1.0", prog_name="as-scan")
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Enable verbose logging"
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress all non-error output"
)
def cli(verbose, quiet):
    """Remote Error Monitoring System.

    A comprehensive tool for scanning, analyzing, and reporting on errors
    in remote log files using pattern matching and workflow orchestration.

    \b
    Common workflows:
      1. Initialize a new catalog interactively:
         $ as-scan init

      2. Validate your catalog:
         $ as-scan validate my_catalog.yaml

      3. Run a scan:
         $ as-scan scan --catalog my_catalog.yaml --output ./results

      4. View results interactively:
         $ as-scan view ./results/report.json

      5. Export to markdown:
         $ as-scan export ./results/report.json --template markdown --output report.md

    \b
    Supported file URIs:
      - SSH:   ssh://user@host/path/to/logs/**/*.log
      - SFTP:  sftp://user@host/path/to/logs/**/*.out
      - Local: /var/log/**/*.log
      - S3:    s3://bucket/prefix/**/*.log
    """
    # Configure logging level
    if verbose:
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level="DEBUG",
            colorize=True
        )
    elif quiet:
        logger.remove()
        logger.add(sys.stderr, level="ERROR", colorize=True)


# Import command modules
from src.cli.commands.scan import scan
from src.cli.commands.view import view
from src.cli.commands.export import export
from src.cli.commands.validate import validate
from src.cli.commands.init import init

# Register commands
cli.add_command(scan)
cli.add_command(view)
cli.add_command(export)
cli.add_command(validate)
cli.add_command(init)


def main():
    """Main entry point for CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
