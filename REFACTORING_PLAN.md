# Refactoring Plan: Critical Issues

This document provides a step-by-step plan to fix the critical architectural issues identified in ARCHITECTURE_REVIEW.md.

---

## Phase 1: Create Infrastructure Layer (Day 1-2)

### Step 1.1: Create infrastructure package

```bash
mkdir -p src/infrastructure
touch src/infrastructure/__init__.py
```

### Step 1.2: Create uri_utils.py

**File**: `src/infrastructure/uri_utils.py`

```python
"""URI utility functions for fsspec URIs."""

def is_remote_uri(uri: str) -> bool:
    """Check if URI is a remote fsspec URI (not local file).

    Args:
        uri: Path or URI string

    Returns:
        True if URI has a protocol and is not file://

    Examples:
        >>> is_remote_uri("s3://bucket/path")
        True
        >>> is_remote_uri("/local/path")
        False
        >>> is_remote_uri("file:///local/path")
        False
    """
    return "://" in uri and not uri.startswith("file://")


def is_github_uri(uri: str) -> bool:
    """Check if URI is a GitHub URI.

    Args:
        uri: URI string to check

    Returns:
        True if URI starts with github://
    """
    return uri.startswith("github://")


def is_ssh_uri(uri: str) -> bool:
    """Check if URI is SSH/SFTP URI.

    Args:
        uri: URI string to check

    Returns:
        True if URI is ssh:// or sftp://
    """
    return uri.startswith(("ssh://", "sftp://"))


def is_s3_uri(uri: str) -> bool:
    """Check if URI is an S3 URI.

    Args:
        uri: URI string to check

    Returns:
        True if URI starts with s3://
    """
    return uri.startswith("s3://")


def normalize_rsync_uri(uri: str) -> str:
    """Normalize rsync-style SSH/SFTP URIs to standard format.

    Converts: ssh://host:/path -> ssh://host/path

    Args:
        uri: URI potentially in rsync format

    Returns:
        Normalized URI

    Examples:
        >>> normalize_rsync_uri("ssh://lumi:/home/test.txt")
        'ssh://lumi/home/test.txt'
        >>> normalize_rsync_uri("ssh://lumi/home/test.txt")
        'ssh://lumi/home/test.txt'
    """
    if "://" not in uri:
        return uri

    scheme, rest = uri.split("://", 1)

    if scheme in ("ssh", "sftp") and ":/" in rest:
        # Remove the colon: hostname:/path -> hostname/path
        rest = rest.replace(":/", "/", 1)
        return f"{scheme}://{rest}"

    return uri
```

**Tests**: `tests/infrastructure/test_uri_utils.py`

```python
import pytest
from src.infrastructure.uri_utils import (
    is_remote_uri,
    is_github_uri,
    is_ssh_uri,
    is_s3_uri,
    normalize_rsync_uri,
)


class TestIsRemoteURI:
    def test_s3_uri(self):
        assert is_remote_uri("s3://bucket/path") is True

    def test_ssh_uri(self):
        assert is_remote_uri("ssh://host/path") is True

    def test_github_uri(self):
        assert is_remote_uri("github://org:repo@main/path") is True

    def test_local_absolute_path(self):
        assert is_remote_uri("/local/path") is False

    def test_file_uri(self):
        assert is_remote_uri("file:///local/path") is False


class TestNormalizeRsyncURI:
    def test_normalize_ssh_rsync_style(self):
        assert normalize_rsync_uri("ssh://lumi:/home/test.txt") == "ssh://lumi/home/test.txt"

    def test_normalize_sftp_rsync_style(self):
        assert normalize_rsync_uri("sftp://host:/path") == "sftp://host/path"

    def test_already_normalized(self):
        assert normalize_rsync_uri("ssh://host/path") == "ssh://host/path"

    def test_non_ssh_uri(self):
        assert normalize_rsync_uri("s3://bucket/path") == "s3://bucket/path"
```

### Step 1.3: Create ssh_config.py

**File**: `src/infrastructure/ssh_config.py`

