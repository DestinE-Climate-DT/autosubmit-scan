"""Validation functions for domain models.

This module provides custom validators for:
- Semver version strings
- fsspec URIs (s3://, ssh://, sftp://, ftp://, file://, local paths)
- Callable strings (module:function format)
"""

import re

import semver


def validate_semver(version: str) -> str:
    """Validate that a string is a valid semantic version.

    Args:
        version: Version string to validate

    Returns:
        The validated version string

    Raises:
        ValueError: If the version is not valid semver
    """
    try:
        # Try new API first (semver 3.x)
        if hasattr(semver, "Version"):
            semver.Version.parse(version)
        else:
            # Fall back to older API (semver 2.x)
            semver.parse(version)
        return version
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid semantic version '{version}': {e}") from e


def validate_uri(uri: str) -> str:
    """Validate that a string is a valid fsspec URI or local path.

    Supports:
    - s3://bucket/path
    - ssh://host:/path (rsync-style, recommended)
    - ssh://user@host:port/path (standard)
    - sftp://host:/path (rsync-style, recommended)
    - sftp://user:pass@host/path (standard)
    - ftp://user:pass@host/path
    - file:///absolute/path
    - /absolute/path

    Allows glob patterns (* and **) in paths.

    Note: Rsync-style SSH/SFTP URIs (with colon before path) automatically
    resolve host aliases and credentials from ~/.ssh/config.

    Args:
        uri: URI string to validate

    Returns:
        The validated URI string

    Raises:
        ValueError: If the URI format is invalid
    """
    # Allow empty string for optional fields
    if not uri:
        return uri

    # S3 URIs: s3://bucket/path
    if uri.startswith("s3://"):
        if len(uri) > 5:  # More than just "s3://"
            return uri
        raise ValueError(f"Invalid S3 URI: {uri}")

    # SSH URIs: ssh://user@host:port/path or ssh://user@host/path
    # Also supports rsync-style: ssh://host:/path (with colon before slash)
    if uri.startswith("ssh://"):
        # Rsync-style: ssh://host:/path or ssh://user@host:/path
        rsync_pattern = r"^ssh://(?:[^@]+@)?[^:/]+:/.+"
        # Standard: ssh://user@host/path or ssh://user@host:port/path
        standard_pattern = r"^ssh://[^@]+@[^:/]+(?::\d+)?/.+"
        if re.match(rsync_pattern, uri) or re.match(standard_pattern, uri):
            return uri
        raise ValueError(f"Invalid SSH URI: {uri}")

    # SFTP URIs: sftp://user:pass@host/path or sftp://user@host/path
    # Also supports rsync-style: sftp://host:/path (with colon before slash)
    if uri.startswith("sftp://"):
        # Rsync-style: sftp://host:/path or sftp://user@host:/path
        rsync_pattern = r"^sftp://(?:[^@]+@)?[^:/]+:/.+"
        # Standard: sftp://user@host/path
        standard_pattern = r"^sftp://[^@]+@[^/]+/.+"
        if re.match(rsync_pattern, uri) or re.match(standard_pattern, uri):
            return uri
        raise ValueError(f"Invalid SFTP URI: {uri}")

    # FTP URIs: ftp://user:pass@host/path or ftp://host/path
    if uri.startswith("ftp://"):
        pattern = r"^ftp://(?:[^@]+@)?[^/]+/.+"
        if re.match(pattern, uri):
            return uri
        raise ValueError(f"Invalid FTP URI: {uri}")

    # File URIs: file:///absolute/path
    if uri.startswith("file://"):
        if uri.startswith("file:///"):
            return uri
        raise ValueError(f"Invalid file URI: {uri} (must start with file:///)")

    # Absolute local paths: /path/to/file
    if uri.startswith("/"):
        return uri

    # If we get here, it's not a recognized format
    raise ValueError(
        f"Invalid URI: {uri}. Must be a valid fsspec URI " "(s3://, ssh://, sftp://, ftp://, file:///) or absolute path (/)."
    )


def validate_callable_string(callable_str: str) -> str:
    """Validate that a string is in module:function format.

    Valid formats:
    - module:function
    - package.module:function
    - package.subpackage.module:function_name

    Args:
        callable_str: Callable string to validate

    Returns:
        The validated callable string

    Raises:
        ValueError: If the format is invalid
    """
    if not callable_str:
        raise ValueError("Callable string cannot be empty")

    if ":" not in callable_str:
        raise ValueError(f"Invalid callable format: {callable_str}. " "Must be in 'module:function' format")

    parts = callable_str.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid callable format: {callable_str}. " "Must contain exactly one ':' separator")

    module_path, function_name = parts

    if not module_path or not function_name:
        raise ValueError(f"Invalid callable format: {callable_str}. " "Both module path and function name must be non-empty")

    # Validate module path (letters, numbers, underscores, dots)
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*$", module_path):
        raise ValueError(f"Invalid module path in callable: {module_path}. " "Must be a valid Python module path")

    # Validate function name (letters, numbers, underscores)
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", function_name):
        raise ValueError(f"Invalid function name in callable: {function_name}. " "Must be a valid Python identifier")

    return callable_str


def validate_positive_int(value: int) -> int:
    """Validate that an integer is positive (>= 1).

    Args:
        value: Integer to validate

    Returns:
        The validated integer

    Raises:
        ValueError: If the value is less than 1
    """
    if value < 1:
        raise ValueError(f"Value must be >= 1, got {value}")
    return value


def validate_non_negative_int(value: int) -> int:
    """Validate that an integer is non-negative (>= 0).

    Args:
        value: Integer to validate

    Returns:
        The validated integer

    Raises:
        ValueError: If the value is negative
    """
    if value < 0:
        raise ValueError(f"Value must be >= 0, got {value}")
    return value
