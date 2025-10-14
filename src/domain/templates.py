"""Template loading and rendering utilities.

Supports loading templates from any fsspec-compatible location.
"""

import os
from pathlib import Path
from typing import Any

import fsspec
from jinja2 import Template, TemplateError
from loguru import logger


def is_fsspec_uri(path: str) -> bool:
    """Check if a path is an fsspec URI (has a protocol).

    Args:
        path: Path or URI string

    Returns:
        True if path contains an fsspec protocol, False otherwise
    """
    return "://" in path and not path.startswith("file://")


def load_template(uri: str) -> str:
    """Load a template from any fsspec-compatible location.

    Supports:
    - Local files: /path/to/template.yaml
    - GitHub: github://org:repo@ref/path/to/template.yaml
    - SSH: ssh://host/path/to/template.yaml
    - S3: s3://bucket/path/to/template.yaml
    - HTTP: https://example.com/template.yaml

    Args:
        uri: Path or URI to template file

    Returns:
        Template content as string

    Raises:
        FileNotFoundError: If template not found
        RuntimeError: If template cannot be loaded
    """
    if is_fsspec_uri(uri):
        # Special handling for GitHub URIs (fsspec has issues with branch names containing /)
        if uri.startswith("github://"):
            try:
                # Parse GitHub URI manually: github://org:repo@ref/path/to/file
                parts = uri.replace("github://", "").split("@", 1)
                if len(parts) != 2:
                    raise ValueError(f"Invalid GitHub URI format: {uri}")

                org_repo = parts[0]
                ref_and_path = parts[1]

                # Split org:repo
                if ":" not in org_repo:
                    raise ValueError(f"Invalid GitHub URI format (missing :): {uri}")
                org, repo = org_repo.split(":", 1)

                # Find where the path starts (after known path markers or first /)
                path_markers = ["templates/", "examples/", "src/", "docs/"]
                ref = None
                file_path = None

                for marker in path_markers:
                    if marker in ref_and_path:
                        ref, file_path = ref_and_path.split(marker, 1)
                        file_path = marker + file_path
                        ref = ref.rstrip("/")  # Remove trailing slash from ref
                        break

                if ref is None:
                    # Fall back to splitting on first /
                    if "/" in ref_and_path:
                        ref, file_path = ref_and_path.split("/", 1)
                    else:
                        raise ValueError(f"Invalid GitHub URI format (no path): {uri}")

                # Get GitHub credentials
                github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
                github_username = os.environ.get("GITHUB_USERNAME") or os.environ.get("GH_USERNAME")

                # Create GitHub filesystem with manual parameters
                if github_token and github_username:
                    fs = fsspec.filesystem("github", org=org, repo=repo, sha=ref, username=github_username, token=github_token)
                    logger.debug(f"Using authenticated GitHub access as {github_username}")
                else:
                    fs = fsspec.filesystem("github", org=org, repo=repo, sha=ref)
                    logger.debug("No GitHub credentials found - using unauthenticated access (rate limited)")

                # Read the file
                with fs.open(file_path, "r") as f:
                    content = f.read()
                return content

            except Exception as e:
                raise FileNotFoundError(f"Template not found at URI: {uri}") from e

        else:
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


def render_template(template_str: str, variables: dict[str, Any]) -> str:
    """Render a Jinja2 template with variables.

    Args:
        template_str: Template string
        variables: Dictionary of variables to render

    Returns:
        Rendered template string

    Raises:
        TemplateError: If template rendering fails
    """
    try:
        template = Template(template_str)
        rendered = template.render(**variables)
        return rendered
    except TemplateError as e:
        raise ValueError(f"Failed to render template: {e}") from e


def load_and_render_template(uri: str, variables: dict[str, Any]) -> str:
    """Load and render a template from any fsspec location.

    Args:
        uri: Path or URI to template file
        variables: Dictionary of variables to render

    Returns:
        Rendered template string

    Raises:
        FileNotFoundError: If template not found
        RuntimeError: If template cannot be loaded
        ValueError: If template rendering fails
    """
    template_str = load_template(uri)
    return render_template(template_str, variables)
