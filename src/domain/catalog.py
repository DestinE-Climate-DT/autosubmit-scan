"""Catalog I/O operations.

This module provides functions for:
- Loading catalogs from YAML files or fsspec URIs
- Saving catalogs to YAML files
- Converting catalogs to JSON-LD format
- Converting JSON-LD to catalogs
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import fsspec
import yaml

from src.domain.models import ErrorCatalog


def is_fsspec_uri(path: str) -> bool:
    """Check if a path is an fsspec URI (has a protocol).

    Args:
        path: Path or URI string

    Returns:
        True if path contains an fsspec protocol, False otherwise
    """
    # fsspec URIs have the format: protocol://path
    # Local files can be absolute (/path) or relative (path)
    return "://" in path and not path.startswith("file://")


def load_catalog(path: str) -> ErrorCatalog:
    """Load error catalog from YAML file or fsspec URI.

    Supports any fsspec-compatible URI including:
    - Local files: /path/to/catalog.yaml
    - GitHub: github://org:repo@ref/path/to/catalog.yaml
    - SSH: ssh://host/path/to/catalog.yaml
    - S3: s3://bucket/path/to/catalog.yaml
    - HTTP: https://example.com/catalog.yaml

    Args:
        path: Path to YAML file or fsspec URI

    Returns:
        ErrorCatalog instance

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
        pydantic.ValidationError: If catalog structure is invalid
    """
    if is_fsspec_uri(path):
        # Use fsspec to open remote URIs
        try:
            with fsspec.open(path, "r") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Catalog not found at URI: {path}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to load catalog from {path}: {e}") from e
    else:
        # Use local file path
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"Catalog file not found: {path}")

        with open(file_path) as f:
            data = yaml.safe_load(f)

    # Convert datetime strings to datetime objects
    if "metadata" in data:
        if "created" in data["metadata"]:
            if isinstance(data["metadata"]["created"], str):
                data["metadata"]["created"] = datetime.fromisoformat(data["metadata"]["created"])
        if "updated" in data["metadata"]:
            if isinstance(data["metadata"]["updated"], str):
                data["metadata"]["updated"] = datetime.fromisoformat(data["metadata"]["updated"])

    return ErrorCatalog(**data)


def save_catalog(catalog: ErrorCatalog, path: str) -> None:
    """Save error catalog to YAML file.

    Args:
        catalog: ErrorCatalog to save
        path: Path to save YAML file

    Raises:
        OSError: If file cannot be written
    """
    file_path = Path(path)

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict with proper serialization
    data = catalog.model_dump(mode="python")

    # Convert datetime objects to ISO format strings
    if "metadata" in data:
        if isinstance(data["metadata"]["created"], datetime):
            data["metadata"]["created"] = data["metadata"]["created"].isoformat()
        if isinstance(data["metadata"]["updated"], datetime):
            data["metadata"]["updated"] = data["metadata"]["updated"].isoformat()

    # Convert enums to strings
    def convert_enums(obj):
        """Recursively convert enum values to strings."""
        if isinstance(obj, dict):
            return {k: convert_enums(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_enums(item) for item in obj]
        elif hasattr(obj, "value"):  # Enum
            return obj.value
        else:
            return obj

    data = convert_enums(data)

    with open(file_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def catalog_to_jsonld(catalog: ErrorCatalog) -> dict[str, Any]:
    """Convert error catalog to JSON-LD format.

    Uses Schema.org vocabulary with custom extensions.

    Args:
        catalog: ErrorCatalog to convert

    Returns:
        JSON-LD representation as dictionary
    """
    # Generate a unique ID for this catalog instance
    catalog_id = f"urn:uuid:{uuid.uuid4()}"

    # Convert catalog to dict
    data = catalog.model_dump(mode="python")

    # Convert datetime objects to ISO format strings
    if "metadata" in data:
        if isinstance(data["metadata"]["created"], datetime):
            data["metadata"]["created"] = data["metadata"]["created"].isoformat()
        if isinstance(data["metadata"]["updated"], datetime):
            data["metadata"]["updated"] = data["metadata"]["updated"].isoformat()

    # Convert enums to strings
    def convert_enums(obj):
        """Recursively convert enum values to strings."""
        if isinstance(obj, dict):
            return {k: convert_enums(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_enums(item) for item in obj]
        elif hasattr(obj, "value"):  # Enum
            return obj.value
        else:
            return obj

    data = convert_enums(data)

    # Build JSON-LD structure
    jsonld = {
        "@context": {
            "@vocab": "https://schema.org/",
            "error_scan": "https://destine.example/error-scan/schema#",
        },
        "@type": "ErrorCatalog",
        "@id": catalog_id,
        **data,
    }

    return jsonld


def jsonld_to_catalog(data: dict[str, Any]) -> ErrorCatalog:
    """Convert JSON-LD to error catalog.

    Args:
        data: JSON-LD dictionary

    Returns:
        ErrorCatalog instance

    Raises:
        pydantic.ValidationError: If structure is invalid
    """
    # Remove JSON-LD specific fields
    catalog_data = {k: v for k, v in data.items() if not k.startswith("@")}

    # Convert datetime strings to datetime objects
    if "metadata" in catalog_data:
        if "created" in catalog_data["metadata"]:
            if isinstance(catalog_data["metadata"]["created"], str):
                catalog_data["metadata"]["created"] = datetime.fromisoformat(catalog_data["metadata"]["created"])
        if "updated" in catalog_data["metadata"]:
            if isinstance(catalog_data["metadata"]["updated"], str):
                catalog_data["metadata"]["updated"] = datetime.fromisoformat(catalog_data["metadata"]["updated"])

    return ErrorCatalog(**catalog_data)