```python
"""SSH configuration parsing utilities."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SSHConfig:
    """SSH configuration for a host."""

    hostname: str
    user: str
    port: int = 22
    identity_file: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for fsspec kwargs."""
        return {
            "host": self.hostname,
            "username": self.user,
            "port": self.port,
        }


class SSHConfigParser:
    """Parse OpenSSH configuration files."""

    @staticmethod
    def parse_host(alias: str, config_path: Optional[Path] = None) -> SSHConfig:
        """Parse SSH config to get connection details for an alias.

        Args:
            alias: SSH host alias (e.g., 'mn5', 'lumi')
            config_path: Path to SSH config file (defaults to ~/.ssh/config)

        Returns:
            SSHConfig with resolved connection details

        Examples:
            >>> config = SSHConfigParser.parse_host("myserver")
            >>> print(config.hostname, config.user, config.port)
            'example.com' 'john' 22
        """
        if config_path is None:
            config_path = Path.home() / ".ssh" / "config"

        config = SSHConfig(
            hostname=alias,  # Default to alias if not found
            user=os.getenv("USER", ""),
            port=22,
        )

        if not config_path.exists():
            return config

        in_target_host = False

        with open(config_path) as f:
            for line in f:
                line = line.strip()

                # New Host section
                if line.startswith("Host "):
                    host_line = line[5:].strip()
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
                            config.hostname = value
                        elif key_lower == "user":
                            config.user = value
                        elif key_lower == "port":
                            try:
                                config.port = int(value)
                            except ValueError:
                                pass
                        elif key_lower == "identityfile":
                            config.identity_file = os.path.expanduser(value)

        return config

    @staticmethod
    def list_hosts(config_path: Optional[Path] = None) -> list[str]:
        """List all host aliases from SSH config.

        Args:
            config_path: Path to SSH config file (defaults to ~/.ssh/config)

        Returns:
            List of host aliases (excludes patterns with wildcards)

        Examples:
            >>> hosts = SSHConfigParser.list_hosts()
            >>> print(hosts)
            ['server1', 'server2', 'mn5', 'lumi']
        """
        if config_path is None:
            config_path = Path.home() / ".ssh" / "config"

        hosts = []

        if not config_path.exists():
            return hosts

        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("Host ") and not line.startswith("Host *"):
                    host_line = line[5:].strip()
                    # Skip patterns with wildcards
                    if "*" not in host_line and "?" not in host_line:
                        # Can have multiple hosts on one line
                        for host in host_line.split():
                            if host and host not in hosts:
                                hosts.append(host)

        return hosts
```

**Tests**: `tests/infrastructure/test_ssh_config.py`

```python
import pytest
from pathlib import Path
from src.infrastructure.ssh_config import SSHConfigParser, SSHConfig


@pytest.fixture
def ssh_config_file(tmp_path):
    """Create a temporary SSH config file for testing."""
    config = tmp_path / "config"
    config.write_text("""
Host myserver
    HostName example.com
    User testuser
    Port 2222
    IdentityFile ~/.ssh/mykey

Host server2
    HostName server2.example.com
    User admin

Host *
    ServerAliveInterval 60
""")
    return config


class TestSSHConfigParser:
    def test_parse_host_with_all_settings(self, ssh_config_file):
        config = SSHConfigParser.parse_host("myserver", ssh_config_file)

        assert config.hostname == "example.com"
        assert config.user == "testuser"
        assert config.port == 2222
        assert config.identity_file is not None

    def test_parse_host_with_defaults(self, ssh_config_file):
        config = SSHConfigParser.parse_host("server2", ssh_config_file)

        assert config.hostname == "server2.example.com"
        assert config.user == "admin"
        assert config.port == 22  # Default

    def test_parse_unknown_host(self, ssh_config_file):
        config = SSHConfigParser.parse_host("unknown", ssh_config_file)

        # Should return alias as hostname with defaults
        assert config.hostname == "unknown"
        assert config.port == 22

    def test_list_hosts(self, ssh_config_file):
        hosts = SSHConfigParser.list_hosts(ssh_config_file)

        assert "myserver" in hosts
        assert "server2" in hosts
        assert "*" not in hosts  # Wildcard patterns excluded

    def test_to_dict(self):
        config = SSHConfig(hostname="example.com", user="john", port=2222)
        result = config.to_dict()

        assert result == {
            "host": "example.com",
            "username": "john",
            "port": 2222,
        }
```

