# Infrastructure Module

Low-level utilities and helper functions.

## Overview

The infrastructure module provides internal utilities for:
- File system operations (fsspec integration)
- Logging configuration
- Configuration management
- Helper functions

:::{warning}
This module contains internal implementation details that may change without notice.
Use the stable public APIs in other modules when possible.
:::

## Module Structure

```
src/infrastructure/
├── __init__.py
├── filesystem.py      # fsspec filesystem helpers
├── logging.py        # Logging configuration
├── config.py         # Configuration management
└── utils.py          # General utilities
```

## Filesystem Utilities

```{eval-rst}
.. automodule:: src.infrastructure.filesystem
   :members:
   :undoc-members:
   :show-inheritance:
```

## Logging Configuration

```{eval-rst}
.. automodule:: src.infrastructure.logging
   :members:
   :undoc-members:
   :show-inheritance:
```

## Configuration Management

```{eval-rst}
.. automodule:: src.infrastructure.config
   :members:
   :undoc-members:
   :show-inheritance:
```

## Utilities

```{eval-rst}
.. automodule:: src.infrastructure.utils
   :members:
   :undoc-members:
   :show-inheritance:
```

## See Also

- [Architecture Overview](../ARCHITECTURE.md)
- [fsspec Documentation](https://filesystem-spec.readthedocs.io/)
