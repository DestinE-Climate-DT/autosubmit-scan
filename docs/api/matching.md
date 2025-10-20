# Matching Module

Pattern matching engine for error detection in log files.

## Overview

The matching module provides:
- **Pattern Matchers**: Literal, regex, and callable pattern implementations
- **Stream Reader**: Memory-efficient file reading for large files
- **Context Extractor**: Extract surrounding lines for error context
- **Match Builder**: Build ErrorMatch objects from raw matches

## Module Structure

```
src/matching/
├── __init__.py
├── pattern_matcher.py    # Pattern matcher implementations
├── stream_reader.py      # Memory-efficient file reading
├── context_extractor.py  # Context extraction
├── match_builder.py      # ErrorMatch construction
└── callable_loader.py    # Load custom callable patterns
```

## Pattern Matchers

```{eval-rst}
.. automodule:: src.matching.pattern_matcher
   :members:
   :undoc-members:
   :show-inheritance:
```

## Stream Reader

```{eval-rst}
.. automodule:: src.matching.stream_reader
   :members:
   :undoc-members:
   :show-inheritance:
```

## Context Extractor

```{eval-rst}
.. automodule:: src.matching.context_extractor
   :members:
   :undoc-members:
   :show-inheritance:
```

## Match Builder

```{eval-rst}
.. automodule:: src.matching.match_builder
   :members:
   :undoc-members:
   :show-inheritance:
```

## Callable Loader

```{eval-rst}
.. automodule:: src.matching.callable_loader
   :members:
   :undoc-members:
   :show-inheritance:
```

## See Also

- [Pattern Matching Tutorial](../tutorials/02_pattern_matching.ipynb)
- [Pattern Matching Guide](../how-to/pattern-matching.md)