### Step 1.4: Create github.py

**File**: `src/infrastructure/github.py`

```python
"""GitHub URI parsing and access utilities."""

import os
from dataclasses import dataclass
from typing import Optional

import fsspec
from loguru import logger


@dataclass
class GitHubURI:
    """Parsed GitHub URI components.

    Represents a GitHub URI in the format:
    github://org:repo@ref/path/to/file
    """

    org: str
    repo: str
    ref: str
    path: str

    def __str__(self) -> str:
        """Reconstruct URI string."""
        return f"github://{self.org}:{self.repo}@{self.ref}/{self.path}"


class GitHubURIError(ValueError):
    """Invalid GitHub URI format."""

    pass


class GitHubURIParser:
    """Parse and validate GitHub URIs.

    Format: github://org:repo@ref/path/to/file

    The ref can contain slashes (e.g., feature/my-branch), so we use
    known path markers to detect where the ref ends and path begins.
    """

    # Canonical list of path markers for detecting ref boundaries
    # Order matters - checked in sequence
    PATH_MARKERS = [
        "templates/",
        "examples/",
        "src/",
        "docs/",
        "config/",
        "catalogs/",
    ]

    @classmethod
    def parse(cls, uri: str) -> GitHubURI:
        """Parse GitHub URI into components.

        Args:
            uri: GitHub URI string

        Returns:
            GitHubURI with parsed components

        Raises:
            GitHubURIError: If URI format is invalid

        Examples:
            >>> parsed = GitHubURIParser.parse(
            ...     "github://DestinE-Climate-DT:autosubmit-scan@main/templates/default.yaml"
            ... )
            >>> print(parsed.org, parsed.repo, parsed.ref, parsed.path)
            'DestinE-Climate-DT' 'autosubmit-scan' 'main' 'templates/default.yaml'
        """
        if not uri.startswith("github://"):
            raise GitHubURIError(f"Not a GitHub URI: {uri}")

        # Remove protocol
        rest = uri[len("github://") :]

        # Split org:repo and ref/path
        if "@" not in rest:
            raise GitHubURIError(f"Invalid GitHub URI (missing @ separator): {uri}")

        org_repo, ref_and_path = rest.split("@", 1)

        # Split org:repo
        if ":" not in org_repo:
            raise GitHubURIError(f"Invalid GitHub URI (missing : separator): {uri}")

        org, repo = org_repo.split(":", 1)

        # Find where ref ends and path begins using path markers
        ref = None
        file_path = None

        for marker in cls.PATH_MARKERS:
            # Look for /marker in the ref_and_path
            if f"/{marker}" in ref_and_path:
                ref, file_path = ref_and_path.split(f"/{marker}", 1)
                file_path = marker + file_path
                break

        if ref is None or file_path is None:
            raise GitHubURIError(
                f"Cannot parse GitHub URI (missing known path marker): {uri}\n"
                f"Expected one of: {', '.join(cls.PATH_MARKERS)}\n"
                f"Add your path prefix to GitHubURIParser.PATH_MARKERS if needed."
            )

        return GitHubURI(org=org, repo=repo, ref=ref, path=file_path)

    @staticmethod
    def get_credentials() -> tuple[Optional[str], Optional[str]]:
        """Get GitHub credentials from environment.

        Checks the following environment variables:
        - GITHUB_USERNAME or GH_USERNAME
        - GITHUB_TOKEN or GH_TOKEN

        Returns:
            Tuple of (username, token) or (None, None) if not found

        Examples:
            >>> username, token = GitHubURIParser.get_credentials()
            >>> if username and token:
            ...     print("Authenticated")
            ... else:
            ...     print("Anonymous")
        """
        username = os.environ.get("GITHUB_USERNAME") or os.environ.get("GH_USERNAME")
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

        return (username, token) if username and token else (None, None)

    @classmethod
    def create_filesystem(cls, uri: GitHubURI) -> fsspec.AbstractFileSystem:
        """Create fsspec filesystem for GitHub URI.

        Args:
            uri: Parsed GitHub URI

        Returns:
            GitHub filesystem instance

        Examples:
            >>> parsed = GitHubURIParser.parse("github://org:repo@main/path")
            >>> fs = GitHubURIParser.create_filesystem(parsed)
            >>> with fs.open(parsed.path, "r") as f:
            ...     content = f.read()
        """
        username, token = cls.get_credentials()

        fs_kwargs = {"org": uri.org, "repo": uri.repo, "sha": uri.ref}

        if username and token:
            fs_kwargs["username"] = username
            fs_kwargs["token"] = token
            logger.debug(f"Using authenticated GitHub access as {username}")
        else:
            logger.debug("No GitHub credentials - using anonymous access (rate limited)")

        return fsspec.filesystem("github", **fs_kwargs)
```

