"""URI parsing and validation utilities.

Provides centralized URI detection and normalization.
"""


def is_fsspec_uri(path: str) -> bool:
    """Check if a path is an fsspec URI (has a protocol).

    Args:
        path: Path or URI string

    Returns:
        True if path contains an fsspec protocol, False otherwise

    Examples:
        >>> is_fsspec_uri("ssh://host/path")
        True
        >>> is_fsspec_uri("s3://bucket/key")
        True
        >>> is_fsspec_uri("/local/path")
        False
        >>> is_fsspec_uri("file:///local/path")
        False
    """
    return "://" in path and not path.startswith("file://")


def normalize_uri_for_fsspec(uri: str) -> str:
    """Convert rsync-style URIs to fsspec format.

    Users prefer rsync-style notation (ssh://host:/path), but fsspec
    expects standard URIs (ssh://host/path). This function converts
    between the two formats.

    Converts:
        ssh://lumi:/path/to/file -> ssh://lumi/path/to/file
        sftp://host:/path -> sftp://host/path
        ssh://user@host:/path -> ssh://user@host/path

    Args:
        uri: URI in rsync-style or fsspec format

    Returns:
        URI in fsspec format

    Examples:
        >>> normalize_uri_for_fsspec("ssh://lumi:/home/test.txt")
        'ssh://lumi/home/test.txt'
        >>> normalize_uri_for_fsspec("ssh://lumi/home/test.txt")
        'ssh://lumi/home/test.txt'
        >>> normalize_uri_for_fsspec("/local/path")
        '/local/path'
    """
    # Check if it's an SSH/SFTP URI with colon notation
    if "://" in uri:
        scheme, rest = uri.split("://", 1)
        if scheme in ("ssh", "sftp"):
            # Check if there's a colon after the hostname
            # Format: ssh://hostname:/path or ssh://user@hostname:/path
            if ":/" in rest:
                # Remove the colon: hostname:/path -> hostname/path
                rest = rest.replace(":/", "/", 1)
                return f"{scheme}://{rest}"

    return uri
