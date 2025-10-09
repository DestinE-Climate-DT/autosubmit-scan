"""Streaming file reader with fsspec support.

Provides memory-efficient line-by-line reading for files accessed via:
- Local filesystem
- S3 (s3://)
- SSH (ssh://) with rsync-style notation (ssh://host:/path)
- SFTP (sftp://) with rsync-style notation (sftp://host:/path)
- FTP (ftp://)
"""

import fsspec
from typing import Iterator, Tuple, List, Optional
from urllib.parse import urlparse

from src.cli.completion import normalize_uri_for_fsspec, get_fsspec_filesystem


class FileStream:
    """Memory-efficient file streaming with line-based access.

    Supports all fsspec protocols and provides:
    - Line-by-line iteration with line numbers
    - Reading specific line ranges
    - Context manager support
    """

    def __init__(self, file_handle, uri: str, strip_newlines: bool = False):
        """Initialize FileStream.

        Args:
            file_handle: Open fsspec file handle
            uri: Original file URI
            strip_newlines: If True, strip newline characters from lines
        """
        self.file_handle = file_handle
        self.uri = uri
        self.strip_newlines = strip_newlines

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and close file handle."""
        self.close()
        return False

    def close(self):
        """Close the file handle."""
        if self.file_handle:
            try:
                self.file_handle.close()
            except Exception:
                pass  # Ignore errors on close

    @classmethod
    def open_file(cls, uri: str, strip_newlines: bool = False) -> "FileStream":
        """Open a file for streaming.

        Args:
            uri: File URI (supports s3://, ssh://, sftp://, ftp://, file://, or local path)
            strip_newlines: If True, strip newline characters from lines

        Returns:
            FileStream instance

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file cannot be accessed

        Examples:
            >>> stream = FileStream.open_file("/var/log/app.log")
            >>> stream = FileStream.open_file("s3://bucket/data/log.txt")
            >>> stream = FileStream.open_file("sftp://user@host/path/file.log")
        """
        try:
            # Normalize rsync-style URIs to fsspec format
            normalized_uri = normalize_uri_for_fsspec(uri)

            # Get filesystem with SSH config support
            fs = get_fsspec_filesystem(uri)

            # Parse URI to extract path
            parsed = urlparse(normalized_uri)
            protocol_part = parsed.scheme or 'file'

            # Extract the path component
            if protocol_part in ('ssh', 'sftp', 's3'):
                file_path = parsed.path
            elif protocol_part == 'file':
                file_path = parsed.path
            else:
                # Local path without protocol
                file_path = normalized_uri

            # Open file with filesystem
            opened_file = fs.open(file_path, mode='r', encoding='utf-8')

            return cls(opened_file, uri, strip_newlines)

        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {uri}") from e
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {uri}") from e

    def read_lines(self) -> Iterator[Tuple[int, str]]:
        """Read file line by line.

        Yields:
            Tuple of (line_number, line_text)
            Line numbers are 1-indexed

        Examples:
            >>> stream = FileStream.open_file("data.log")
            >>> for line_num, line_text in stream.read_lines():
            ...     print(f"{line_num}: {line_text}")
        """
        # Seek to beginning in case we're re-reading
        try:
            self.file_handle.seek(0)
        except (OSError, AttributeError):
            # Some protocols don't support seeking
            # Close and reopen the file
            self.close()
            normalized_uri = normalize_uri_for_fsspec(self.uri)
            self.file_handle = fsspec.open(normalized_uri, mode='r', encoding='utf-8').open()

        line_number = 1
        for line in self.file_handle:
            if self.strip_newlines:
                line = line.rstrip('\n\r')
            yield (line_number, line)
            line_number += 1

    def read_lines_range(self, start: int, end: int) -> List[str]:
        """Read a specific range of lines.

        Args:
            start: Starting line number (1-indexed, inclusive)
            end: Ending line number (1-indexed, inclusive)

        Returns:
            List of lines in the range

        Raises:
            ValueError: If start > end or start < 1

        Examples:
            >>> stream = FileStream.open_file("data.log")
            >>> lines = stream.read_lines_range(10, 15)  # Read lines 10-15
        """
        if start < 1:
            raise ValueError(f"Start line must be >= 1, got {start}")

        if start > end:
            raise ValueError(
                f"Start line ({start}) cannot be greater than end line ({end})"
            )

        result = []

        for line_num, line_text in self.read_lines():
            if line_num < start:
                continue
            if line_num > end:
                break
            result.append(line_text)

        return result

    def close(self):
        """Close the file handle."""
        if self.file_handle:
            try:
                self.file_handle.close()
            except Exception:
                # Ignore errors on close
                pass

    def __enter__(self) -> "FileStream":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close file."""
        self.close()
        return False
