"""Scan command implementation.

Executes the error scanning workflow using Snakemake orchestration.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click
import yaml
from loguru import logger
from pydantic import ValidationError

from src.cli.types import FsspecPath
from src.domain.catalog import load_catalog
from src.reporting.jsonld import ReportGenerator


@click.command()
@click.option(
    "--catalog",
    required=True,
    type=FsspecPath(exists=True, dir_okay=False),
    help="Path or URI to error catalog YAML file (supports local paths, github://, ssh://, s3://, etc.)",
)
@click.option(
    "--output",
    default="./output",
    type=click.Path(file_okay=False, resolve_path=True),
    help="Output directory for results [default: ./output]",
)
@click.option("--cores", default=4, type=int, help="Number of CPU cores for Snakemake [default: 4]")
@click.option("--dryrun", is_flag=True, help="Show workflow plan without executing")
@click.option("--force", is_flag=True, help="Force re-execution of all rules")
@click.option("--verbose", "-v", count=True, help="Increase verbosity (can be repeated: -v for DEBUG, -vv for TRACE)")
def scan(catalog, output, cores, dryrun, force, verbose):
    """Run error scanning workflow.

    This command executes the full scanning pipeline:

    \b
    1. Loads and validates the error catalog
    2. Discovers files matching patterns
    3. Scans files for error patterns
    4. Evaluates railway pattern conditions
    5. Generates JSON-LD report

    Example:
        $ autosubmit-scan scan --catalog errors.yaml --output ./results --cores 8
    """
    try:
        # Set log level based on verbose flag
        # Remove existing handlers and reconfigure with new level
        logger.remove()
        if verbose >= 2:
            logger.add(sys.stderr, level="TRACE", format="<level>{level:8}</level> | <level>{message}</level>")
        elif verbose == 1:
            logger.add(sys.stderr, level="DEBUG", format="<level>{level:8}</level> | <level>{message}</level>")
        else:
            logger.add(sys.stderr, level="INFO", format="<level>{level:8}</level> | <level>{message}</level>")

        # Load and validate catalog
        logger.info(f"Loading catalog from {catalog}")
        try:
            error_catalog = load_catalog(catalog)
        except FileNotFoundError:
            logger.error(f"Catalog file not found: {catalog}")
            logger.info("Use 'autosubmit-scan init' to create a sample catalog")
            sys.exit(1)
        except ValidationError as e:
            logger.error(f"Invalid catalog format: {e}")
            logger.info("Use 'autosubmit-scan validate' to check your catalog")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            sys.exit(1)

        logger.success(f"Loaded catalog '{error_catalog.metadata.name}' with {len(error_catalog.errors)} error definitions")

        # Debug output for verbose mode
        if verbose >= 1:
            logger.debug("=" * 80)
            logger.debug("RENDERED CATALOG")
            logger.debug("=" * 80)
            logger.debug(f"Variables extracted: {error_catalog.metadata.variables if error_catalog.metadata.variables else 'None'}")
            logger.debug("")
            for error_id, error_def in error_catalog.errors.items():
                logger.debug(f"Error: {error_id}")
                logger.debug(f"  Pattern: {error_def.pattern.type} - {error_def.pattern.pattern}")
                logger.debug(f"  Files ({len(error_def.files)}):")
                for file_uri in error_def.files[:3]:  # Show first 3
                    logger.debug(f"    - {file_uri}")
                if len(error_def.files) > 3:
                    logger.debug(f"    ... and {len(error_def.files) - 3} more")
                logger.debug(f"  Meaning: {error_def.meaning}")
                logger.debug("")
            logger.debug("=" * 80)

        # Create output directories
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create workflow configuration
        config_data = {
            "catalog_path": str(catalog),
            "output_dirs": {
                "manifests": str(output_path / "manifests"),
                "fingerprints": str(output_path / "fingerprints"),
                "matches": str(output_path / "matches"),
                "filtered": str(output_path / "filtered"),
                "results": str(output_path / "results"),
                "aggregated": str(output_path / "aggregated"),
                "railway": str(output_path / "railway"),
            },
        }

        # Write temporary config file
        config_file = output_path / "workflow_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False)

        logger.info(f"Created workflow configuration at {config_file}")

        # Get Snakefile path
        snakefile_path = Path(__file__).parent.parent.parent / "orchestration" / "Snakefile"
        if not snakefile_path.exists():
            logger.error(f"Snakefile not found at {snakefile_path}")
            sys.exit(1)

        # Build Snakemake command
        cmd = [
            "snakemake",
            "--snakefile",
            str(snakefile_path),
            "--configfile",
            str(config_file),
            "--cores",
            str(cores),
            "--printshellcmds",
        ]

        if dryrun:
            cmd.append("--dryrun")
            cmd.append("--quiet")

        if force:
            cmd.append("--forceall")

        # Execute Snakemake
        if dryrun:
            logger.info("Performing dry run (no files will be modified)")
        else:
            logger.info(f"Starting workflow with {cores} cores")

        logger.debug(f"Executing: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error("Workflow execution failed")
            logger.error(result.stderr)
            if result.stdout:
                logger.debug(f"Stdout: {result.stdout}")
            sys.exit(1)

        if dryrun:
            logger.success("Dry run completed successfully")
            if result.stdout:
                print("\n" + result.stdout)
            return

        logger.success("Workflow completed successfully")

        # Generate JSON-LD report
        logger.info("Generating JSON-LD report")

        # Load all aggregated matches
        all_matches = []
        aggregated_dir = output_path / "aggregated"

        if aggregated_dir.exists():
            for match_file in aggregated_dir.glob("*_all_matches.json"):
                try:
                    with open(match_file) as f:
                        file_matches = json.load(f)

                    # Convert JSON to ErrorMatch objects
                    from src.domain.models import ErrorMatch

                    for match_data in file_matches:
                        # Parse timestamp
                        if isinstance(match_data.get("timestamp"), str):
                            match_data["timestamp"] = datetime.fromisoformat(match_data["timestamp"].replace("Z", "+00:00"))
                        match = ErrorMatch(**match_data)
                        all_matches.append(match)

                except Exception as e:
                    logger.warning(f"Failed to load matches from {match_file}: {e}")

        logger.info(f"Collected {len(all_matches)} total error matches")

        # Generate report
        generator = ReportGenerator()
        report = generator.generate_report(
            matches=all_matches,
            catalog=error_catalog,
            metadata={
                "author": {"name": error_catalog.metadata.author, "email": ""},
                "description": f"Scan results for {error_catalog.metadata.name}",
            },
        )

        # Save report
        report_path = output_path / "report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.success(f"Report saved to {report_path}")

        # Display summary
        summary = report["summary"]
        logger.info("=" * 60)
        logger.info("SCAN SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total matches: {summary['totalMatches']}")
        logger.info(f"Error types detected: {summary['errorTypes']}")
        logger.info(f"Files scanned: {summary['filesScanned']}")
        if summary.get("hostsScanned"):
            logger.info(f"Hosts scanned: {', '.join(summary['hostsScanned'])}")
        logger.info("=" * 60)

        # Suggest next steps
        logger.info("\nNext steps:")
        logger.info(f"  View results:   autosubmit-scan view {report_path}")
        logger.info(f"  Export report:  autosubmit-scan export {report_path} --template markdown")

    except KeyboardInterrupt:
        logger.warning("Scan interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error during scan: {e}")
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)
