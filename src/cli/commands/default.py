"""Default command implementation.

Runs a default scan for an Autosubmit experiment using a templated catalog.
"""

import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import click
from loguru import logger
from pydantic import ValidationError

from src.domain.catalog import load_catalog
from src.domain.templates import load_template, render_template

# Default catalog template URI - can be overridden with environment variable
DEFAULT_TEMPLATE_URI = os.getenv(
    "AUTOSUBMIT_SCAN_DEFAULT_TEMPLATE",
    "github://DestinE-Climate-DT:autosubmit-scan-error-catalogs@main/templates/default_autosubmit.yaml",
)

# ⚠️ INTERNAL FALLBACK TEMPLATE - DO NOT EDIT ⚠️
# This is used only when remote template loading fails.
# The canonical template is maintained at:
# https://github.com/DestinE-Climate-DT/autosubmit-scan-error-catalogs
FALLBACK_CATALOG_TEMPLATE = """
#############################################################################
# ⚠️  WARNING: INTERNAL FALLBACK TEMPLATE - FOR EMERGENCY USE ONLY  ⚠️
#
# This template is embedded in the code as a fallback when the remote
# template cannot be loaded. DO NOT rely on this for production use.
#
# The canonical, maintained template is at:
# https://github.com/DestinE-Climate-DT/autosubmit-scan-error-catalogs
#
# To use the latest template from the repository, ensure you have network
# access or set AUTOSUBMIT_SCAN_DEFAULT_TEMPLATE to a local/cached copy.
#############################################################################

version: 1.0.0
schema_version: 1.0.0
metadata:
  name: "Autosubmit Scan for {{ expid }} (INTERNAL FALLBACK)"
  description: "Emergency fallback error checks for Autosubmit experiment {{ expid }}"
  author: "{{ user }}"
  created: "{{ timestamp }}"
  updated: "{{ timestamp }}"

errors:
  OOMError:
    id: OOMError
    pattern:
      type: regex
      pattern: "Out of memory|OOM|oom-kill|Killed process"
      flags: ["IGNORECASE"]
    files:
      - ssh://{{ host }}:{{ base_path }}/{{ expid }}/LOG_{{ expid }}/*.out
      - ssh://{{ host }}:{{ base_path }}/{{ expid }}/LOG_{{ expid }}/*.err
    meaning: "Job was killed due to out-of-memory condition"
    suggestion: "Increase memory allocation or optimize memory usage"
    context_lines: 10
    next_errors: []
    metadata:
      severity: high

  TimeoutError:
    id: TimeoutError
    pattern:
      type: regex
      pattern: "TIMEOUT|TIME LIMIT|CANCELLED|DUE TO TIME LIMIT"
      flags: ["IGNORECASE"]
    files:
      - ssh://{{ host }}:{{ base_path }}/{{ expid }}/LOG_{{ expid }}/*.out
      - ssh://{{ host }}:{{ base_path }}/{{ expid }}/LOG_{{ expid }}/*.err
    meaning: "Job exceeded time limit and was cancelled"
    suggestion: "Increase walltime or optimize performance"
    context_lines: 10
    next_errors: []
    metadata:
      severity: high

  SubmissionError:
    id: SubmissionError
    pattern:
      type: regex
      pattern: "sbatch.*failed|Unable to allocate resources|Invalid account|QOSMaxSubmitJobPerUserLimit"
      flags: ["IGNORECASE"]
    files:
      - ssh://{{ host }}:{{ base_path }}/{{ expid }}/LOG_{{ expid }}/*.out
      - ssh://{{ host }}:{{ base_path }}/{{ expid }}/LOG_{{ expid }}/*.err
    meaning: "Job submission failed"
    suggestion: "Check SLURM configuration, queue limits, and account settings"
    context_lines: 10
    next_errors: []
    metadata:
      severity: critical

  PythonError:
    id: PythonError
    pattern:
      type: regex
      pattern: 'Traceback \\(most recent call last\\)|^\\s*File .*, line [0-9]+'
      flags: ["MULTILINE"]
    files:
      - ssh://{{ host }}:{{ base_path }}/{{ expid }}/LOG_{{ expid }}/*.out
      - ssh://{{ host }}:{{ base_path }}/{{ expid }}/LOG_{{ expid }}/*.err
    meaning: "Python exception occurred during execution"
    suggestion: "Review traceback and fix code error"
    context_lines: 15
    next_errors: []
    metadata:
      severity: high

  SegmentationFault:
    id: SegmentationFault
    pattern:
      type: regex
      pattern: "Segmentation fault|segfault|SIGSEGV"
      flags: ["IGNORECASE"]
    files:
      - ssh://{{ host }}:{{ base_path }}/{{ expid }}/LOG_{{ expid }}/*.out
      - ssh://{{ host }}:{{ base_path }}/{{ expid }}/LOG_{{ expid }}/*.err
    meaning: "Program crashed with segmentation fault"
    suggestion: "Check for memory corruption, array bounds, or pointer issues"
    context_lines: 10
    next_errors: []
    metadata:
      severity: critical
"""


