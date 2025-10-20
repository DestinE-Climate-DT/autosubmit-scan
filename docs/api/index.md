# API Reference

Complete API documentation for autosubmit-scan, organized by module and functionality.

## Module Overview

autosubmit-scan follows a layered architecture with clear separation of concerns:

```{mermaid}
graph TD
    CLI[CLI Layer] --> Domain[Domain Layer]
    CLI --> Matching[Matching Layer]
    CLI --> Orchestration[Orchestration Layer]
    CLI --> Reporting[Reporting Layer]

    Orchestration --> Domain
    Orchestration --> Matching
    Matching --> Domain
    Reporting --> Domain
    Orchestration --> Infrastructure[Infrastructure Layer]

    style CLI fill:#e1f5ff
    style Domain fill:#fff4e1
    style Matching fill:#e8f5e9
    style Orchestration fill:#f3e5f5
    style Reporting fill:#fff3e0
    style Infrastructure fill:#fce4ec
```

## Quick Navigation

### By Layer

- **[CLI Module](cli.md)** - Command-line interface and user commands
- **[Domain Module](domain.md)** - Core data models and business logic
- **[Matching Module](matching.md)** - Pattern matching engine
- **[Orchestration Module](orchestration.md)** - Workflow coordination (Snakemake)
- **[Reporting Module](reporting.md)** - Result generation and visualization
- **[Infrastructure Module](infrastructure.md)** - Low-level utilities and helpers

### By Functionality

#### Catalog Management
- {py:mod}`src.domain.catalog_io` - Load and save error catalogs
- {py:mod}`src.domain.catalog_validation` - Validate catalog structure
- {py:mod}`src.domain.models` - Pydantic data models

#### Pattern Matching
- {py:mod}`src.matching.pattern_matcher` - Pattern matcher implementations
- {py:mod}`src.matching.stream_reader` - Memory-efficient file reading
- {py:mod}`src.matching.context_extractor` - Extract error context
- {py:mod}`src.matching.callable_loader` - Load custom matchers

#### Workflow Execution
- {py:mod}`src.orchestration.scanner` - Main scan orchestration
- {py:mod}`src.orchestration.railway` - Railway pattern execution
- {py:mod}`src.orchestration.condition_evaluator` - Evaluate conditions

#### Report Generation
- {py:mod}`src.reporting.jsonld` - JSON-LD report generation
- {py:mod}`src.reporting.templates` - Template rendering (Jinja2)
- {py:mod}`src.reporting.tui` - Terminal user interface (Textual)
- {py:mod}`src.reporting.aggregator` - Aggregate scan results

## API Design Principles

### Pydantic Models
All data structures use Pydantic v2 for:
- Automatic validation
- Type safety
- JSON/YAML serialization
- Clear error messages

### Type Hints
All public APIs include comprehensive type hints for:
- IDE autocompletion
- Static type checking
- Self-documenting code

### NumPy-Style Docstrings
Documentation follows NumPy/Google style for clarity:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Extended description with more details about the function's
    behavior, algorithm, or important notes.

    Parameters
    ----------
    param1 : str
        Description of param1
    param2 : int
        Description of param2

    Returns
    -------
    bool
        Description of return value

    Raises
    ------
    ValueError
        Description of when this error is raised

    Examples
    --------
    >>> example_function("test", 42)
    True
    """
```

## Common Patterns

### Loading Catalogs

```python
from src.domain.catalog_io import load_catalog

catalog = load_catalog("path/to/catalog.yaml")
print(f"Loaded {len(catalog.errors)} error definitions")
```

### Pattern Matching

```python
from src.matching.pattern_matcher import create_pattern_matcher

matcher = create_pattern_matcher({
    "type": "regex",
    "pattern": r"ERROR|CRITICAL",
    "flags": ["IGNORECASE"]
})

if matcher.match("ERROR: Something failed"):
    print("Pattern matched!")
```

### Railway Pattern Evaluation

```python
from src.orchestration.railway import evaluate_railway_condition
from src.domain.models import ErrorMatch, ErrorDefinition

# Check if condition is met
should_chain = evaluate_railway_condition(
    match=error_match,
    condition=condition_spec,
    error_def=error_definition,
    catalog=catalog
)
```

## API Stability

### Stable APIs (1.0+)
These modules have stable APIs and maintain backward compatibility:
- {py:mod}`src.domain.models` - Core data models
- {py:mod}`src.domain.catalog_io` - Catalog I/O
- {py:mod}`src.matching.pattern_matcher` - Pattern matching

### Evolving APIs (0.x)
These modules may change in future versions:
- {py:mod}`src.reporting.tui` - TUI interface (experimental)
- {py:mod}`src.orchestration.scanner` - Workflow execution (may add features)

### Internal APIs
These modules are for internal use and may change without notice:
- {py:mod}`src.infrastructure.*` - Internal utilities
- {py:mod}`src.matching.match_builder` - Internal matching logic

## See Also

- [User Guide](../USER_GUIDE.md) - High-level usage guide
- [Architecture](../ARCHITECTURE.md) - System design overview
- [Tutorials](../tutorials/01_getting_started.ipynb) - Step-by-step tutorials
