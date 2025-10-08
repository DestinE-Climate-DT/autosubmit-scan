"""Catalog I/O operations.

This module provides functions for:
- Loading catalogs from YAML files
- Saving catalogs to YAML files
- Converting catalogs to JSON-LD format
- Converting JSON-LD to catalogs
"""

import yaml
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import uuid

from src.domain.models import ErrorCatalog


def load_catalog(path: str) -> ErrorCatalog:
    """Load error catalog from YAML file.

    Args:
        path: Path to YAML file

    Returns:
        ErrorCatalog instance

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
        pydantic.ValidationError: If catalog structure is invalid
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Catalog file not found: {path}")

    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    # Convert datetime strings to datetime objects
    if "metadata" in data:
        if "created" in data["metadata"]:
            if isinstance(data["metadata"]["created"], str):
                data["metadata"]["created"] = datetime.fromisoformat(
                    data["metadata"]["created"]
                )
        if "updated" in data["metadata"]:
            if isinstance(data["metadata"]["updated"], str):
                data["metadata"]["updated"] = datetime.fromisoformat(
                    data["metadata"]["updated"]
                )

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


def catalog_to_jsonld(catalog: ErrorCatalog) -> Dict[str, Any]:
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


def jsonld_to_catalog(data: Dict[str, Any]) -> ErrorCatalog:
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
                catalog_data["metadata"]["created"] = datetime.fromisoformat(
                    catalog_data["metadata"]["created"]
                )
        if "updated" in catalog_data["metadata"]:
            if isinstance(catalog_data["metadata"]["updated"], str):
                catalog_data["metadata"]["updated"] = datetime.fromisoformat(
                    catalog_data["metadata"]["updated"]
                )

    return ErrorCatalog(**catalog_data)
