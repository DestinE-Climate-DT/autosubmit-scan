"""Init command implementation.

Creates a sample error catalog to get started.
"""

import sys
import shutil
from pathlib import Path

import click
from loguru import logger


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
def init(output, force):
    """Create a sample error catalog.

    Creates a new catalog file based on the sample catalog template.
    The sample includes examples of:

    \b
    - Different pattern types (literal, regex, callable)
    - Various file URI schemes (local, S3, SFTP, FTP)
    - Railway pattern with conditional chaining
    - Error metadata and suggestions

    Example:
        $ autosubmit-scan init
        $ autosubmit-scan init --output my_catalog.yaml
        $ autosubmit-scan init --output my_catalog.yaml --force
    """
    try:
        output_path = Path(output)

        # Check if file exists
        if output_path.exists() and not force:
            logger.error(f"File already exists: {output_path}")
            logger.info("Use --force to overwrite, or choose a different path")
            sys.exit(1)

        # Find sample catalog
        # Look in examples/ directory relative to this file
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

        # Display next steps
        logger.info("\n" + "=" * 60)
        logger.info("NEXT STEPS")
        logger.info("=" * 60)
        logger.info(f"1. Review and edit the catalog:")
        logger.info(f"   $ $EDITOR {output_path}")
        logger.info("")
        logger.info(f"2. Validate your catalog:")
        logger.info(f"   $ autosubmit-scan validate {output_path}")
        logger.info("")
        logger.info(f"3. Run a scan:")
        logger.info(f"   $ autosubmit-scan scan --catalog {output_path} --output ./results")
        logger.info("")
        logger.info("For more information, see the User Guide:")
        logger.info("  $ cat docs/USER_GUIDE.md")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("Init interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Failed to create sample catalog: {e}")
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)
