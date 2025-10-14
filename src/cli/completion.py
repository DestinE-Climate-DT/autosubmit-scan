"""Custom completion for questionary prompts with fsspec support.

This module provides:
- Tab completion for fsspec URIs (SSH, SFTP, S3, local)
- SSH hostname completion from ~/.ssh/config
- Rsync-style URI format (ssh://host:/path) that's user-friendly
- Automatic conversion to fsspec format when needed
"""

import os
from pathlib import Path
from urllib.parse import urlparse

import fsspec
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

__all__ = ["normalize_uri_for_fsspec", "get_fsspec_filesystem", "FsspecPathCompleter", "GlobPatternCompleter"]


# Global cache for filesystem connections to enable connection pooling
_FILESYSTEM_CACHE = {}


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


def _parse_ssh_config_standalone(alias: str) -> dict[str, str]:
    """Parse SSH config to get connection details for an alias.

    Args:
        alias: SSH host alias (e.g., 'mn5', 'lumi')

    Returns:
        Dictionary with 'hostname', 'user', 'port', 'identity_file'
    """
    ssh_config_path = Path.home() / ".ssh" / "config"
    config = {
        "hostname": alias,  # Default to alias if not found
        "user": os.getenv("USER"),
        "port": 22,
        "identity_file": None,
    }

    if not ssh_config_path.exists():
        return config

    try:
        in_target_host = False

        with open(ssh_config_path) as f:
            for line in f:
                line = line.strip()

                # New Host section
                if line.startswith("Host "):
                    host_line = line[5:].strip()
                    # Check if this is our target host
                    hosts_in_line = host_line.split()
                    in_target_host = alias in hosts_in_line
                    continue

                # Parse config options for our target host
                if in_target_host and line:
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        key, value = parts
                        key_lower = key.lower()

                        if key_lower == "hostname":
                            config["hostname"] = value
                        elif key_lower == "user":
                            config["user"] = value
                        elif key_lower == "port":
                            try:
                                config["port"] = int(value)
                            except ValueError:
                                pass
                        elif key_lower == "identityfile":
                            # Expand ~ in identity file path
                            identity_path = os.path.expanduser(value)
                            config["identity_file"] = identity_path

    except Exception:
        pass

    return config


def get_fsspec_filesystem(uri: str):
    """Get fsspec filesystem for a given URI with SSH config support.

    This function handles:
    - Local filesystems
    - S3 filesystems
    - SSH/SFTP filesystems with automatic SSH config parsing
    - Connection pooling to reuse SSH connections

    Args:
        uri: File URI (can be rsync-style for SSH/SFTP)

    Returns:
        fsspec filesystem instance

    Examples:
        >>> fs = get_fsspec_filesystem("ssh://mn5:/path/to/file")
        >>> fs = get_fsspec_filesystem("s3://bucket/path")
        >>> fs = get_fsspec_filesystem("/local/path")
    """
    # Normalize rsync-style URIs
    normalized_uri = normalize_uri_for_fsspec(uri)
    parsed = urlparse(normalized_uri)
    protocol = parsed.scheme or "file"

    # Create cache key and check for cached connection
    if protocol in ("ssh", "sftp"):
        hostname = parsed.hostname or parsed.netloc.rstrip(":/")
        ssh_config = _parse_ssh_config_standalone(hostname)
        cache_key = f"{protocol}://{ssh_config['user']}@{ssh_config['hostname']}:{ssh_config['port']}"

        # Check for cached connection and verify it's still alive
        if cache_key in _FILESYSTEM_CACHE:
            cached_fs = _FILESYSTEM_CACHE[cache_key]
            try:
                # Test connection by trying to list root
                cached_fs.ls("/", detail=False)
                return cached_fs
            except Exception:
                # Connection is dead, remove from cache and create new one
                del _FILESYSTEM_CACHE[cache_key]

    # Create filesystem based on protocol
    if protocol == "s3":
        fs = fsspec.filesystem("s3", anon=False)
    elif protocol in ("ssh", "sftp"):
        # Build fsspec filesystem with proper settings
        fs_kwargs = {
            "host": ssh_config["hostname"],
            "username": parsed.username or ssh_config["user"],
            "port": ssh_config["port"],
        }

        # Note: fsspec's sshfs uses asyncssh which automatically discovers keys from
        # ~/.ssh/ and ssh-agent, so we don't need to explicitly specify key_filename

        fs = fsspec.filesystem(protocol, **fs_kwargs)

        # Cache SSH/SFTP connections for reuse
        _FILESYSTEM_CACHE[cache_key] = fs
    else:
        # Default to local filesystem
        fs = fsspec.filesystem("file")

    return fs


