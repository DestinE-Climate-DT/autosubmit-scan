"""Add command implementation.

Adds a new error definition to an existing catalog interactively.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

import click
import questionary
import yaml
from loguru import logger
from prompt_toolkit.shortcuts import prompt
from pydantic import ValidationError

from src.domain.catalog import load_catalog
from ..completion import GlobPatternCompleter


@click.command()
@click.argument(
    "catalog",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, resolve_path=True),
    help="Save to a different file (default: update catalog in-place)"
)
def add(catalog, output):
    """Add a new error definition to an existing catalog.

    Interactively guides you through creating a new error definition
    and adds it to the specified catalog.

    \b
    The interactive prompts will ask for:
    - Error ID (unique identifier)
    - Pattern type and value
    - File paths/URIs to scan
    - Error description and suggested action
    - Context lines and severity

    \b
    Examples:
        # Add error to existing catalog
        $ as-scan add my_catalog.yaml

        # Add error and save to new file
        $ as-scan add my_catalog.yaml --output updated_catalog.yaml
    """
    try:
        catalog_path = Path(catalog)

        # Load existing catalog
        logger.info(f"Loading catalog from {catalog_path}")
        try:
            error_catalog = load_catalog(str(catalog_path))
        except FileNotFoundError:
            logger.error(f"Catalog file not found: {catalog_path}")
            sys.exit(1)
        except ValidationError as e:
            logger.error(f"Invalid catalog format: {e}")
            logger.info("Use 'as-scan validate' to check your catalog")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            sys.exit(1)

        logger.success(f"Loaded catalog '{error_catalog.metadata.name}' with {len(error_catalog.errors)} existing error(s)")
        logger.info("\nCreating new error definition...")
        logger.info("Press Ctrl+C at any time to cancel\n")

        # Get new error ID
        existing_ids = list(error_catalog.errors.keys())

        while True:
            error_id = questionary.text(
                "Error ID (unique identifier, e.g., 'oom_error'):",
                validate=lambda text: len(text) > 0 and text.replace("_", "").isalnum()
            ).ask()

            if error_id in existing_ids:
                logger.error(f"Error ID '{error_id}' already exists in catalog")
                logger.info(f"Existing errors: {', '.join(existing_ids)}")
                retry = questionary.confirm("Try a different ID?", default=True).ask()
                if not retry:
                    logger.warning("Cancelled")
                    sys.exit(0)
            else:
                break

        # Pattern type
        pattern_type = questionary.select(
            "Pattern type:",
            choices=["literal", "regex", "callable"]
        ).ask()

        # Pattern value with smart defaults
        if pattern_type == "literal":
            default_pattern = "ERROR"
        elif pattern_type == "regex":
            default_pattern = "ERROR|FATAL|CRITICAL"
        else:
            default_pattern = "module:function"

        pattern_value = questionary.text(
            f"Pattern ({pattern_type}):",
            default=default_pattern
        ).ask()

        # File URIs with tab completion
        logger.info("\nSpecify files to scan (use Tab for completion):")
        logger.info("  - Start typing a protocol: ssh://, sftp://, s3://, or /")
        logger.info("  - Tab-complete paths and add glob patterns like **/*.log")
        logger.info("  - Press Enter on empty line to finish")

        files = []
        completer = GlobPatternCompleter()

        while True:
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
                break

            file_uri = file_uri.strip()
            if not file_uri:
                break
            files.append(file_uri)

        if not files:
            logger.error("At least one file URI is required")
            sys.exit(1)

        # Error metadata
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

        # Build pattern dict
        pattern_dict = {"type": pattern_type, "pattern": pattern_value}
        if pattern_type == "regex":
            # Ask about regex flags
            use_ignorecase = questionary.confirm(
                "Use case-insensitive matching?",
                default=True
            ).ask()
            if use_ignorecase:
                pattern_dict["flags"] = ["IGNORECASE"]

        # Build new error definition
        new_error = {
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

        # Load raw YAML to preserve structure and comments
        with open(catalog_path, 'r') as f:
            catalog_dict = yaml.safe_load(f)

        # Add new error
        catalog_dict["errors"][error_id] = new_error

        # Update timestamp
        catalog_dict["metadata"]["updated"] = datetime.now(timezone.utc).isoformat()

        # Determine output path
        output_path = Path(output) if output else catalog_path

        # Confirm before saving
        if output_path == catalog_path:
            logger.info(f"\nWill update {output_path} with new error '{error_id}'")
        else:
            logger.info(f"\nWill save catalog with new error '{error_id}' to {output_path}")

        confirm = questionary.confirm("Proceed?", default=True).ask()
        if not confirm:
            logger.warning("Cancelled")
            sys.exit(0)

        # Write updated catalog
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(catalog_dict, f, default_flow_style=False, sort_keys=False)

        logger.success(f"\n✓ Added error '{error_id}' to catalog")
        logger.success(f"✓ Saved to {output_path}")

        # Display summary
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Catalog now contains {len(catalog_dict['errors'])} error definition(s):")
        for err_id in catalog_dict['errors'].keys():
            marker = "NEW" if err_id == error_id else ""
            logger.info(f"  - {err_id} {marker}")
        logger.info("=" * 60)

        # Next steps
        logger.info("\nNext steps:")
        logger.info(f"  1. Validate: as-scan validate {output_path}")
        logger.info(f"  2. Run scan: as-scan scan --catalog {output_path} --output ./results")

    except KeyboardInterrupt:
        logger.warning("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Failed to add error to catalog: {e}")
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)
