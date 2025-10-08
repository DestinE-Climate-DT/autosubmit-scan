# Architecture Documentation

System architecture for autosubmit-scan following the 4+1 architectural views model.

## Table of Contents

1. [Logical View](#logical-view)
2. [Process View](#process-view)
3. [Development View](#development-view)
4. [Physical View](#physical-view)
5. [Scenarios View](#scenarios-view)

## Logical View

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Interface                           │
│  Entry point for all user interactions                      │
│  Commands: scan, view, export, validate, init               │
└────────────┬────────────────────────────────────────────────┘
             │
      ┌──────┴──────────────┐
      │                     │
┌─────▼────────┐     ┌─────▼────────┐
│   Domain     │     │   Matching   │
│   Layer      │     │   Engine     │
│              │     │              │
│ - Models     │     │ - Pattern    │
│ - Catalog    │     │   Matchers   │
│ - Validation │     │ - Stream     │
│              │     │   Reader     │
└──────┬───────┘     └─────┬────────┘
       │                   │
       │     ┌─────────────▼──────────┐
       │     │   Orchestration        │
       │     │   (Snakemake)          │
       │     │                        │
       │     │ - Workflow Rules       │
       │     │ - Checkpoints          │
       │     │ - File Discovery       │
       │     └────────┬───────────────┘
       │              │
┌──────▼──────────────▼──────┐
│   Railway Pattern          │
│   Executor                 │
│                            │
│ - Condition Evaluator      │
│ - Error Chaining           │
└──────┬─────────────────────┘
       │
┌──────▼─────────────────────┐
│   Reporting Layer          │
│                            │
│ - JSON-LD Generator        │
│ - Template Renderer        │
│ - TUI Application          │
└────────────────────────────┘
```

### Core Components

#### 1. Domain Layer (`src/domain/`)

**Purpose:** Define core business entities and rules.

**Components:**
- `models.py`: Pydantic models for ErrorCatalog, ErrorMatch, etc.
- `catalog.py`: I/O operations for catalogs (load, save, JSON-LD conversion)
- `validation.py`: Validation logic for catalogs

**Key Classes:**
- `ErrorCatalog`: Container for error definitions
- `ErrorDefinition`: Single error pattern with metadata
- `ErrorMatch`: Detected error instance with context
- `PatternConfig`: Pattern matching configuration

#### 2. Matching Engine (`src/matching/`)

**Purpose:** Pattern matching and text processing.

**Components:**
- `pattern_matcher.py`: Pattern matching implementations (literal, regex, callable)
- `stream_reader.py`: Memory-efficient file reading
- `context_extractor.py`: Extract context around matches
- `match_builder.py`: Build ErrorMatch objects

**Key Classes:**
- `PatternMatcher`: Abstract base for pattern matchers
- `LiteralMatcher`: Exact string matching
- `RegexMatcher`: Regular expression matching
- `CallableMatcher`: Custom function matching

#### 3. Orchestration Layer (`src/orchestration/`)

**Purpose:** Workflow coordination and execution.

**Components:**
- `Snakefile`: Snakemake workflow definition
- `helpers.py`: Utility functions for workflow
- `scanners.py`: File scanning logic
- `conditions.py`: Condition evaluation
- `railway.py`: Railway pattern execution

**Key Features:**
- Checkpoint-based execution
- Parallel file processing
- Atomic rule execution
- Result aggregation

#### 4. Railway Pattern (`src/orchestration/railway.py`)

**Purpose:** Conditional error chaining.

**Components:**
- `RailwayExecutor`: Evaluates conditions and determines next errors
- Condition evaluators: `FieldEquals`, `FieldContains`, `Custom`, etc.
- Logical operators: `AndCondition`, `OrCondition`

**Key Concepts:**
- Conditional branching based on match context
- Support for complex nested conditions
- Custom Python functions for advanced logic

#### 5. Reporting Layer (`src/reporting/`)

**Purpose:** Generate and visualize results.

**Components:**
- `jsonld.py`: JSON-LD report generation
- `templates.py`: Jinja2 template rendering
- `tui.py`: Textual terminal UI
- `aggregator.py`: Result aggregation utilities

**Key Classes:**
- `ReportGenerator`: Creates JSON-LD reports
- `TemplateRenderer`: Renders Jinja2 templates
- `ErrorReportApp`: Textual TUI application

#### 6. CLI Interface (`src/cli/`)

**Purpose:** User interaction layer.

**Components:**
- `main.py`: CLI entry point and group
- `commands/scan.py`: Scan workflow execution
- `commands/view.py`: TUI launcher
- `commands/export.py`: Report export
- `commands/validate.py`: Catalog validation
- `commands/init.py`: Catalog initialization

## Process View

### Scan Workflow

```
1. User Command
   │
   ├─> Load Catalog
   │   └─> Validate Schema
   │
   ├─> Generate Workflow Config
   │
   ├─> Execute Snakemake
   │   │
   │   ├─> [Checkpoint] Discover Files
   │   │   └─> Expand glob patterns
   │   │
   │   ├─> [Checkpoint] Fingerprint Files
   │   │   └─> Hash and cache metadata
   │   │
   │   ├─> [Rule] Match Patterns
   │   │   └─> Scan files for patterns
   │   │
   │   ├─> [Checkpoint] Filter Matches
   │   │   └─> Keep only files with matches
   │   │
   │   ├─> [Rule] Extract Context
   │   │   └─> Build ErrorMatch objects
   │   │
   │   ├─> [Checkpoint] Evaluate Railway
   │   │   └─> Determine next errors
   │   │
   │   ├─> [Rule] Scan Chained Errors
   │   │   └─> Execute railway pattern
   │   │
   │   └─> [Rule] Aggregate Results
   │       └─> Combine all matches
   │
   └─> Generate JSON-LD Report
       └─> Display Summary
```

### Data Flow

```
Input Catalog (YAML)
        │
        ├─> Parse & Validate
        │
        ▼
   ErrorCatalog Objects
        │
        ├─> Pattern Matching
        │   └─> For each error definition:
        │       ├─> Discover files
        │       ├─> Scan patterns
        │       └─> Extract matches
        │
        ▼
   ErrorMatch Objects
        │
        ├─> Railway Evaluation
        │   └─> For each match:
        │       ├─> Evaluate conditions
        │       ├─> Chain to next errors
        │       └─> Recurse
        │
        ▼
   Complete Match Set
        │
        ├─> Report Generation
        │   ├─> JSON-LD format
        │   ├─> Summary statistics
        │   └─> Schema.org vocabulary
        │
        ▼
   Output Report (JSON)
        │
        ├─> View (TUI)
        │   └─> Interactive browsing
        │
        └─> Export (Templates)
            ├─> Markdown
            ├─> HTML
            └─> Text
```

## Development View

### Directory Structure

```
autosubmit-scan/
├── src/
│   ├── domain/              # Core domain models
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── catalog.py
│   │   └── validation.py
│   ├── matching/            # Pattern matching
│   │   ├── __init__.py
│   │   ├── pattern_matcher.py
│   │   ├── stream_reader.py
│   │   ├── context_extractor.py
│   │   ├── match_builder.py
│   │   └── callable_loader.py
│   ├── orchestration/       # Workflow orchestration
│   │   ├── __init__.py
│   │   ├── Snakefile
│   │   ├── helpers.py
│   │   ├── scanners.py
│   │   ├── conditions.py
│   │   └── railway.py
│   ├── reporting/           # Report generation
│   │   ├── __init__.py
│   │   ├── jsonld.py
│   │   ├── templates.py
│   │   ├── tui.py
│   │   ├── aggregator.py
│   │   └── templates/
│   │       ├── report.md.j2
│   │       ├── report.html.j2
│   │       └── summary.txt.j2
│   └── cli/                 # Command-line interface
│       ├── __init__.py
│       ├── main.py
│       └── commands/
│           ├── __init__.py
│           ├── scan.py
│           ├── view.py
│           ├── export.py
│           ├── validate.py
│           └── init.py
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
├── examples/                # Example catalogs
├── docs/                    # Documentation
├── config/                  # Configuration files
├── schemas/                 # JSON schemas
└── scripts/                 # Utility scripts
```

### Module Dependencies

```
cli → domain, reporting, orchestration
    │
    ├─> domain (models, catalog)
    ├─> reporting (jsonld, templates, tui)
    └─> orchestration (via Snakemake subprocess)

orchestration → domain, matching, railway
    │
    ├─> domain (models, catalog)
    ├─> matching (pattern_matcher, scanners)
    └─> railway (conditions, executor)

reporting → domain
    │
    └─> domain (models, catalog)

matching → domain
    │
    └─> domain (models)

railway → domain, orchestration
    │
    ├─> domain (models, catalog)
    └─> orchestration (conditions)
```

### Extension Points

#### 1. Custom Pattern Matchers

Implement `PatternMatcher` interface:

```python
from src.matching.pattern_matcher import PatternMatcher

class MyCustomMatcher(PatternMatcher):
    def match(self, text: str) -> bool:
        # Custom matching logic
        return result
```

Register in catalog:
```yaml
pattern:
  type: "callable"
  pattern: "my_module:MyCustomMatcher"
```

#### 2. Custom Conditions

Implement condition function:

```python
from src.domain.models import ErrorMatch, ErrorDefinition, ErrorCatalog

def my_condition(
    match: ErrorMatch,
    error_def: ErrorDefinition,
    catalog: ErrorCatalog
) -> bool:
    # Custom condition logic
    return result
```

Use in catalog:
```yaml
when:
  type: "custom"
  callable: "my_module:my_condition"
```

#### 3. Custom Templates

Create Jinja2 template in `src/reporting/templates/`:

```jinja2
# my_template.j2
{% for match in matches %}
{{ match.error_id }}: {{ match.matched_text }}
{% endfor %}
```

Render:
```python
renderer = TemplateRenderer()
renderer.render("my_template.j2", data, "output.txt")
```

## Physical View

### Deployment Model

```
┌─────────────────────────────────────────────────┐
│              User Workstation                    │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │   autosubmit-scan CLI                  │    │
│  │   (Python 3.12+, Pixi environment)     │    │
│  └────────────┬───────────────────────────┘    │
│               │                                  │
│               ├─> Local Filesystem               │
│               │   - Catalog files                │
│               │   - Output directory             │
│               │   - Temporary files              │
│               │                                  │
└───────────────┼──────────────────────────────────┘
                │
                ├──────────────────┐
                │                  │
    ┌───────────▼────────┐  ┌─────▼─────────┐
    │   Remote Storage   │  │  Remote Hosts │
    │                    │  │               │
    │ - S3 Buckets       │  │ - SFTP        │
    │ - FTP Servers      │  │ - SSH         │
    └────────────────────┘  └───────────────┘
```

### Runtime Dependencies

**Core:**
- Python >= 3.12
- Pydantic >= 2.0
- PyYAML >= 6.0
- Loguru >= 0.7

**CLI:**
- Click
- Click-Loguru

**Workflow:**
- Snakemake >= 9.12

**Remote Access:**
- boto3 (S3)
- s3fs (S3 filesystem)
- paramiko (SFTP)
- sshfs (SFTP filesystem)
- fsspec (General filesystem)

**Reporting:**
- Textual >= 1.0 (TUI)
- Jinja2 >= 3.1 (Templates)

**Testing:**
- pytest >= 8.0
- pytest-cov
- pytest-xdist

## Scenarios View

### Use Case 1: Basic Error Scanning

**Actor:** System Administrator

**Flow:**
1. Create catalog with error patterns
2. Validate catalog syntax
3. Run scan against log files
4. Review results in TUI
5. Export report to Markdown

**Components Involved:**
- CLI (init, validate, scan, view, export)
- Domain (catalog loading, validation)
- Orchestration (Snakemake workflow)
- Matching (pattern matching)
- Reporting (JSON-LD, TUI, templates)

### Use Case 2: Railway Pattern Monitoring

**Actor:** DevOps Engineer

**Flow:**
1. Define primary error (e.g., OOM killed)
2. Add conditional next_errors
3. Configure conditions (severity, context)
4. Run scan
5. Verify error chains are detected

**Components Involved:**
- Domain (ErrorDefinition with next_errors)
- Orchestration (Snakefile railway rules)
- Railway (condition evaluation)
- Reporting (chain visualization)

### Use Case 3: Remote File Scanning

**Actor:** Cloud Operations Team

**Flow:**
1. Configure S3/SFTP URIs in catalog
2. Set up credentials
3. Run scan with remote access
4. Monitor progress
5. Aggregate results

**Components Involved:**
- Domain (file pattern parsing)
- Orchestration (file discovery, fsspec)
- Matching (stream reading from remote)
- Reporting (summary with host information)

### Use Case 4: Custom Pattern Development

**Actor:** Developer

**Flow:**
1. Write custom pattern matcher
2. Register in catalog
3. Test with sample files
4. Deploy to production catalog
5. Monitor matches

**Components Involved:**
- Matching (callable loader, PatternMatcher)
- Domain (PatternConfig with callable type)
- Orchestration (integration into workflow)

### Use Case 5: Automated Monitoring

**Actor:** CI/CD Pipeline

**Flow:**
1. Clone repository
2. Install via pixi
3. Run scan command
4. Parse JSON-LD output
5. Trigger alerts if matches found

**Components Involved:**
- CLI (scan command with JSON output)
- Domain (catalog loading)
- Orchestration (automated execution)
- Reporting (JSON-LD for parsing)

## Design Patterns

### 1. Repository Pattern

`src/domain/catalog.py` implements repository pattern for catalog persistence:
- `load_catalog()`: Load from storage
- `save_catalog()`: Persist to storage
- `catalog_to_jsonld()`: Transform for export

### 2. Strategy Pattern

`src/matching/pattern_matcher.py` uses strategy pattern for different matching algorithms:
- `LiteralMatcher`
- `RegexMatcher`
- `CallableMatcher`

### 3. Builder Pattern

`src/matching/match_builder.py` uses builder for constructing ErrorMatch objects with context.

### 4. Template Method Pattern

`src/reporting/templates.py` uses template method via Jinja2 for flexible report generation.

### 5. Chain of Responsibility

Railway pattern in `src/orchestration/railway.py` implements chain of responsibility for error evaluation.

## Performance Considerations

### 1. Parallel Processing

- Snakemake orchestrates parallel file scanning
- Configure with `--cores N` for optimal throughput
- Files processed independently

### 2. Caching

- File fingerprints cached by Snakemake
- Avoid re-scanning unchanged files
- Checkpoints enable incremental execution

### 3. Streaming

- Stream reading for large files (see `stream_reader.py`)
- Memory-efficient line-by-line processing
- Configurable buffer sizes

### 4. Remote Access Optimization

- Use fsspec for efficient remote I/O
- Connection pooling for S3/SFTP
- Parallel downloads with Snakemake

## Security Considerations

### 1. Credentials

- Never embed credentials in catalogs
- Use environment variables or credential files
- Support SSH key authentication for SFTP

### 2. File Access

- Validate file paths to prevent path traversal
- Respect filesystem permissions
- Sanitize user inputs in patterns

### 3. Code Execution

- Callable patterns execute arbitrary code
- Review custom functions before deployment
- Consider sandboxing for untrusted catalogs

## Future Extensions

### Planned Features

1. **Web Dashboard**: Browser-based result viewing
2. **Real-time Monitoring**: Watch files for new errors
3. **Alert Integration**: Webhook/email notifications
4. **Plugin System**: Dynamic pattern/condition loading
5. **Distributed Execution**: Multi-node scanning

### Extension Architecture

All extensions should follow existing patterns:
- Use Pydantic for configuration
- Implement appropriate interfaces
- Add tests (unit, integration, e2e)
- Document in USER_GUIDE.md
