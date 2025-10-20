# Domain Module

Core business logic and data models using Pydantic v2.

## Overview

The domain module defines the core data structures and validation logic:
- **Models**: Pydantic models for catalogs, errors, matches, and patterns
- **Catalog I/O**: Load and save YAML catalogs
- **Validation**: Schema validation and business rule checks

## Module Structure

```
src/domain/
├── __init__.py
├── models.py              # Pydantic data models
├── catalog_io.py          # Load/save catalogs
└── catalog_validation.py  # Validation logic
```

## Data Models

```{eval-rst}
.. automodule:: src.domain.models
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource
```

### Key Models

#### ErrorCatalog

Top-level container for error definitions.

```python
from src.domain.models import ErrorCatalog

catalog = ErrorCatalog(
    version="1.0.0",
    schema_version="1.0.0",
    metadata=CatalogMetadata(...),
    errors={"error_id": ErrorDefinition(...)}
)
```

#### ErrorDefinition

Single error pattern with matching and chaining configuration.

```python
from src.domain.models import ErrorDefinition, PatternMatcher

error_def = ErrorDefinition(
    id="oom_killer",
    pattern=PatternMatcher(type="literal", pattern="oom-kill"),
    files=["/var/log/**/*.log"],
    meaning="Process killed by OOM",
    suggestion="Increase memory",
    context_lines=3,
    next_errors=[],
    metadata={"severity": "critical"}
)
```

#### ErrorMatch

Detected error instance with context.

```python
from src.domain.models import ErrorMatch

match = ErrorMatch(
    error_id="oom_killer",
    file_uri="/var/log/system.log",
    line_number=42,
    matched_text="Out of memory - oom-kill event",
    context_before=["line 1", "line 2"],
    context_after=["line 3", "line 4"],
    meaning="Process killed by OOM",
    suggestion="Increase memory",
    metadata={"severity": "critical"}
)
```

#### PatternMatcher

Pattern matching configuration.

```python
from src.domain.models import PatternMatcher

# Literal pattern
literal = PatternMatcher(type="literal", pattern="ERROR")

# Regex pattern with flags
regex = PatternMatcher(
    type="regex",
    pattern=r"ERROR|CRITICAL",
    flags=["IGNORECASE"]
)

# Callable pattern
callable = PatternMatcher(
    type="callable",
    pattern="my_module:my_function"
)
```

#### ConditionSpec

Railway pattern condition specification.

```python
from src.domain.models import ConditionSpec

# Always condition
always = ConditionSpec(type="always")

# Field equals condition
field_eq = ConditionSpec(
    type="field_equals",
    field="metadata.severity",
    value="critical"
)

# Complex AND/OR condition
complex = ConditionSpec(
    type="and",
    conditions=[
        ConditionSpec(type="field_equals", field="severity", value="high"),
        ConditionSpec(
            type="or",
            conditions=[
                ConditionSpec(type="field_contains", field="text", value="urgent"),
                ConditionSpec(type="field_contains", field="text", value="critical")
            ]
        )
    ]
)
```

## Catalog I/O

```{eval-rst}
.. automodule:: src.domain.catalog_io
   :members:
   :undoc-members:
   :show-inheritance:
```

### Usage Examples

#### Loading Catalogs

```python
from src.domain.catalog_io import load_catalog

# Load from YAML file
catalog = load_catalog("path/to/catalog.yaml")

print(f"Loaded catalog: {catalog.metadata.name}")
print(f"Error definitions: {len(catalog.errors)}")
```

#### Saving Catalogs

```python
from src.domain.catalog_io import save_catalog
from src.domain.models import ErrorCatalog, CatalogMetadata

# Create catalog
catalog = ErrorCatalog(
    version="1.0.0",
    schema_version="1.0.0",
    metadata=CatalogMetadata(
        name="My Catalog",
        description="Test catalog",
        author="Me",
        created="2024-01-01T00:00:00Z",
        updated="2024-01-01T00:00:00Z"
    ),
    errors={}
)

# Save to file
save_catalog(catalog, "output_catalog.yaml")
```

## Catalog Validation

```{eval-rst}
.. automodule:: src.domain.catalog_validation
   :members:
   :undoc-members:
   :show-inheritance:
```

### Validation Examples

```python
from src.domain.catalog_validation import validate_catalog
from src.domain.catalog_io import load_catalog

catalog = load_catalog("catalog.yaml")

# Validate structure and business rules
is_valid, errors = validate_catalog(catalog)

if is_valid:
    print("✓ Catalog is valid")
else:
    print("✗ Validation errors:")
    for error in errors:
        print(f"  - {error}")
```

## Model Validation

Pydantic automatically validates all models:

```python
from pydantic import ValidationError
from src.domain.models import ErrorDefinition

try:
    # This will raise ValidationError
    error = ErrorDefinition(
        id="",  # Invalid: empty ID
        pattern={"type": "invalid"},  # Invalid: unknown type
        files=[],  # Invalid: no files
        meaning="",
        suggestion="",
        context_lines=-1,  # Invalid: negative
        next_errors=[],
        metadata={}
    )
except ValidationError as e:
    print("Validation errors:")
    for error in e.errors():
        print(f"  - {error['loc']}: {error['msg']}")
```

## JSON Schema Export

Export Pydantic models as JSON Schema:

```python
from src.domain.models import ErrorCatalog

# Get JSON schema
schema = ErrorCatalog.model_json_schema()

# Save to file
import json
with open("catalog_schema.json", "w") as f:
    json.dump(schema, f, indent=2)
```

## See Also

- [Catalog Schema Reference](../reference/catalog-schema.md)
- [Pattern Matching Guide](../how-to/pattern-matching.md)
- [Pydantic Documentation](https://docs.pydantic.dev/latest/)
