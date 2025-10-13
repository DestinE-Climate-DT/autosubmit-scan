"""Template loading and rendering utilities.

Supports loading templates from any fsspec-compatible location.
"""

from pathlib import Path
from typing import Any

import fsspec
from jinja2 import Template, TemplateError


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
        # Use fsspec to open remote URIs
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
