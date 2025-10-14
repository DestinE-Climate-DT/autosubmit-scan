"""Custom Click parameter types for CLI."""

from pathlib import Path

import click
import fsspec


class FsspecPath(click.ParamType):
    """Click parameter type for local paths or fsspec URIs.

    Supports:
    - Local filesystem paths: /path/to/file or ~/path/to/file
    - GitHub: github://org:repo@ref/path/to/file
    - SSH: ssh://user@host/path/to/file
    - SFTP: sftp://user@host/path/to/file
    - S3: s3://bucket/path/to/file
    - HTTP/HTTPS: https://example.com/path/to/file
    - FTP: ftp://user:pass@host/path/to/file

    Args:
        exists: If True, validate that the path/URI is accessible
        dir_okay: If False, reject directories (only for local paths)
        file_okay: If False, reject files
    """

    name = "fsspec_path"

    def __init__(self, exists: bool = False, dir_okay: bool = True, file_okay: bool = True):
        self.exists = exists
        self.dir_okay = dir_okay
        self.file_okay = file_okay

    def convert(self, value, param, ctx):
        """Convert and validate the path/URI."""
        if value is None:
            return None

        # Check if it's an fsspec URI (has protocol)
        if "://" in value and not value.startswith("file://"):
            # It's an fsspec URI
            if self.exists:
                # Try to validate URI is accessible
                try:
                    # Skip validation for GitHub URIs as fsspec's GitHub URI parsing
                    # has issues with refs containing slashes (e.g., test/dynamic-variables)
                    # The actual file access will validate during catalog loading
                    if value.startswith("github://"):
                        # Basic format validation only
                        if "@" not in value or ":" not in value:
                            self.fail(f"Invalid GitHub URI format (expected github://org:repo@ref/path): {value}", param, ctx)
                    else:
                        # Use standard url_to_fs for other protocols
                        fs = fsspec.core.url_to_fs(value)[0]
                        # For URIs, we can't easily distinguish file vs directory
                        # so we just check if the path exists
                        path_part = value.split("://", 1)[1]
                        if not fs.exists(path_part):
                            self.fail(f"URI does not exist: {value}", param, ctx)
                except Exception as e:
                    self.fail(f"Cannot access URI '{value}': {e}", param, ctx)

            return value

        else:
            # It's a local path
            path = Path(value).expanduser()

            if self.exists:
                if not path.exists():
                    self.fail(f"Path does not exist: {value}", param, ctx)

                if not self.file_okay and path.is_file():
                    self.fail(f"Path is a file (expected directory): {value}", param, ctx)

                if not self.dir_okay and path.is_dir():
                    self.fail(f"Path is a directory (expected file): {value}", param, ctx)

            return str(path.resolve())

    def __repr__(self):
        """Return string representation showing configuration."""
        parts = []
        if self.exists:
            parts.append("exists=True")
        if not self.file_okay:
            parts.append("file_okay=False")
        if not self.dir_okay:
            parts.append("dir_okay=False")

        if not parts:
            return self.__class__.__name__
        return f"{self.__class__.__name__}({', '.join(parts)})"