**Tests**: `tests/infrastructure/test_github.py`

```python
import pytest
from src.infrastructure.github import GitHubURIParser, GitHubURIError, GitHubURI


class TestGitHubURIParser:
    def test_parse_simple_uri(self):
        uri = "github://org:repo@main/templates/file.yaml"
        parsed = GitHubURIParser.parse(uri)

        assert parsed.org == "org"
        assert parsed.repo == "repo"
        assert parsed.ref == "main"
        assert parsed.path == "templates/file.yaml"

    def test_parse_branch_with_slash(self):
        uri = "github://org:repo@feature/my-branch/templates/file.yaml"
        parsed = GitHubURIParser.parse(uri)

        assert parsed.org == "org"
        assert parsed.repo == "repo"
        assert parsed.ref == "feature/my-branch"
        assert parsed.path == "templates/file.yaml"

    def test_parse_real_uri(self):
        uri = "github://DestinE-Climate-DT:autosubmit-scan@test/dynamic-variables/templates/default.yaml"
        parsed = GitHubURIParser.parse(uri)

        assert parsed.org == "DestinE-Climate-DT"
        assert parsed.repo == "autosubmit-scan"
        assert parsed.ref == "test/dynamic-variables"
        assert parsed.path == "templates/default.yaml"

    def test_parse_missing_protocol(self):
        with pytest.raises(GitHubURIError, match="Not a GitHub URI"):
            GitHubURIParser.parse("http://example.com/file")

    def test_parse_missing_at_separator(self):
        with pytest.raises(GitHubURIError, match="missing @ separator"):
            GitHubURIParser.parse("github://org:repo/path")

    def test_parse_missing_colon_separator(self):
        with pytest.raises(GitHubURIError, match="missing : separator"):
            GitHubURIParser.parse("github://org-repo@main/path")

    def test_parse_unknown_path_marker(self):
        with pytest.raises(GitHubURIError, match="missing known path marker"):
            GitHubURIParser.parse("github://org:repo@main/unknown/path.yaml")

    def test_reconstruct_uri(self):
        original = "github://org:repo@main/templates/file.yaml"
        parsed = GitHubURIParser.parse(original)
        reconstructed = str(parsed)

        assert reconstructed == original

    def test_get_credentials_none(self, monkeypatch):
        monkeypatch.delenv("GITHUB_USERNAME", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_USERNAME", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)

        username, token = GitHubURIParser.get_credentials()

        assert username is None
        assert token is None

    def test_get_credentials_from_env(self, monkeypatch):
        monkeypatch.setenv("GITHUB_USERNAME", "testuser")
        monkeypatch.setenv("GITHUB_TOKEN", "testtoken")

        username, token = GitHubURIParser.get_credentials()

        assert username == "testuser"
        assert token == "testtoken"
```

---

## Phase 2: Create Configuration Module (Day 2)

### Step 2.1: Create config.py

**File**: `src/config.py`

