"""Check SSH connection pooling configuration.

Verifies that SSH ControlMaster is properly configured for efficient
connection pooling when scanning remote files.
"""

import subprocess
import sys
from pathlib import Path

import click
from loguru import logger


@click.command(name="check-ssh")
@click.argument("hostname", required=False, default="climatedt-wf")
@click.option(
    "--quiet", "-q", is_flag=True, help="Only show errors and warnings (suppress info messages)"
)
def check_ssh(hostname: str, quiet: bool):
    """Check SSH connection pooling configuration.

    Verifies that SSH ControlMaster is properly configured for efficient
    remote file scanning. ControlMaster allows multiple SSH sessions to
    share a single network connection, dramatically reducing connection
    overhead.

    \b
    Without ControlMaster:  44+ connections per scan  → high timeout risk
    With ControlMaster:     1-2 connections per scan  → low timeout risk

    Examples:
        # Check default host (climatedt-wf)
        as-scan check-ssh

        # Check specific host
        as-scan check-ssh mn5

        # Quiet mode (only show warnings/errors)
        as-scan check-ssh --quiet
    """
    if quiet:
        logger.remove()
        logger.add(sys.stderr, level="WARNING")
    else:
        logger.info(f"Checking SSH connection pooling for host: {hostname}")

    # Find the check script
    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "check_ssh_pooling.sh"

    if not script_path.exists():
        logger.error(f"Check script not found: {script_path}")
        logger.error("Please ensure the autosubmit-scan repository is complete")
        sys.exit(1)

    # Run the check script
    try:
        result = subprocess.run(
            [str(script_path), hostname],
            check=False,  # Don't raise on non-zero exit
            capture_output=False,  # Show output directly
        )

        sys.exit(result.returncode)

    except FileNotFoundError:
        logger.error("Failed to execute check script (bash not found?)")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
