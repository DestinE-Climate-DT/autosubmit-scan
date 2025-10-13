"""Validate command implementation.

Validates error catalog files against the schema.
"""

import subprocess
import sys
from pathlib import Path

import click
import yaml
from loguru import logger
from pydantic import ValidationError

from src.domain.catalog import load_catalog


@click.command()
@click.argument("catalog_path", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option(
    "--schema", type=click.Path(exists=True, dir_okay=False, resolve_path=True), help="Path to JSON schema file (optional)"
)
def validate(catalog_path, schema):
    """Validate error catalog file.

    Validates the catalog against:
    1. YAML syntax
    2. Pydantic data models
    3. Optional JSON schema (if --schema provided)

    Exits with code 0 if valid, 1 if invalid.

    Example:
        $ autosubmit-scan validate my_catalog.yaml
        $ autosubmit-scan validate my_catalog.yaml --schema catalog_schema.json
    """
    try:
        catalog_file = Path(catalog_path)

        logger.info(f"Validating catalog: {catalog_file.name}")

        # Step 1: Validate YAML syntax
        logger.info("Checking YAML syntax...")
        try:
            with open(catalog_file) as f:
                yaml_data = yaml.safe_load(f)

            if yaml_data is None:
                logger.error("YAML file is empty")
                sys.exit(1)

            logger.success("YAML syntax is valid")

        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML syntax: {e}")
            sys.exit(1)

        # Step 2: Validate against Pydantic models
        logger.info("Validating against data models...")
        try:
            catalog = load_catalog(str(catalog_file))
            logger.success("Catalog structure is valid")

        except ValidationError as e:
            logger.error("Validation failed:")
            for error in e.errors():
                location = " -> ".join(str(x) for x in error["loc"])
                logger.error(f"  {location}: {error['msg']}")
            sys.exit(1)

        except Exception as e:
            logger.error(f"Validation error: {e}")
            sys.exit(1)

        # Step 3: Validate against JSON schema (if provided)
        if schema:
            logger.info("Validating against JSON schema...")
            schema_file = Path(schema)

            try:
                # Use check-jsonschema tool
                result = subprocess.run(
                    ["check-jsonschema", "--schemafile", str(schema_file), str(catalog_file)], capture_output=True, text=True
                )

                if result.returncode != 0:
                    logger.error("JSON schema validation failed:")
                    logger.error(result.stdout)
                    if result.stderr:
                        logger.error(result.stderr)
                    sys.exit(1)

                logger.success("JSON schema validation passed")

            except FileNotFoundError:
                logger.error("check-jsonschema tool not found")
                logger.info("Install with: pixi add check-jsonschema")
                sys.exit(1)

        # Display catalog info
        logger.info("=" * 60)
        logger.info("CATALOG INFORMATION")
        logger.info("=" * 60)
        logger.info(f"Name: {catalog.metadata.name}")
        logger.info(f"Version: {catalog.version}")
        logger.info(f"Schema version: {catalog.schema_version}")
        logger.info(f"Description: {catalog.metadata.description}")
        logger.info(f"Author: {catalog.metadata.author}")
        logger.info(f"Error definitions: {len(catalog.errors)}")
        logger.info("=" * 60)

        # Show error IDs
        if catalog.errors:
            logger.info("\nError definitions:")
            for error_id, error_def in catalog.errors.items():
                pattern_type = error_def.pattern.type
                file_count = len(error_def.files)
                next_count = len(error_def.next_errors)

                railway_info = ""
                if next_count > 0:
                    railway_info = f" -> {next_count} next"

                logger.info(f"  - {error_id}: {pattern_type} pattern, {file_count} files{railway_info}")

        # Check for railway chains
        has_railway = any(len(e.next_errors) > 0 for e in catalog.errors.values())
        if has_railway:
            logger.info("\nRailway pattern detected:")
            for error_id, error_def in catalog.errors.items():
                if error_def.next_errors:
                    for next_error in error_def.next_errors:
                        next_id = next_error.error_id if hasattr(next_error, "error_id") else next_error["error_id"]
                        when_type = next_error.when.type if hasattr(next_error.when, "type") else next_error["when"]["type"]
                        logger.info(f"  {error_id} --[{when_type}]--> {next_id}")

        logger.success("\nCatalog is valid and ready to use!")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)