```python
"""Centralized configuration for autosubmit-scan.

All configuration is accessed through get_config().
Environment variables are read once at startup.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AutosubmitScanConfig:
    """Configuration for autosubmit-scan.

    All settings can be overridden via environment variables.
    """

    # GitHub repository for default templates
    default_template_repo_org: str = "DestinE-Climate-DT"
    default_template_repo_name: str = "autosubmit-scan-error-catalogs"
    default_template_branch: str = "main"
    default_template_path: str = "templates/default_autosubmit.yaml"

    # Autosubmit defaults
    autosubmit_default_host: str = "mn5"
    autosubmit_default_base_path: str = "/gpfs/scratch/ehpc01/awi478153"

    # GitHub credentials
    github_username: Optional[str] = None
    github_token: Optional[str] = None

    @classmethod
    def from_env(cls) -> "AutosubmitScanConfig":
        """Create configuration from environment variables.

        Environment variables:
            AUTOSUBMIT_SCAN_TEMPLATE_ORG: GitHub org for templates
            AUTOSUBMIT_SCAN_TEMPLATE_REPO: GitHub repo for templates
            AUTOSUBMIT_SCAN_TEMPLATE_BRANCH: Branch to use
            AUTOSUBMIT_SCAN_TEMPLATE_PATH: Path within repo
            AUTOSUBMIT_HOST: Default SSH host for Autosubmit
            AUTOSUBMIT_BASE_PATH: Default base path for experiments
            GITHUB_USERNAME or GH_USERNAME: GitHub username
            GITHUB_TOKEN or GH_TOKEN: GitHub token

        Returns:
            Config instance with values from environment
        """
        return cls(
            default_template_repo_org=os.getenv("AUTOSUBMIT_SCAN_TEMPLATE_ORG", cls.default_template_repo_org),
            default_template_repo_name=os.getenv("AUTOSUBMIT_SCAN_TEMPLATE_REPO", cls.default_template_repo_name),
            default_template_branch=os.getenv("AUTOSUBMIT_SCAN_TEMPLATE_BRANCH", cls.default_template_branch),
            default_template_path=os.getenv("AUTOSUBMIT_SCAN_TEMPLATE_PATH", cls.default_template_path),
            autosubmit_default_host=os.getenv("AUTOSUBMIT_HOST", cls.autosubmit_default_host),
            autosubmit_default_base_path=os.getenv("AUTOSUBMIT_BASE_PATH", cls.autosubmit_default_base_path),
            github_username=os.getenv("GITHUB_USERNAME") or os.getenv("GH_USERNAME"),
            github_token=os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN"),
        )

    @property
    def default_template_uri(self) -> str:
        """Get complete URI for default template.

        Returns:
            GitHub URI for default catalog template

        Examples:
            >>> config = get_config()
            >>> print(config.default_template_uri)
            'github://DestinE-Climate-DT:autosubmit-scan-error-catalogs@main/templates/default_autosubmit.yaml'
        """
        return (
            f"github://{self.default_template_repo_org}:"
            f"{self.default_template_repo_name}@{self.default_template_branch}/"
            f"{self.default_template_path}"
        )


# Global config instance (singleton)
_config: Optional[AutosubmitScanConfig] = None


def get_config() -> AutosubmitScanConfig:
    """Get global configuration instance.

    Configuration is loaded once on first call and cached.

    Returns:
        Global config instance

    Examples:
        >>> config = get_config()
        >>> print(config.default_template_uri)
    """
    global _config
    if _config is None:
        _config = AutosubmitScanConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset configuration (mainly for testing).

    Forces configuration to be reloaded on next get_config() call.
    """
    global _config
    _config = None
```

**Tests**: `tests/test_config.py`

```python
import pytest
from src.config import get_config, reset_config, AutosubmitScanConfig


class TestConfig:
    def test_default_values(self, monkeypatch):
        # Clear environment
        for key in [
            "AUTOSUBMIT_SCAN_TEMPLATE_ORG",
            "AUTOSUBMIT_SCAN_TEMPLATE_REPO",
            "GITHUB_USERNAME",
            "GITHUB_TOKEN",
        ]:
            monkeypatch.delenv(key, raising=False)

        reset_config()
        config = get_config()

        assert config.default_template_repo_org == "DestinE-Climate-DT"
        assert config.default_template_branch == "main"
        assert config.github_username is None

    def test_override_from_env(self, monkeypatch):
        monkeypatch.setenv("AUTOSUBMIT_SCAN_TEMPLATE_ORG", "MyOrg")
        monkeypatch.setenv("AUTOSUBMIT_SCAN_TEMPLATE_BRANCH", "dev")
        monkeypatch.setenv("GITHUB_USERNAME", "testuser")
        monkeypatch.setenv("GITHUB_TOKEN", "testtoken")

        reset_config()
        config = get_config()

        assert config.default_template_repo_org == "MyOrg"
        assert config.default_template_branch == "dev"
        assert config.github_username == "testuser"
        assert config.github_token == "testtoken"

    def test_default_template_uri(self):
        reset_config()
        config = get_config()

        uri = config.default_template_uri

        assert uri.startswith("github://")
        assert "DestinE-Climate-DT" in uri
        assert "@main/" in uri

    def test_singleton_pattern(self):
        reset_config()
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2  # Same instance
```

