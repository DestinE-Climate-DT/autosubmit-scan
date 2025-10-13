"""Helper functions for Snakemake workflow orchestration.

Provides utilities for:
- File hashing (cache keys)
- Glob pattern expansion (file discovery)
- File fingerprinting (metadata extraction)
- Manifest reading/writing
- Error definition lookup
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.cli.completion import get_fsspec_filesystem, normalize_uri_for_fsspec
from src.domain.models import ErrorCatalog, ErrorDefinition


def get_file_hash(uri: str) -> str:
    """Generate a SHA256 hash of a file URI for use as cache key.

    Args:
        uri: File URI to hash

    Returns:
        SHA256 hex digest (64 characters)

    Examples:
        >>> get_file_hash("s3://bucket/path/file.log")
        'a1b2c3d4...'
    """
    return hashlib.sha256(uri.encode("utf-8")).hexdigest()


def expand_fsspec_patterns(patterns: list[str]) -> list[str]:
    """Expand glob patterns to list of matching file URIs.

    Supports all fsspec protocols:
    - Local paths: /var/log/*.log
    - File protocol: file:///var/log/*.log
    - S3: s3://bucket/**/*.log
    - SSH: ssh://user@host/path/*.log
    - SFTP: sftp://user@host/path/*.log
    - FTP: ftp://user:pass@host/path/*.log

    Args:
        patterns: List of glob patterns (fsspec compatible)

    Returns:
        List of matched file URIs (deduplicated and sorted)

    Examples:
        >>> expand_fsspec_patterns(["/var/log/*.log"])
        ['/var/log/app.log', '/var/log/system.log']

        >>> expand_fsspec_patterns(["s3://bucket/logs/**/*.log"])
        ['s3://bucket/logs/2024/01/app.log', ...]
    """
    all_files = []

    for pattern in patterns:
        try:
            # Get the filesystem with SSH config support
            fs = get_fsspec_filesystem(pattern)

            # Normalize the pattern for fsspec
            normalized_pattern = normalize_uri_for_fsspec(pattern)

            # Parse the normalized URI to extract path and protocol
            parsed = urlparse(normalized_pattern)
            protocol_part = parsed.scheme or "file"

            # Extract the path component for globbing
            if protocol_part in ("ssh", "sftp", "s3"):
                # For remote filesystems, use the path component
                glob_path = parsed.path
            elif protocol_part == "file":
                # For file:// URIs, use the path
                glob_path = parsed.path
            else:
                # For local paths without protocol
                glob_path = normalized_pattern

            # Expand the glob pattern directly on the filesystem
            matched_files = fs.glob(glob_path)

            # Convert to full URIs
            for matched_file in matched_files:
                # Build full URI based on pattern format
                if pattern.startswith("file://"):
                    # Normalize file:// URIs - ensure absolute path
                    if not matched_file.startswith("/"):
                        matched_file = "/" + matched_file
                    full_uri = f"file://{matched_file}"
                elif protocol_part in ("s3", "ssh", "sftp", "ftp"):
                    # Remote protocols - rebuild URI with hostname
                    # matched_file is just the path, so we need to add back the netloc
                    if parsed.netloc:
                        # For SSH/SFTP, use rsync-style format (with colon before path)
                        # This is required by our Pydantic validation
                        if protocol_part in ("ssh", "sftp"):
                            # Rsync-style: ssh://host:/path
                            full_uri = f"{protocol_part}://{parsed.netloc}:/{matched_file.lstrip('/')}"
                        else:
                            # Other protocols use standard format
                            full_uri = f"{protocol_part}://{parsed.netloc}/{matched_file.lstrip('/')}"
                    else:
                        full_uri = f"{protocol_part}://{matched_file}"
                else:
                    # Local path without protocol - keep as-is
                    full_uri = matched_file

                all_files.append(full_uri)

        except (FileNotFoundError, OSError, IndexError, ValueError):
            # Pattern matched no files or path doesn't exist
            # This is not necessarily an error - glob patterns can match nothing
            continue

    # Deduplicate and sort
    return sorted(set(all_files))


def get_fingerprint(uri: str) -> dict[str, Any]:
    """Get file metadata fingerprint for caching and change detection.

    Fingerprint includes:
    - uri: Original file URI
    - size: File size in bytes
    - mtime: Last modification time (ISO format)
    - checksum: File checksum (MD5 for local files, protocol-dependent for remote)
    - fingerprinted_at: When fingerprint was created

    Args:
        uri: File URI (supports all fsspec protocols)

    Returns:
        Dictionary with fingerprint data

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file cannot be accessed

    Examples:
        >>> fp = get_fingerprint("/var/log/app.log")
        >>> fp['size']
        1048576
        >>> fp['checksum']
        'md5:a1b2c3d4...'
    """
    try:
        # Normalize rsync-style URIs to fsspec format
        normalized_uri = normalize_uri_for_fsspec(uri)

        # Get filesystem with SSH config support
        fs = get_fsspec_filesystem(uri)

        # Parse URI to extract path
        parsed = urlparse(normalized_uri)
        protocol_part = parsed.scheme or "file"

        # Extract the path component
        if protocol_part in ("ssh", "sftp", "s3"):
            file_path = parsed.path
        elif protocol_part == "file":
            file_path = parsed.path
        else:
            # Local path without protocol
            file_path = normalized_uri

        # Get file info
        file_info = fs.info(file_path)

        # Extract metadata
        size = file_info.get("size", 0)

        # Get modification time
        mtime = file_info.get("mtime")
        if mtime is not None:
            # Convert to ISO format
            if isinstance(mtime, (int, float)):
                mtime_dt = datetime.fromtimestamp(mtime)
            elif isinstance(mtime, datetime):
                mtime_dt = mtime
            else:
                mtime_dt = datetime.now()
            mtime_str = mtime_dt.isoformat() + "Z"
        else:
            mtime_str = datetime.now().isoformat() + "Z"

        # Compute checksum for local files
        checksum = None
        try:
            # Determine if this is a local file
            is_local = False
            if hasattr(fs, "protocol"):
                protocol = fs.protocol
                if isinstance(protocol, list):
                    protocol = protocol[0]
                # Check for local file protocols
                if protocol in ("file", "local", "abstract"):
                    is_local = True
            # Also check if URI doesn't have a protocol (local path)
            if "://" not in uri or uri.startswith("file://"):
                is_local = True

            if is_local:
                # For local files, compute MD5 checksum
                import hashlib

                md5_hash = hashlib.md5()

                with fs.open(paths[0], "rb") as f:
                    # Read in chunks to handle large files
                    for chunk in iter(lambda: f.read(8192), b""):
                        md5_hash.update(chunk)

                checksum = f"md5:{md5_hash.hexdigest()}"

            # For S3, use ETag if available
            elif hasattr(fs, "protocol") and "s3" in str(fs.protocol):
                etag = file_info.get("ETag", "").strip('"')
                if etag:
                    checksum = f"etag:{etag}"

        except Exception:
            # If checksum fails, continue without it
            pass

        # Build fingerprint
        fingerprint = {
            "uri": uri,
            "size": size,
            "mtime": mtime_str,
            "fingerprinted_at": datetime.now().isoformat() + "Z",
        }

        if checksum:
            fingerprint["checksum"] = checksum

        return fingerprint

    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {uri}") from e
    except PermissionError as e:
        raise PermissionError(f"Permission denied: {uri}") from e


def read_manifest(manifest_path: str) -> list[str]:
    """Read a manifest file containing list of file URIs.

    Manifest format:
    - One URI per line
    - Lines starting with # are comments (skipped)
    - Empty lines are skipped
    - Whitespace is trimmed

    Args:
        manifest_path: Path to manifest file

    Returns:
        List of file URIs

    Examples:
        >>> uris = read_manifest("manifests/slurm_oom_files.txt")
        >>> uris
        ['s3://bucket/logs/job1.log', 's3://bucket/logs/job2.log']
    """
    uris = []

    with open(manifest_path, encoding="utf-8") as f:
        for line in f:
            # Strip whitespace
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            uris.append(line)

    return uris


def write_manifest(manifest_path: str, uris: list[str]) -> None:
    """Write a manifest file containing list of file URIs.

    Args:
        manifest_path: Path to manifest file
        uris: List of file URIs to write

    Examples:
        >>> write_manifest("manifests/files.txt", ["s3://bucket/file1.log", "s3://bucket/file2.log"])
    """
    # Ensure parent directory exists
    Path(manifest_path).parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "w", encoding="utf-8") as f:
        for uri in uris:
            f.write(f"{uri}\n")


def get_error_definition(catalog: ErrorCatalog, error_id: str) -> ErrorDefinition:
    """Get an error definition from a catalog by ID.

    Args:
        catalog: ErrorCatalog instance
        error_id: Error ID to look up

    Returns:
        ErrorDefinition instance

    Raises:
        KeyError: If error ID doesn't exist in catalog

    Examples:
        >>> catalog = load_catalog("catalog.yaml")
        >>> error_def = get_error_definition(catalog, "slurm_oom")
        >>> error_def.meaning
        'Job was killed due to out-of-memory condition'
    """
    if error_id not in catalog.errors:
        raise KeyError(f"Error ID '{error_id}' not found in catalog. " f"Available errors: {list(catalog.errors.keys())}")

    return catalog.errors[error_id]
