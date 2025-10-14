"""Variable extraction from files and environment.

Source types:
- file: Extract from local or remote files
- env: Extract from environment variables

File extraction methods:
- regex: Extract using regular expression
- line: Extract specific line number
- json_path: Extract from JSON using JSONPath
- yaml_path: Extract from YAML using dot notation

Supports any fsspec-compatible URI for file sources:
- Local files: /path/to/file or ~/path/to/file
- S3: s3://bucket/path/to/file
- GitHub: github://org:repo@ref/path/to/file
- SSH: ssh://user@host/path/to/file
- SFTP: sftp://user@host/path/to/file
- HTTP/HTTPS: https://example.com/path/to/file
"""

import json
import os
import re
from pathlib import Path
from typing import Any

import fsspec
import yaml
from loguru import logger

from src.domain.models import VariableExtractor


def _is_fsspec_uri(path: str) -> bool:
    """Check if a path is an fsspec URI (has a protocol).

    Args:
        path: Path or URI string

    Returns:
        True if path contains an fsspec protocol, False otherwise
    """
    return "://" in path and not path.startswith("file://")


def _read_file_content(path: str) -> str:
    """Read file content from local path or fsspec URI.

    Args:
        path: Local path or fsspec URI

    Returns:
        File content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If file cannot be read
    """
    if _is_fsspec_uri(path):
        # Use fsspec to read remote files
        try:
            with fsspec.open(path, "r") as f:
                return f.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found at URI: {path}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to read file from {path}: {e}") from e
    else:
        # Use local file path with expanduser support
        file_path = Path(path).expanduser()
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_text()


def extract_variable(extractor: VariableExtractor) -> str:
    """Extract a variable value using the configured extractor.

    Args:
        extractor: Variable extractor configuration

    Returns:
        Extracted value as string, or default value if extraction fails

    Raises:
        FileNotFoundError: If source file doesn't exist
        ValueError: If extraction fails and no default is provided
    """
    try:
        # Handle environment variable extraction
        if extractor.source == "env":
            return _extract_from_env(extractor)

        # Handle file extraction (local or remote)
        content = _read_file_content(extractor.path)

        # Apply extraction method
        if extractor.method == "regex":
            return _extract_with_regex(content, extractor)
        elif extractor.method == "line":
            return _extract_line(content, extractor)
        elif extractor.method == "json_path":
            return _extract_json_path(content, extractor)
        elif extractor.method == "yaml_path":
            return _extract_yaml_path(content, extractor)
        else:
            raise ValueError(f"Unsupported extraction method: {extractor.method}")

    except Exception as e:
        if extractor.default is not None:
            source_desc = f"environment variable '{extractor.pattern}'" if extractor.source == "env" else f"file {extractor.path}"
            logger.warning(f"Variable extraction failed from {source_desc}: {e}, using default: {extractor.default}")
            return extractor.default
        raise ValueError(f"Variable extraction failed: {e}") from e


def _extract_from_env(extractor: VariableExtractor) -> str:
    """Extract value from environment variable.

    Args:
        extractor: Variable extractor configuration with pattern as env var name

    Returns:
        Environment variable value

    Raises:
        ValueError: If environment variable is not set
    """
    env_var_name = extractor.pattern
    value = os.environ.get(env_var_name)

    if value is None:
        raise ValueError(f"Environment variable '{env_var_name}' is not set")

    return value.strip() if extractor.strip else value


def _extract_with_regex(content: str, extractor: VariableExtractor) -> str:
    """Extract value using regular expression."""
    pattern = re.compile(extractor.pattern)
    match = pattern.search(content)

    if not match:
        raise ValueError(f"Pattern '{extractor.pattern}' not found in content")

    # Try to get named group 'value', otherwise use first group or entire match
    if "value" in match.groupdict():
        value = match.group("value")
    elif match.groups():
        value = match.group(1)
    else:
        value = match.group(0)

    return value.strip() if extractor.strip else value


def _extract_line(content: str, extractor: VariableExtractor) -> str:
    """Extract specific line from file content."""
    lines = content.splitlines()
    line_num = extractor.line_number

    if line_num < 1 or line_num > len(lines):
        raise ValueError(f"Line number {line_num} out of range (file has {len(lines)} lines)")

    value = lines[line_num - 1]  # Convert to 0-indexed
    return value.strip() if extractor.strip else value


def _extract_json_path(content: str, extractor: VariableExtractor) -> str:
    """Extract value from JSON content using JSONPath."""
    try:
        import jsonpath_ng.ext as jp
    except ImportError:
        raise ImportError("jsonpath-ng package required for json_path extraction. Install with: pip install jsonpath-ng")

    data = json.loads(content)
    jsonpath_expr = jp.parse(extractor.pattern)
    matches = jsonpath_expr.find(data)

    if not matches:
        raise ValueError(f"JSONPath '{extractor.pattern}' found no matches")

    value = str(matches[0].value)
    return value.strip() if extractor.strip else value


def _extract_yaml_path(content: str, extractor: VariableExtractor) -> str:
    """Extract value from YAML content using dot notation path."""
    data = yaml.safe_load(content)

    # Navigate through nested dict using dot notation
    keys = extractor.pattern.split(".")
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            raise ValueError(f"YAML path '{extractor.pattern}' not found (failed at key '{key}')")

    value = str(current)
    return value.strip() if extractor.strip else value


def extract_catalog_variables(extractors: dict[str, VariableExtractor]) -> dict[str, str]:
    """Extract all variables defined in catalog metadata.

    Variables are extracted in order, and later variables can reference earlier ones
    using Jinja2 template syntax in their paths (e.g., {{ expid }}).

    Args:
        extractors: Dictionary of variable name -> extractor config

    Returns:
        Dictionary of variable name -> extracted value

    Raises:
        ValueError: If any required extraction fails
    """
    from jinja2 import Template

    variables = {}

    for var_name, extractor in extractors.items():
        try:
            # Render templates in extractor path using previously extracted variables
            if extractor.source == "file" and extractor.path:
                try:
                    template = Template(extractor.path)
                    rendered_path = template.render(**variables)
                    if rendered_path != extractor.path:
                        logger.debug(f"Rendered path template for '{var_name}': {extractor.path} -> {rendered_path}")
                        # Create a new extractor with rendered path
                        extractor = VariableExtractor(
                            source=extractor.source,
                            path=rendered_path,
                            method=extractor.method,
                            pattern=extractor.pattern,
                            line_number=extractor.line_number,
                            default=extractor.default,
                            strip=extractor.strip,
                        )
                except Exception as e:
                    logger.warning(f"Failed to render path template for '{var_name}': {e}, using original path")

            value = extract_variable(extractor)
            variables[var_name] = value

            # Log extraction with appropriate source description
            if extractor.source == "env":
                logger.debug(f"Extracted variable '{var_name}' from environment variable '{extractor.pattern}': {value}")
            else:
                logger.debug(f"Extracted variable '{var_name}' from {extractor.path}: {value}")

        except Exception as e:
            logger.error(f"Failed to extract variable '{var_name}': {e}")
            raise

    return variables
