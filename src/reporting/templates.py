"""Template rendering for error reports.

This module provides Jinja2 template rendering functionality
for generating reports in various formats (Markdown, HTML, plain text).
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class TemplateRenderer:
    """Renders error reports using Jinja2 templates.

    Loads templates from src/reporting/templates/ directory and
    renders them with provided data.
    """

    def __init__(self):
        """Initialize the template renderer with Jinja2 environment."""
        # Get the templates directory path
        templates_dir = Path(__file__).parent / "templates"

        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=False,  # We control the output format
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, data: dict[str, Any], output_path: str) -> None:
        """Render a template with data and write to file.

        Args:
            template_name: Name of the template file (e.g., "report.md.j2")
            data: Dictionary of data to pass to the template
            output_path: Path where the rendered output should be written

        Raises:
            TemplateNotFound: If the template file doesn't exist
        """
        # Load template
        template = self.env.get_template(template_name)

        # Render template with data
        rendered = template.render(**data)

        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write rendered content to file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered)