---

## Phase 3: Update Existing Code (Day 3)

### Step 3.1: Update catalog.py

Replace GitHub parsing logic (lines 65-108) with:

```python
from src.infrastructure.github import GitHubURIParser, GitHubURIError
from src.infrastructure.uri_utils import is_remote_uri, is_github_uri

def load_catalog(path: str) -> ErrorCatalog:
    """Load error catalog from YAML file or fsspec URI."""
    if is_github_uri(path):
        try:
            parsed = GitHubURIParser.parse(path)
            fs = GitHubURIParser.create_filesystem(parsed)

            with fs.open(parsed.path, "r") as f:
                data = yaml.safe_load(f)

        except GitHubURIError as e:
            raise ValueError(f"Invalid GitHub URI: {e}") from e
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Catalog not found at URI: {path}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to load catalog from {path}: {e}") from e

    elif is_remote_uri(path):
        # Use fsspec for other remote URIs
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

    # ... rest of function stays the same
```

Remove the `is_fsspec_uri()` function entirely.

### Step 3.2: Update templates.py

Replace GitHub parsing logic (lines 49-101) with:

```python
from src.infrastructure.github import GitHubURIParser, GitHubURIError
from src.infrastructure.uri_utils import is_remote_uri, is_github_uri

def load_template(uri: str) -> str:
    """Load a template from any fsspec-compatible location."""
    if is_github_uri(uri):
        try:
            parsed = GitHubURIParser.parse(uri)
            fs = GitHubURIParser.create_filesystem(parsed)

            with fs.open(parsed.path, "r") as f:
                content = f.read()
            return content

        except GitHubURIError as e:
            raise ValueError(f"Invalid GitHub URI: {e}") from e
        except Exception as e:
            raise FileNotFoundError(f"Template not found at URI: {uri}") from e

    elif is_remote_uri(uri):
        # Use fsspec to open other remote URIs
        try:
            with fsspec.open(uri, "r") as f:
                content = f.read()
            return content
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Template not found at URI: {uri}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to load template from {uri}: {e}") from e
    else:
        # Use local file path
        file_path = Path(uri)

        if not file_path.exists():
            raise FileNotFoundError(f"Template file not found: {uri}")

        with open(file_path) as f:
            return f.read()
```

Remove the `is_fsspec_uri()` function entirely.

### Step 3.3: Update variable_extractor.py

Replace `_is_fsspec_uri()` function with import:

```python
from src.infrastructure.uri_utils import is_remote_uri

def _read_file_content(path: str) -> str:
    """Read file content from local path or fsspec URI."""
    if is_remote_uri(path):
        # ... rest stays the same
```

Remove the `_is_fsspec_uri()` function entirely.

### Step 3.4: Update completion.py

Replace both `_parse_ssh_config()` and `_parse_ssh_config_standalone()` with:

```python
from src.infrastructure.ssh_config import SSHConfigParser
from src.infrastructure.uri_utils import normalize_rsync_uri

# In normalize_uri_for_fsspec(), just call:
def normalize_uri_for_fsspec(uri: str) -> str:
    """Convert rsync-style URIs to fsspec format."""
    return normalize_rsync_uri(uri)

# In get_fsspec_filesystem():
def get_fsspec_filesystem(uri: str):
    """Get fsspec filesystem for a given URI with SSH config support."""
    normalized_uri = normalize_rsync_uri(uri)
    parsed = urlparse(normalized_uri)
    protocol = parsed.scheme or "file"

    if protocol in ("ssh", "sftp"):
        hostname = parsed.hostname or parsed.netloc.rstrip(":/")
        ssh_config = SSHConfigParser.parse_host(hostname)  # Use new function

        # ... rest of logic using ssh_config.to_dict()

# In FsspecPathCompleter.__init__():
def __init__(self, ...):
    self._ssh_hosts = None  # Will use SSHConfigParser.list_hosts()

# In _get_ssh_hosts():
def _get_ssh_hosts(self) -> list[str]:
    """Parse ~/.ssh/config for Host entries."""
    if self._ssh_hosts is not None:
        return self._ssh_hosts

    self._ssh_hosts = SSHConfigParser.list_hosts()
    return self._ssh_hosts

# Remove both _parse_ssh_config() methods entirely
```

