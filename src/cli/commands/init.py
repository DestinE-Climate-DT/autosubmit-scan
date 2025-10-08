"""Init command implementation.

Creates a sample error catalog to get started.
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone

import click
import questionary
import yaml
from loguru import logger
from prompt_toolkit.shortcuts import prompt

from ..completion import GlobPatternCompleter


def _create_interactive_catalog(output_path: Path) -> None:
    """Create a catalog interactively using questionary prompts."""
    logger.info("Creating error catalog interactively...")
    logger.info("Press Ctrl+C at any time to cancel\n")

    # Catalog metadata
    catalog_name = questionary.text(
        "Catalog name:",
        default="My Error Catalog"
    ).ask()

    catalog_description = questionary.text(
        "Description:",
        default="Error patterns for monitoring"
    ).ask()

    author = questionary.text(
        "Author:",
        default="Your Name"
    ).ask()

    # Error definition
    error_id = questionary.text(
        "\nError ID (unique identifier, e.g., 'oom_error'):",
        validate=lambda text: len(text) > 0 and text.replace("_", "").isalnum()
    ).ask()

    pattern_type = questionary.select(
        "Pattern type:",
        choices=["literal", "regex", "callable"]
    ).ask()

    pattern_value = questionary.text(
        f"Pattern ({pattern_type}):",
        default="ERROR" if pattern_type == "literal" else "ERROR|FATAL" if pattern_type == "regex" else "module:function"
    ).ask()

    # File URIs
    logger.info("\nSpecify files to scan (use Tab for completion):")
    logger.info("  - Start typing a protocol: ssh://, sftp://, s3://, or /")
    logger.info("  - Tab-complete paths and add glob patterns like **/*.log")
    logger.info("  - Press Enter on empty line to finish")

    files = []
    completer = GlobPatternCompleter()

    while True:
        # Use prompt_toolkit's prompt with our custom completer
        try:
            file_uri = prompt(
                f"\nFile URI #{len(files) + 1}: ",
                completer=completer,
                complete_while_typing=False,
                default="" if files else "ssh://"
            )
        except KeyboardInterrupt:
            raise
        except EOFError:
            # Ctrl+D was pressed
            break

        # Strip whitespace
        file_uri = file_uri.strip()

        if not file_uri:
            break
        files.append(file_uri)

    if not files:
        logger.error("At least one file URI is required")
        sys.exit(1)

    meaning = questionary.text(
        "\nError meaning:",
        default="Critical error detected"
    ).ask()

    suggestion = questionary.text(
        "Suggested action:",
        default="Review logs and take appropriate action"
    ).ask()

    context_lines = questionary.text(
        "Context lines (before/after match):",
        default="5",
        validate=lambda text: text.isdigit() and int(text) >= 0
    ).ask()

    severity = questionary.select(
        "Severity:",
        choices=["low", "medium", "high", "critical"]
    ).ask()

    # Build catalog structure
    now = datetime.now(timezone.utc).isoformat()

    pattern_dict = {"type": pattern_type, "pattern": pattern_value}
    if pattern_type == "regex":
        pattern_dict["flags"] = ["IGNORECASE"]

    catalog = {
        "version": "1.0.0",
        "schema_version": "1.0.0",
        "metadata": {
            "name": catalog_name,
            "description": catalog_description,
            "author": author,
            "created": now,
            "updated": now
        },
        "errors": {
            error_id: {
                "id": error_id,
                "pattern": pattern_dict,
                "files": files,
                "meaning": meaning,
                "suggestion": suggestion,
                "context_lines": int(context_lines),
                "next_errors": [],
                "metadata": {
                    "severity": severity
                }
            }
        }
    }

    # Create parent directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write catalog
    with open(output_path, 'w') as f:
        yaml.dump(catalog, f, default_flow_style=False, sort_keys=False)

    logger.success(f"\nCatalog created: {output_path}")
    _display_next_steps(output_path)


def _copy_sample_catalog(output_path: Path) -> None:
    """Copy the sample catalog to the output path."""
    # Find sample catalog
    src_dir = Path(__file__).parent.parent.parent
    sample_catalog = src_dir.parent / "examples" / "sample_catalog.yaml"

    if not sample_catalog.exists():
        logger.error(f"Sample catalog not found at: {sample_catalog}")
        logger.error("This is likely a packaging issue. Please report this bug.")
        sys.exit(1)

    # Create parent directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy sample catalog
    logger.info(f"Creating sample catalog at {output_path}")
    shutil.copy(sample_catalog, output_path)

    logger.success(f"Sample catalog created: {output_path}")
    _display_next_steps(output_path)


def _display_next_steps(output_path: Path) -> None:
    """Display next steps after creating catalog."""
    logger.info("\n" + "=" * 60)
    logger.info("NEXT STEPS")
    logger.info("=" * 60)
    logger.info(f"1. Review and edit the catalog:")
    logger.info(f"   $ $EDITOR {output_path}")
    logger.info("")
    logger.info(f"2. Validate your catalog:")
    logger.info(f"   $ as-scan validate {output_path}")
    logger.info("")
    logger.info(f"3. Run a scan:")
    logger.info(f"   $ as-scan scan --catalog {output_path} --output ./results")
    logger.info("")
    logger.info("=" * 60)


@click.command()
@click.option(
    "--output",
    type=click.Path(dir_okay=False, resolve_path=True),
    default="./error_catalog.yaml",
    help="Output path for the sample catalog [default: ./error_catalog.yaml]"
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing file if present"
)
@click.option(
    "--interactive",
    is_flag=True,
    help="Create catalog interactively with questionary prompts"
)
@click.option(
    "--sample",
    is_flag=True,
    help="Copy the sample catalog (default if not --interactive)"
)
def init(output, force, interactive, sample):
    """Create an error catalog.

    By default, creates a catalog interactively. Use --sample to copy
    the full sample catalog instead.

    \b
    Interactive mode guides you through creating an error definition:
    - Error ID and description
    - Pattern type (literal, regex, or callable)
    - File paths/URIs to scan
    - Context lines and metadata

    Example:
        $ as-scan init
        $ as-scan init --output my_catalog.yaml
        $ as-scan init --sample --output example.yaml
    """
    try:
        output_path = Path(output)

        # Check if file exists
        if output_path.exists() and not force:
            logger.error(f"File already exists: {output_path}")
            logger.info("Use --force to overwrite, or choose a different path")
            sys.exit(1)

        # Default to interactive if neither flag is specified
        if not interactive and not sample:
            interactive = True

        if interactive:
            _create_interactive_catalog(output_path)
        else:
            _copy_sample_catalog(output_path)

    except KeyboardInterrupt:
        logger.warning("Init interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Failed to create sample catalog: {e}")
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)