def get_default_template_variables(expid: str) -> dict:
    """Get default template variables for catalog rendering.

    Args:
        expid: Experiment ID

    Returns:
        Dictionary of template variables
    """
    # Get user from environment
    user = os.getenv("USER", "unknown")

    # Default host and base path for Autosubmit on MN5
    # These can be overridden by environment variables
    host = os.getenv("AUTOSUBMIT_HOST", "mn5")
    base_path = os.getenv("AUTOSUBMIT_BASE_PATH", "/gpfs/scratch/ehpc01/awi478153")

    return {
        "expid": expid,
        "user": user,
        "host": host,
        "base_path": base_path,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def run_default_scan(expid: str, cores: int = 4, verbose: int = 0):
    """Run default scan for an Autosubmit experiment.

    Args:
        expid: Experiment ID
        cores: Number of CPU cores for Snakemake
        verbose: Verbosity level (0=INFO, 1=DEBUG, 2=TRACE)
    """
    logger.info(f"Running default scan for experiment: {expid}")

    # Set environment variable for catalog's dynamic variable extraction
    # The catalog will extract all other details (including username) from Autosubmit metadata
    os.environ["AUTOSUBMIT_EXPID"] = expid

    # Note: HPCUSER is now extracted from experiment_data.yml automatically
    # Users can still override by setting: export AUTOSUBMIT_HPCUSER=myusername

    # Try to load catalog from remote URI (no template rendering needed - catalog has dynamic vars)
    catalog_path = None
    catalog_source = None

    try:
        logger.info(f"Loading catalog from: {DEFAULT_TEMPLATE_URI}")
        catalog_yaml = load_template(DEFAULT_TEMPLATE_URI)
        catalog_source = DEFAULT_TEMPLATE_URI
        logger.success("Loaded catalog from remote repository")

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            catalog_path = Path(f.name)
            f.write(catalog_yaml)

    except Exception as e:
        logger.warning(f"Failed to load remote catalog: {e}")
        logger.warning("Falling back to internal emergency template")

        # Fall back to old template with rendering
        variables = get_default_template_variables(expid)
        try:
            catalog_yaml = render_template(FALLBACK_CATALOG_TEMPLATE, variables)
            catalog_source = "internal fallback"
        except ValueError as e:
            logger.error(f"Failed to render fallback catalog: {e}")
            sys.exit(1)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            catalog_path = Path(f.name)
            f.write(catalog_yaml)

    logger.debug(f"Created temporary catalog: {catalog_path}")

    # Validate catalog
    try:
        catalog = load_catalog(str(catalog_path))
        logger.success(f"Loaded catalog with {len(catalog.errors)} default error checks")
    except ValidationError as e:
        logger.error(f"Invalid catalog template: {e}")
        if catalog_path.exists():
            catalog_path.unlink()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load catalog: {e}")
        if catalog_path.exists():
            catalog_path.unlink()
        sys.exit(1)

    # Create output directory
    output_dir = Path(f"./scan_results_{expid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Output directory: {output_dir}")

    # Save the rendered catalog for reference
    saved_catalog = output_dir / "catalog.yaml"
    with open(saved_catalog, "w") as f:
        f.write(catalog_yaml)
    logger.info(f"Saved catalog to: {saved_catalog}")

    # Run scan using the scan command
    from src.cli.commands.scan import scan

    logger.info("Starting scan workflow...")

    try:
        # Invoke scan command with the saved catalog
        ctx = click.Context(scan)
        ctx.invoke(
            scan,
            catalog=str(saved_catalog),  # Use persistent catalog path
            output=str(output_dir),
            cores=cores,
            dryrun=False,
            force=False,
            verbose=verbose,  # Pass through verbose flag
        )
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        sys.exit(1)
    finally:
        # Clean up temporary catalog file (if different from saved catalog)
        if catalog_path.exists() and catalog_path != saved_catalog:
            catalog_path.unlink()

    logger.success(f"\nScan completed for experiment {expid}")
    logger.info(f"Results saved to: {output_dir}")
    logger.info("\nNext steps:")
    logger.info(f"  View results: as-scan view {output_dir}/report.json")
    logger.info(f"  Export report: as-scan export {output_dir}/report.json --template markdown")


# Click command wrapper (hidden from help, used internally)
@click.command(name="default", hidden=True)
@click.argument("expid")
@click.option("--cores", default=4, type=int, help="Number of CPU cores for Snakemake [default: 4]")
@click.option("--verbose", "-v", count=True, help="Increase verbosity (can be repeated: -v for DEBUG, -vv for TRACE)")
def default(expid, cores, verbose):
    """Run default scan for an Autosubmit experiment (internal command)."""
    run_default_scan(expid, cores=cores, verbose=verbose)
