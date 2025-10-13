"""Main CLI entry point for autosubmit-scan.

Provides commands for scanning, viewing, exporting, validating, and initializing
error catalogs.
"""

import sys

import click
from loguru import logger

# Will be populated after commands are registered
SUBCOMMAND_NAMES = set()

# Configure loguru for CLI
logger.remove()  # Remove default handler
logger.add(sys.stderr, format="<level>{level: <8}</level> | <level>{message}</level>", level="INFO", colorize=True)


@click.group()
@click.version_option(version="bleeding-edge (paul.gierz@awi.de)", prog_name="as-scan")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.option("-q", "--quiet", is_flag=True, help="Suppress all non-error output")
def cli(verbose, quiet):
    """Remote Error Monitoring System.

    A comprehensive tool for scanning, analyzing, and reporting on errors
    in remote log files using pattern matching and workflow orchestration.

    \b
    Quick Start (Autosubmit experiments):
      $ as-scan a23i              # Scan experiment a23i with default checks

    \b
    Common workflows:
      1. Initialize a new catalog interactively:
         $ as-scan init

      2. Add errors to an existing catalog:
         $ as-scan add my_catalog.yaml

      3. Validate your catalog:
         $ as-scan validate my_catalog.yaml

      4. Visualize workflow DAG:
         $ as-scan dag --catalog my_catalog.yaml --output dag.png --format png

      5. Run a scan:
         $ as-scan scan --catalog my_catalog.yaml --output ./results

      6. View results interactively:
         $ as-scan view ./results/report.json

      7. Export to markdown:
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
            colorize=True,
        )
    elif quiet:
        logger.remove()
        logger.add(sys.stderr, level="ERROR", colorize=True)


# Import command modules
from src.cli.commands.add import add
from src.cli.commands.dag import dag
from src.cli.commands.default import default
from src.cli.commands.export import export
from src.cli.commands.init import init
from src.cli.commands.scan import scan
from src.cli.commands.validate import validate
from src.cli.commands.view import view

# Register commands
cli.add_command(scan)
cli.add_command(view)
cli.add_command(export)
cli.add_command(validate)
cli.add_command(init)
cli.add_command(add)
cli.add_command(dag)
cli.add_command(default)  # Hidden command for expid shortcut

# Populate subcommand names for shortcut detection
SUBCOMMAND_NAMES.update(["scan", "view", "export", "validate", "init", "add", "dag", "default"])


def main():
    """Main entry point for CLI."""
    # Handle expid shortcut: if first arg is not a known subcommand, inject "default"
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        # Check if first arg is not an option and not a known subcommand
        if not first_arg.startswith("-") and first_arg not in SUBCOMMAND_NAMES:
            # Insert "default" as the command, keep the expid as its argument
            logger.debug(f"Detected expid shortcut: {first_arg}")
            sys.argv.insert(1, "default")

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