### Step 3.5: Update default.py

Replace hardcoded DEFAULT_TEMPLATE_URI with:

```python
from src.config import get_config

# Remove old DEFAULT_TEMPLATE_URI definition
# Replace with:
def run_default_scan(expid: str, verbose: int = 0):
    """Run default scan for an Autosubmit experiment."""
    config = get_config()

    logger.info(f"Running default scan for experiment: {expid}")

    # Try to load catalog from remote URI
    catalog_path = None
    catalog_source = None

    try:
        template_uri = config.default_template_uri
        logger.info(f"Loading catalog from: {template_uri}")
        catalog_yaml = load_template(template_uri)
        catalog_source = template_uri
        # ... rest stays the same
```

---

## Phase 4: Testing (Day 4)

### Step 4.1: Run existing tests

```bash
pixi run test-unit
```

Fix any broken imports or tests.

### Step 4.2: Add new tests

Create test files as specified in Phase 1 steps.

### Step 4.3: Integration testing

```bash
pixi run test-integration
```

---

## Phase 5: Documentation (Day 4)

### Step 5.1: Update CLAUDE.md

Add section on new infrastructure layer:

```markdown
## Infrastructure Layer

New in v1.0: Infrastructure utilities for remote access.

### GitHub URIs

Parse GitHub URIs:
```python
from src.infrastructure.github import GitHubURIParser

parsed = GitHubURIParser.parse("github://org:repo@main/path")
fs = GitHubURIParser.create_filesystem(parsed)
```

### SSH Configuration

Parse SSH config:
```python
from src.infrastructure.ssh_config import SSHConfigParser

config = SSHConfigParser.parse_host("mn5")
print(config.hostname, config.user, config.port)
```

### URI Utilities

```python
from src.infrastructure.uri_utils import is_remote_uri, is_github_uri

if is_github_uri(uri):
    # Handle GitHub
elif is_remote_uri(uri):
    # Handle other remote
else:
    # Handle local
```

### Configuration

Access configuration:
```python
from src.config import get_config

config = get_config()
print(config.default_template_uri)
```
```

### Step 5.2: Create CHANGELOG.md

```markdown
# Changelog

## [1.0.0] - Unreleased

### Added
- Infrastructure layer for better code organization
- Centralized configuration via `config.py`
- GitHub URI parser and utilities
- SSH config parser and utilities
- URI utility functions

### Changed
- BREAKING: Moved GitHub URI parsing to `src.infrastructure.github`
- BREAKING: Moved SSH config parsing to `src.infrastructure.ssh_config`
- Improved error messages for invalid URIs

### Fixed
- Deduplicated GitHub URI parsing (was in 2 places)
- Deduplicated SSH config parsing (was in 2 places within same file!)
- Deduplicated URI detection (was in 4 files)

### Removed
- Duplicate helper functions across modules
```

---

## Validation Checklist

After completing all phases:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No duplicate code for GitHub URI parsing
- [ ] No duplicate code for SSH config parsing
- [ ] No duplicate code for URI detection
- [ ] Configuration is centralized in config.py
- [ ] All modules use infrastructure layer
- [ ] Documentation updated
- [ ] CHANGELOG.md created
- [ ] No import cycles
- [ ] Code coverage maintained or improved

---

## Rollback Plan

If issues arise:

1. Each phase is in separate commits
2. Can revert individual commits
3. Tests will catch breaking changes immediately

---

## Timeline

- Day 1: Create infrastructure modules (uri_utils, ssh_config)
- Day 2: Create github.py and config.py
- Day 3: Update all existing code to use new modules
- Day 4: Testing and documentation
- Total: 4 days focused work

---

## Questions?

Open an issue if you need clarification on any step.