class FsspecPathCompleter(Completer):
    """Path completer that works with fsspec URIs (local, SSH, SFTP, S3, etc.)."""

    class _DummyFS:
        """Dummy filesystem for failed connections."""

        def ls(self, path, detail=False):
            return []

        def isdir(self, path):
            return False

    def __init__(self, only_directories: bool = False, expanduser: bool = True):
        """Initialize completer for fsspec URIs.

        Args:
            only_directories: Only complete directories, not files
            expanduser: Expand ~ to user home directory
        """
        self.only_directories = only_directories
        self.expanduser = expanduser
        self._cache: dict = {}  # Cache for remote filesystem calls
        self._fs_cache: dict = {}  # Cache for filesystem instances
        self._ssh_hosts: list[str] | None = None  # Cached SSH hosts

    def get_completions(self, document: Document, complete_event) -> list[Completion]:
        """Get path completions for the current input."""
        text = document.text_before_cursor

        # Handle empty input - suggest protocols
        if not text:
            return self._suggest_protocols()

        # Parse the URI to determine protocol
        parsed = urlparse(text)

        # Check if we're in path mode or hostname mode for SSH/SFTP
        if parsed.scheme in ("ssh", "sftp"):
            # Check for rsync-style colon (ssh://host:/) or standard slash (ssh://host/)
            rest_of_uri = text.split("://", 1)[1] if "://" in text else ""
            has_path_separator = ":/" in rest_of_uri or (rest_of_uri.count("/") > 0 and "@" not in rest_of_uri.split("/")[-2:][0])

            if has_path_separator:
                # We're in path mode: ssh://mn5:/hom<TAB>
                return self._complete_path(text)
            else:
                # Still typing hostname: ssh://m<TAB> or ssh://user@m<TAB>
                return self._complete_ssh_host(text)
        elif parsed.scheme in ("s3", "file") or (not parsed.scheme and "/" in text):
            # It's a path-like URI - complete paths
            return self._complete_path(text)
        elif "://" not in text and not text.startswith("/"):
            # Still typing the protocol
            return self._suggest_protocols(text)
        else:
            # Unknown or incomplete URI
            return []

    def _suggest_protocols(self, prefix: str = "") -> list[Completion]:
        """Suggest protocol prefixes."""
        # Get first SSH host for better examples
        ssh_hosts = self._get_ssh_hosts()
        example_host = ssh_hosts[0] if ssh_hosts else "host"

        protocols = [
            (f"ssh://{example_host}:/", "SSH protocol (rsync-style)"),
            (f"sftp://{example_host}:/", "SFTP protocol (rsync-style)"),
            ("s3://bucket/", "S3 protocol"),
            ("/", "Local filesystem"),
        ]

        completions = []
        for proto, description in protocols:
            if proto.startswith(prefix):
                completions.append(Completion(text=proto, start_position=-len(prefix), display=f"{proto:<25} {description}"))

        return completions

    def _complete_ssh_host(self, text: str) -> list[Completion]:
        """Complete SSH hostnames from ~/.ssh/config."""
        # Parse what we have so far
        parsed = urlparse(text)

        # Extract the part after :// or after @
        if "@" in text:
            # ssh://user@h<TAB>
            parts = text.split("@")
            prefix_part = "@".join(parts[:-1]) + "@"
            hostname_part = parts[-1]
        else:
            # ssh://h<TAB>
            prefix_part = f"{parsed.scheme}://"
            hostname_part = text[len(prefix_part) :]

        # Get SSH hosts
        hosts = self._get_ssh_hosts()

        # Filter and create completions
        completions = []
        for host in hosts:
            if host.startswith(hostname_part):
                # Use rsync-style format: ssh://hostname:/path (user-friendly)
                completions.append(Completion(text=host + ":/", start_position=-len(hostname_part), display=host))

        return sorted(completions, key=lambda c: c.text)

    def _get_ssh_hosts(self) -> list[str]:
        """Parse ~/.ssh/config for Host entries."""
        if self._ssh_hosts is not None:
            return self._ssh_hosts

        hosts = []
        ssh_config_path = Path.home() / ".ssh" / "config"

        if ssh_config_path.exists():
            try:
                with open(ssh_config_path) as f:
                    for line in f:
                        line = line.strip()
                        # Match "Host <hostname>" or "Host <pattern>"
                        if line.startswith("Host ") and not line.startswith("Host *"):
                            host_line = line[5:].strip()
                            # Skip patterns with wildcards
                            if "*" not in host_line and "?" not in host_line:
                                # Can have multiple hosts on one line
                                for host in host_line.split():
                                    if host and host not in hosts:
                                        hosts.append(host)
            except Exception:
                pass

        self._ssh_hosts = hosts
        return hosts

    def _parse_ssh_config(self, alias: str) -> dict[str, str]:
        """Parse SSH config to get connection details for an alias.

        Args:
            alias: SSH host alias (e.g., 'mn5', 'lumi')

        Returns:
            Dictionary with 'hostname', 'user', 'port', 'identity_file'
        """
        ssh_config_path = Path.home() / ".ssh" / "config"
        config = {
            "hostname": alias,  # Default to alias if not found
            "user": os.getenv("USER"),
            "port": 22,
            "identity_file": None,
        }

        if not ssh_config_path.exists():
            return config

        try:
            in_target_host = False

            with open(ssh_config_path) as f:
                for line in f:
                    line = line.strip()

                    # New Host section
                    if line.startswith("Host "):
                        host_line = line[5:].strip()
                        # Check if this is our target host
                        hosts_in_line = host_line.split()
                        in_target_host = alias in hosts_in_line
                        continue

                    # Parse config options for our target host
                    if in_target_host and line:
                        parts = line.split(None, 1)
                        if len(parts) == 2:
                            key, value = parts
                            key_lower = key.lower()

                            if key_lower == "hostname":
                                config["hostname"] = value
                            elif key_lower == "user":
                                config["user"] = value
                            elif key_lower == "port":
                                try:
                                    config["port"] = int(value)
                                except ValueError:
                                    pass
                            elif key_lower == "identityfile":
                                # Expand ~ in identity file path
                                identity_path = os.path.expanduser(value)
                                config["identity_file"] = identity_path

        except Exception:
            pass

        return config

    def _complete_path(self, uri: str) -> list[Completion]:
        """Complete filesystem paths for a given URI."""
        try:
            # First normalize the URI for parsing (remove rsync-style colon)
            normalized_uri = normalize_uri_for_fsspec(uri)
            parsed = urlparse(normalized_uri)

            # Determine the base URI and the path to complete
            if parsed.scheme in ("ssh", "sftp", "s3"):
                # Remote URI
                if not parsed.netloc:
                    # Still typing the host
                    return []

                # Extract the path component
                path = parsed.path or "/"

                # Determine directory and filename parts
                if path.endswith("/"):
                    directory = path
                    prefix = ""
                else:
                    directory = os.path.dirname(path) or "/"
                    prefix = os.path.basename(path)

                # Build the base URI (protocol + netloc) for fsspec
                base_uri = f"{parsed.scheme}://{parsed.netloc}"

                return self._complete_from_fsspec(base_uri, directory, prefix, uri)

            else:
                # Local filesystem (file:// or no scheme)
                path = parsed.path if parsed.scheme == "file" else uri

                # Expand user home
                if self.expanduser and path.startswith("~"):
                    path = os.path.expanduser(path)

                # Determine directory and filename parts
                if path.endswith("/"):
                    directory = path
                    prefix = ""
                else:
                    directory = os.path.dirname(path) or "/"
                    prefix = os.path.basename(path)

                return self._complete_local(directory, prefix, uri)

        except Exception:
            # If anything fails, return empty completions
            return []

    def _complete_local(self, directory: str, prefix: str, original_uri: str) -> list[Completion]:
        """Complete local filesystem paths."""
        try:
            if not os.path.isdir(directory):
                return []

            entries = os.listdir(directory)
            completions = []

            for entry in entries:
                if not entry.startswith(prefix):
                    continue

                full_path = os.path.join(directory, entry)
                is_dir = os.path.isdir(full_path)

                if self.only_directories and not is_dir:
                    continue

                display_name = entry + ("/" if is_dir else "")
                completions.append(
                    Completion(text=entry + ("/" if is_dir else ""), start_position=-len(prefix), display=display_name)
                )

            return sorted(completions, key=lambda c: c.text.lower())

        except Exception:
            return []

    def _complete_from_fsspec(self, base_uri: str, directory: str, prefix: str, original_uri: str) -> list[Completion]:
        """Complete paths using fsspec."""
        try:
            # Get or create filesystem
            fs = self._get_filesystem(base_uri)

            # If it's a dummy filesystem (connection failed), show a hint
            if isinstance(fs, type(self)._DummyFS):
                return [
                    Completion(
                        text="",
                        start_position=0,
                        display="(SSH connection failed - check credentials)",
                        style="class:completion.error",
                    )
                ]

            # Cache key
            cache_key = f"{base_uri}:{directory}"

            # Check cache (30 second TTL)
            import time

            current_time = time.time()
            if cache_key in self._cache:
                cached_entries, cached_time = self._cache[cache_key]
                if current_time - cached_time < 30:
                    entries = cached_entries
                else:
                    entries = self._list_directory(fs, directory)
                    self._cache[cache_key] = (entries, current_time)
            else:
                # Show loading indicator on first fetch
                entries = self._list_directory(fs, directory)
                if entries:
                    self._cache[cache_key] = (entries, current_time)

            # Filter and create completions
            completions = []
            for entry in entries:
                name = entry["name"]
                is_dir = entry["type"] == "directory"

                if not name.startswith(prefix):
                    continue

                if self.only_directories and not is_dir:
                    continue

                display_name = name + ("/" if is_dir else "")
                completions.append(
                    Completion(text=name + ("/" if is_dir else ""), start_position=-len(prefix), display=display_name)
                )

            # If no completions, show a hint
            if not completions and not prefix:
                return [
                    Completion(
                        text="", start_position=0, display="(no files found or connection issue)", style="class:completion.info"
                    )
                ]

            return sorted(completions, key=lambda c: c.text.lower())

        except Exception as e:
            # If remote completion fails, show error message
            return [Completion(text="", start_position=0, display=f"(error: {str(e)[:50]})", style="class:completion.error")]

    def _list_directory(self, fs, directory: str) -> list[dict]:
        """List directory contents using fsspec."""
        try:
            # Normalize directory path
            if not directory.endswith("/"):
                directory += "/"

            # List directory
            try:
                entries = fs.ls(directory, detail=True)
            except (FileNotFoundError, OSError):
                return []

            # Convert to standard format
            result = []
            for entry in entries:
                if isinstance(entry, dict):
                    name = os.path.basename(entry.get("name", ""))
                    entry_type = entry.get("type", "file")
                else:
                    name = os.path.basename(str(entry))
                    try:
                        entry_type = "directory" if fs.isdir(entry) else "file"
                    except Exception:
                        # Fallback to file if we can't determine type
                        entry_type = "file"

                if name:  # Skip empty names
                    result.append({"name": name, "type": entry_type})

            return result

        except Exception:
            return []

    def _get_filesystem(self, base_uri: str):
        """Get or create fsspec filesystem for a URI."""
        if base_uri in self._fs_cache:
            return self._fs_cache[base_uri]

        # Parse to get protocol
        parsed = urlparse(base_uri)
        protocol = parsed.scheme

        # Create filesystem based on protocol
        if protocol == "s3":
            # S3 filesystem
            fs = fsspec.filesystem("s3", anon=False)
        elif protocol in ("ssh", "sftp"):
            # SSH filesystem - parse SSH config for proper settings
            try:
                # Extract the hostname/alias from the URI
                # Could be: ssh://mn5 or ssh://user@mn5 or ssh://mn5:
                hostname = parsed.hostname or parsed.netloc.rstrip(":")

                # Parse SSH config to get real hostname, username, port, etc.
                ssh_config = self._parse_ssh_config(hostname)

                # Build fsspec filesystem with proper settings
                fs_kwargs = {
                    "host": ssh_config["hostname"],
                    "username": parsed.username or ssh_config["user"],
                    "port": ssh_config["port"],
                }

                # Note: fsspec's sshfs uses asyncssh which automatically discovers keys from
                # ~/.ssh/ and ssh-agent, so we don't need to explicitly specify key_filename

                fs = fsspec.filesystem(protocol, **fs_kwargs)
            except Exception as e:
                # If SSH fails, return a dummy filesystem
                # Store the error for debugging
                fs = self._DummyFS()
                fs._error = str(e)  # Store error on instance
        else:
            # Default to local filesystem
            fs = fsspec.filesystem("file")

        self._fs_cache[base_uri] = fs
        return fs


class GlobPatternCompleter(FsspecPathCompleter):
    """Path completer that suggests glob patterns for matching multiple files."""

    def get_completions(self, document: Document, complete_event) -> list[Completion]:
        """Get completions with glob pattern suggestions."""
        text = document.text_before_cursor

        # Get base completions from parent
        base_completions = super().get_completions(document, complete_event)

        # If the path ends with a directory, suggest common glob patterns
        if text.endswith("/"):
            glob_patterns = [
                ("**/*.log", "All .log files recursively"),
                ("**/*.out", "All .out files recursively"),
                ("**/*.err", "All .err files recursively"),
                ("*.log", "All .log files in this directory"),
                ("*", "All files in this directory"),
            ]

            for pattern, description in glob_patterns:
                base_completions.append(
                    Completion(
                        text=pattern,
                        start_position=0,
                        display=f"{pattern:<20} {description}",
                        style="class:completion.glob-pattern",
                    )
                )

        return base_completions
