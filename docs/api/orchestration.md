# Orchestration Module

Workflow coordination using Snakemake and railway pattern execution.

## Overview

The orchestration module manages:
- **Scanner**: Main scan execution orchestration
- **Railway**: Conditional error chaining (Railway pattern)
- **Condition Evaluator**: Evaluate chaining conditions
- **Snakefile**: Workflow definition and checkpoints

## Module Structure

```
src/orchestration/
├── __init__.py
├── scanner.py              # Main scan orchestration
├── railway.py              # Railway pattern execution
├── condition_evaluator.py  # Condition evaluation logic
└── Snakefile               # Snakemake workflow definition
```

## Scanner

```{eval-rst}
.. automodule:: src.orchestration.scanner
   :members:
   :undoc-members:
   :show-inheritance:
```

## Railway Pattern

```{eval-rst}
.. automodule:: src.orchestration.railway
   :members:
   :undoc-members:
   :show-inheritance:
```

## Condition Evaluator

```{eval-rst}
.. automodule:: src.orchestration.condition_evaluator
   :members:
   :undoc-members:
   :show-inheritance:
```

## Snakemake Workflow

The Snakefile defines the workflow stages:

1. **discover_files** checkpoint - Expand glob patterns to file lists
2. **fingerprint_file** checkpoint - Cache file metadata
3. **match_pattern** rule - Find match line numbers
4. **filter_matches** checkpoint - Keep only files with matches
5. **extract_context** rule - Build ErrorMatch objects
6. **evaluate_railway** checkpoint - Determine next errors
7. **aggregate_results** rule - Combine all results

### Workflow Visualization

```bash
# Generate workflow DAG
as-scan dag --catalog catalog.yaml --output workflow.svg
```

## See Also

- [Railway Pattern Tutorial](../tutorials/04_railway_pattern.ipynb)
- [Workflow Engine Explanation](../explanation/workflow-engine.md)
- [Snakemake Documentation](https://snakemake.readthedocs.io/)
