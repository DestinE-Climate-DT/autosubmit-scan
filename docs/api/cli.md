# CLI Module

Command-line interface implementation using Click framework.

## Overview

The CLI module provides user-facing commands for interacting with autosubmit-scan:
- `scan` - Run error scanning workflow
- `validate` - Validate error catalogs
- `init` - Create sample catalogs
- `view` - Launch interactive TUI
- `export` - Export reports to various formats
- `check-ssh` - Verify SSH connection pooling

## Module Structure

```
src/cli/
├── __init__.py
├── main.py              # Main CLI entry point
├── types.py             # Custom Click types
├── completion.py        # Shell completion helpers
└── commands/
    ├── __init__.py
    ├── scan.py         # scan command
    ├── validate.py     # validate command
    ├── init.py         # init command
    ├── view.py         # view command
    ├── export.py       # export command
    ├── check_ssh.py    # check-ssh command
    └── dag.py          # dag command (workflow visualization)
```

## Main CLI

```{eval-rst}
.. automodule:: src.cli.main
   :members:
   :undoc-members:
   :show-inheritance:
```

## Command Implementations

### Scan Command

```{eval-rst}
.. automodule:: src.cli.commands.scan
   :members:
   :undoc-members:
   :show-inheritance:
```

### Validate Command

```{eval-rst}
.. automodule:: src.cli.commands.validate
   :members:
   :undoc-members:
   :show-inheritance:
```

### Init Command

```{eval-rst}
.. automodule:: src.cli.commands.init
   :members:
   :undoc-members:
   :show-inheritance:
```

### View Command

```{eval-rst}
.. automodule:: src.cli.commands.view
   :members:
   :undoc-members:
   :show-inheritance:
```

### Export Command

```{eval-rst}
.. automodule:: src.cli.commands.export
   :members:
   :undoc-members:
   :show-inheritance:
```

### Check SSH Command

```{eval-rst}
.. automodule:: src.cli.commands.check_ssh
   :members:
   :undoc-members:
   :show-inheritance:
```

### DAG Command

```{eval-rst}
.. automodule:: src.cli.commands.dag
   :members:
   :undoc-members:
   :show-inheritance:
```

## Custom Types

```{eval-rst}
.. automodule:: src.cli.types
   :members:
   :undoc-members:
   :show-inheritance:
```

## Shell Completion

```{eval-rst}
.. automodule:: src.cli.completion
   :members:
   :undoc-members:
   :show-inheritance:
```

## Usage Examples

### Basic Scan

```python
from src.cli.main import main

# Programmatically invoke CLI (for testing)
import sys
sys.argv = ["as-scan", "scan", "--catalog", "catalog.yaml", "--output", "results"]
main()
```

### Custom Click Types

```python
from src.cli.types import CatalogPath
import click

@click.command()
@click.option("--catalog", type=CatalogPath(), required=True)
def my_command(catalog):
    """Custom command using CatalogPath type."""
    print(f"Catalog: {catalog}")
```

## See Also

- [Command Reference](../reference/cli-commands.md) - Complete command documentation
- [User Guide](../USER_GUIDE.md) - CLI usage guide
- [Click Documentation](https://click.palletsprojects.com/) - Click framework docs
