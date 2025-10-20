# Reporting Module

Result generation and visualization including JSON-LD, templates, and TUI.

## Overview

The reporting module provides:
- **JSON-LD Generation**: Semantic report format
- **Template Rendering**: Jinja2-based export (Markdown, HTML, text)
- **TUI**: Interactive terminal interface (Textual)
- **Aggregation**: Combine scan results
- **CLI Commands**: Report-related commands

## Module Structure

```
src/reporting/
├── __init__.py
├── jsonld.py            # JSON-LD report generation
├── templates.py         # Template rendering
├── tui.py              # Terminal user interface
├── aggregator.py       # Result aggregation
├── cli_commands.py     # Reporting CLI commands
└── templates/          # Jinja2 templates
    ├── report.md.j2
    ├── report.html.j2
    └── summary.txt.j2
```

## JSON-LD Reports

```{eval-rst}
.. automodule:: src.reporting.jsonld
   :members:
   :undoc-members:
   :show-inheritance:
```

## Template Rendering

```{eval-rst}
.. automodule:: src.reporting.templates
   :members:
   :undoc-members:
   :show-inheritance:
```

## Terminal UI (TUI)

```{eval-rst}
.. automodule:: src.reporting.tui
   :members:
   :undoc-members:
   :show-inheritance:
```

## Result Aggregation

```{eval-rst}
.. automodule:: src.reporting.aggregator
   :members:
   :undoc-members:
   :show-inheritance:
```

## CLI Commands

```{eval-rst}
.. automodule:: src.reporting.cli_commands
   :members:
   :undoc-members:
   :show-inheritance:
```

## See Also

- [Export Reports Tutorial](../tutorials/07_export_reports.ipynb)
- [Template Variables Reference](../reference/template-variables.md)
- [Custom Templates Guide](../how-to/custom-templates.md)
