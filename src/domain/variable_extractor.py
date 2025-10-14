"""Variable extraction from local files.

Supports multiple extraction methods:
- regex: Extract using regular expression
- line: Extract specific line number
- json_path: Extract from JSON using JSONPath
- yaml_path: Extract from YAML using dot notation
"""

import json
import re
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from src.domain.models import VariableExtractor


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
    file_path = Path(extractor.path).expanduser()

    if not file_path.exists():
        if extractor.default is not None:
            logger.warning(f"File not found: {file_path}, using default: {extractor.default}")
            return extractor.default
        raise FileNotFoundError(f"Variable extraction failed: {file_path} not found")

    try:
        if extractor.method == "regex":
            return _extract_with_regex(file_path, extractor)
        elif extractor.method == "line":
            return _extract_line(file_path, extractor)
        elif extractor.method == "json_path":
            return _extract_json_path(file_path, extractor)
        elif extractor.method == "yaml_path":
            return _extract_yaml_path(file_path, extractor)
        else:
            raise ValueError(f"Unsupported extraction method: {extractor.method}")
    except Exception as e:
        if extractor.default is not None:
            logger.warning(f"Variable extraction failed: {e}, using default: {extractor.default}")
            return extractor.default
        raise ValueError(f"Variable extraction failed: {e}") from e


def _extract_with_regex(file_path: Path, extractor: VariableExtractor) -> str:
    """Extract value using regular expression."""
    content = file_path.read_text()
    pattern = re.compile(extractor.pattern)
    match = pattern.search(content)

    if not match:
        raise ValueError(f"Pattern '{extractor.pattern}' not found in {file_path}")

    # Try to get named group 'value', otherwise use first group or entire match
    if "value" in match.groupdict():
        value = match.group("value")
    elif match.groups():
        value = match.group(1)
    else:
        value = match.group(0)

    return value.strip() if extractor.strip else value


def _extract_line(file_path: Path, extractor: VariableExtractor) -> str:
    """Extract specific line from file."""
    lines = file_path.read_text().splitlines()
    line_num = extractor.line_number

    if line_num < 1 or line_num > len(lines):
        raise ValueError(f"Line number {line_num} out of range (file has {len(lines)} lines)")

    value = lines[line_num - 1]  # Convert to 0-indexed
    return value.strip() if extractor.strip else value


def _extract_json_path(file_path: Path, extractor: VariableExtractor) -> str:
    """Extract value from JSON file using JSONPath."""
    try:
        import jsonpath_ng.ext as jp
    except ImportError:
        raise ImportError("jsonpath-ng package required for json_path extraction. Install with: pip install jsonpath-ng")

    data = json.loads(file_path.read_text())
    jsonpath_expr = jp.parse(extractor.pattern)
    matches = jsonpath_expr.find(data)

    if not matches:
        raise ValueError(f"JSONPath '{extractor.pattern}' found no matches in {file_path}")

    value = str(matches[0].value)
    return value.strip() if extractor.strip else value


def _extract_yaml_path(file_path: Path, extractor: VariableExtractor) -> str:
    """Extract value from YAML file using dot notation path."""
    data = yaml.safe_load(file_path.read_text())

    # Navigate through nested dict using dot notation
    keys = extractor.pattern.split(".")
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            raise ValueError(f"YAML path '{extractor.pattern}' not found in {file_path} (failed at key '{key}')")

    value = str(current)
    return value.strip() if extractor.strip else value


def extract_catalog_variables(extractors: dict[str, VariableExtractor]) -> dict[str, str]:
    """Extract all variables defined in catalog metadata.

    Args:
        extractors: Dictionary of variable name -> extractor config

    Returns:
        Dictionary of variable name -> extracted value

    Raises:
        ValueError: If any required extraction fails
    """
    variables = {}

    for var_name, extractor in extractors.items():
        try:
            value = extract_variable(extractor)
            variables[var_name] = value
            logger.debug(f"Extracted variable '{var_name}': {value}")
        except Exception as e:
            logger.error(f"Failed to extract variable '{var_name}': {e}")
            raise

    return variables
