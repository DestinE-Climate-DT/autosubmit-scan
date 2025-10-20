"""GitHub repository access utilities.

Provides centralized GitHub URI parsing and filesystem access.
"""

import os
from typing import Tuple
from collections.abc import Callable

import fsspec
from loguru import logger


class GitHubURIParser:
    """Parse and validate GitHub URIs."""

    # Known path markers to help identify where ref ends and path begins
    DEFAULT_PATH_MARKERS = ["templates/", "examples/", "src/", "docs/", "tests/"]

    @staticmethod
    def parse(uri: str, path_markers: list[str] | None = None) -> Tuple[str, str, str, str]:
        """Parse a GitHub URI into components.

        Format: github://org:repo@ref/path/to/file

        Args:
            uri: GitHub URI to parse
            path_markers: List of path markers to identify ref/path boundary.
                         Defaults to ["templates/", "examples/", "src/", "docs/", "tests/"]

        Returns:
            Tuple of (org, repo, ref, file_path)

        Raises:
            ValueError: If URI format is invalid

        Examples:
            >>> parser = GitHubURIParser()
            >>> parser.parse("github://org:repo@main/templates/file.yaml")
            ('org', 'repo', 'main', 'templates/file.yaml')

            >>> parser.parse("github://org:repo@test/branch/src/file.py")
            ('org', 'repo', 'test/branch', 'src/file.py')
        """
        if not uri.startswith("github://"):
            raise ValueError(f"Invalid GitHub URI (must start with github://): {uri}")

        # Use default path markers if none provided
        if path_markers is None:
            path_markers = GitHubURIParser.DEFAULT_PATH_MARKERS

        # Remove protocol
        uri_without_protocol = uri.replace("github://", "")

        # Split at @
        parts = uri_without_protocol.split("@", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid GitHub URI format (missing @): {uri}")

        org_repo = parts[0]
        ref_and_path = parts[1]

        # Split org:repo
        if ":" not in org_repo:
            raise ValueError(f"Invalid GitHub URI format (missing :): {uri}")
        org, repo = org_repo.split(":", 1)

        # Find where the path starts using path markers
        ref = None
        file_path = None

        for marker in path_markers:
            if marker in ref_and_path:
                ref, file_path = ref_and_path.split(marker, 1)
                file_path = marker + file_path
                ref = ref.rstrip("/")  # Remove trailing slash
                break

        # If no path marker found, fall back to splitting on first /
        if ref is None:
            if "/" in ref_and_path:
                ref, file_path = ref_and_path.split("/", 1)
            else:
                raise ValueError(f"Invalid GitHub URI format (no path): {uri}")

        return org, repo, ref, file_path

    @staticmethod
    def create_filesystem(org: str, repo: str, ref: str) -> fsspec.AbstractFileSystem:
        """Create a GitHub filesystem with authentication if available.

        Args:
            org: GitHub organization
            repo: Repository name
            ref: Branch, tag, or commit SHA

        Returns:
            Configured GitHub filesystem

        Examples:
            >>> fs = GitHubURIParser.create_filesystem("myorg", "myrepo", "main")
            >>> with fs.open("README.md", "r") as f:
            ...     content = f.read()
        """
        # Get GitHub credentials from environment
        github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        github_username = os.environ.get("GITHUB_USERNAME") or os.environ.get("GH_USERNAME")

        # Create filesystem with authentication if available
        if github_token and github_username:
            fs = fsspec.filesystem(
                "github",
                org=org,
                repo=repo,
                sha=ref,  # fsspec uses 'sha' parameter, not 'ref'
                username=github_username,
                token=github_token,
            )
            logger.debug(f"Using authenticated GitHub access as {github_username}")
        else:
            fs = fsspec.filesystem("github", org=org, repo=repo, sha=ref)
            logger.debug("No GitHub credentials found - using unauthenticated access (rate limited)")

        return fs

    @staticmethod
    def load_file(uri: str, path_markers: list[str] | None = None) -> str:
        """Load a file from a GitHub repository.

        Args:
            uri: GitHub URI (github://org:repo@ref/path/to/file)
            path_markers: Optional list of path markers for parsing

        Returns:
            File content as string

        Raises:
            ValueError: If URI is invalid
            FileNotFoundError: If file doesn't exist

        Examples:
            >>> content = GitHubURIParser.load_file(
            ...     "github://myorg:myrepo@main/README.md"
            ... )
        """
        try:
            # Parse URI
            org, repo, ref, file_path = GitHubURIParser.parse(uri, path_markers)

            # Create filesystem
            fs = GitHubURIParser.create_filesystem(org, repo, ref)

            # Read file
            with fs.open(file_path, "r") as f:
                content = f.read()

            return content

        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found in GitHub repository: {uri}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to load file from GitHub: {uri} - {e}") from e
