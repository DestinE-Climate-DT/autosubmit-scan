# User Guide

Complete guide to using autosubmit-scan for error monitoring and analysis.

**For unfamiliar terms, see the [Glossary](GLOSSARY.md).**

## Table of Contents

1. [Installation](#installation)
2. [Error Catalog Syntax](#catalog-syntax)
3. [Pattern Matching Types](#pattern-matchers)
4. [Condition Types (When to Check Next Error)](#condition-types)
5. [Railway Pattern (Automatic Error Chains)](#railway-pattern)
6. [CLI Commands](#cli-commands)
7. [Template Customization](#template-customization)
8. [Remote File Access](#remote-file-access)
9. [SSH Connection Reuse (Critical for Remote Scans)](#6-ssh-connection-pooling)

## Installation

### With Pixi

```bash
git clone https://github.com/DestinE-Climate-DT/autosubmit-scan.git
cd autosubmit-scan
pixi install
pixi run autosubmit-scan --help
```

### With pip

```bash
pip install -e .
autosubmit-scan --help
```

## Catalog Syntax

An [error catalog](GLOSSARY.md#catalog) is a [YAML](GLOSSARY.md#yaml) configuration file that tells the tool what errors to look for and how to handle them.

### Basic Structure

```yaml
version: "1.0.0"
schema_version: "1.0.0"

metadata:
  name: "Catalog Name"
  description: "What this catalog monitors"
  author: "Your Name"
  created: "2024-01-01T00:00:00+00:00"
  updated: "2024-01-01T00:00:00+00:00"

errors:
  error_id:
    id: "error_id"              # Unique identifier
    pattern: {...}              # Pattern configuration
    files: []                   # File patterns to scan
    meaning: "What this means"  # Human-readable explanation
    suggestion: "How to fix"    # Remediation advice
    context_lines: 5            # Lines of context to capture
    next_errors: []             # Railway pattern chains
    metadata: {}                # Custom metadata
```

### Field Descriptions

- **version**: Catalog format version (currently 1.0.0)
- **schema_version**: Schema version for validation
- **metadata**: Catalog-level metadata
  - **name**: Human-readable catalog name
  - **description**: Purpose of this catalog
  - **author**: Who created it
  - **created**: ISO 8601 timestamp
  - **updated**: ISO 8601 timestamp
- **errors**: Dictionary of error definitions
  - **id**: Must match the key in the errors dict
  - **pattern**: Pattern matching configuration
  - **files**: List of file patterns ([glob patterns](GLOSSARY.md#glob-patterns), [URI](GLOSSARY.md#uri) schemes supported)
  - **meaning**: What does this error signify?
  - **suggestion**: How should users respond?
  - **context_lines**: How many [lines before/after](GLOSSARY.md#context-lines) to capture
  - **next_errors**: [Railway pattern](GLOSSARY.md#railway-pattern) [conditional chains](GLOSSARY.md#condition)
  - **metadata**: Custom fields (severity, tags, etc.)

## Pattern Matchers

[Pattern matching](GLOSSARY.md#pattern-matching) is how the tool searches for errors in your [log files](GLOSSARY.md#log-file). See the [glossary](GLOSSARY.md#pattern-matching) for choosing which type to use.

### 1. Literal Pattern

[Exact text matching](GLOSSARY.md#literal-pattern). Use when you know the exact error text and it doesn't vary.

```yaml
pattern:
  type: "literal"
  pattern: "OOM killed"
```

### 2. Regex Pattern

[Flexible pattern matching](GLOSSARY.md#regex-pattern) using [regular expressions](GLOSSARY.md#regex). Use when error text varies slightly.

```yaml
pattern:
  type: "regex"
  pattern: "ERROR:\\s+(\\w+)\\s+failed"
  flags:
    - "IGNORECASE"
    - "MULTILINE"
```

**Available flags:**
- `IGNORECASE`: Case-insensitive matching
- `MULTILINE`: ^ and $ match line boundaries
- `DOTALL`: . matches newlines
- `VERBOSE`: Allow comments in regex

### 3. Callable Pattern

[Custom Python function](GLOSSARY.md#callable-pattern) for complex matching logic. Use when you need logic beyond text patterns.

```yaml
pattern:
  type: "callable"
  pattern: "my_module.matchers:check_memory_threshold"
```

Function signature:
```python
def check_memory_threshold(line: str) -> bool:
    """Return True if line matches pattern."""
    # Custom logic here
    return result
```

## Condition Types

[Conditions](GLOSSARY.md#condition) determine when to check for the next error in a [railway pattern](GLOSSARY.md#railway-pattern) chain. In plain English: "When to check the next error."

### 1. Always Condition

Always execute the next error:

```yaml
when:
  type: "always"
```

### 2. Field Equals

Check if a field equals a value:

```yaml
when:
  type: "field_equals"
  field: "metadata.severity"
  operator: "=="
  value: "critical"
```

**Operators:** `==`, `!=`, `>`, `<`, `>=`, `<=`

### 3. Field Contains

Check if a field contains a substring:

```yaml
when:
  type: "field_contains"
  field: "matched_text"
  operator: "contains"
  value: "timeout"
```

**Operators:** `contains`, `not_contains`, `startswith`, `endswith`

### 4. Field Regex

Match field against regex:

```yaml
when:
  type: "field_regex"
  field: "matched_text"
  operator: "regex"
  value: "\\d{3,4}"
```

### 5. Custom Condition

Use custom Python function:

```yaml
when:
  type: "custom"
  callable: "my_module.conditions:is_critical"
```

Function signature:
```python
from src.domain.models import ErrorMatch, ErrorDefinition, ErrorCatalog

def is_critical(
    match: ErrorMatch,
    error_def: ErrorDefinition,
    catalog: ErrorCatalog
) -> bool:
    """Return True if condition is met."""
    return match.metadata.get("severity") == "critical"
```

### 6. Logical Operators

Combine conditions with AND/OR:

```yaml
when:
  type: "and"
  conditions:
    - type: "field_equals"
      field: "severity"
      value: "high"
    - type: "or"
      conditions:
        - type: "field_contains"
          field: "matched_text"
          value: "urgent"
        - type: "field_contains"
          field: "matched_text"
          value: "critical"
```

## Railway Pattern

The [Railway Pattern](GLOSSARY.md#railway-pattern) is an automatic error flowchart system. When the tool finds one error, it can automatically check for related errors based on [conditions](GLOSSARY.md#condition) you define.

**Analogy:** Like a medical diagnosis flowchart:
1. Find symptom: "Fever" → Check temperature
2. If temperature > 102°F → Check for infection
3. If bacterial infection → Prescribe antibiotics

**For log files:**
1. Find "Out of Memory" → Check which process failed
2. If Python process → Check for memory leak pattern
3. If leak found → Create ticket

**Without Railway Pattern:** You manually search for each error, one at a time.
**With Railway Pattern:** The tool follows your flowchart automatically, finding error chains in one scan.

### Simple Chain

```yaml
errors:
  step1:
    id: "step1"
    # ... pattern, files, etc ...
    next_errors:
      - error_id: "step2"
        when:
          type: "always"

  step2:
    id: "step2"
    # ... continues the chain ...
    next_errors: []
```

### Conditional Branching

```yaml
errors:
  main_error:
    id: "main_error"
    next_errors:
      - error_id: "path_a"
        when:
          type: "field_equals"
          field: "metadata.environment"
          value: "production"
      - error_id: "path_b"
        when:
          type: "field_equals"
          field: "metadata.environment"
          value: "staging"

  path_a:
    id: "path_a"
    # Production-specific checks
    next_errors: []

  path_b:
    id: "path_b"
    # Staging-specific checks
    next_errors: []
```

### Complex Conditions

```yaml
next_errors:
  - error_id: "escalate"
    when:
      type: "and"
      conditions:
        - type: "field_equals"
          field: "metadata.severity"
          value: "critical"
        - type: "or"
          conditions:
            - type: "custom"
              callable: "checks:is_weekend"
            - type: "custom"
              callable: "checks:is_night"
```

## CLI Commands

### Initialize Catalog

```bash
# Create sample catalog
autosubmit-scan init

# Specify output path
autosubmit-scan init --output my_catalog.yaml

# Overwrite existing
autosubmit-scan init --output my_catalog.yaml --force
```

### Validate Catalog

```bash
# Basic validation
autosubmit-scan validate my_catalog.yaml

# With JSON schema
autosubmit-scan validate my_catalog.yaml --schema schema.json
```

### Run Scan

```bash
# Basic scan
autosubmit-scan scan --catalog my_catalog.yaml

# Specify output directory
autosubmit-scan scan --catalog my_catalog.yaml --output ./results

# Use multiple cores
autosubmit-scan scan --catalog my_catalog.yaml --cores 8

# Dry run (show plan)
autosubmit-scan scan --catalog my_catalog.yaml --dryrun

# Force re-execution
autosubmit-scan scan --catalog my_catalog.yaml --force
```

### View Results

```bash
# Launch interactive results viewer
autosubmit-scan view ./results/report.json
```

**[Interactive Results Viewer](GLOSSARY.md#interactive-results-viewer) Navigation:**
- Arrow keys: Navigate tree
- Enter: Expand/collapse
- q: Quit

### Export Report

```bash
# Export to Markdown (default)
autosubmit-scan export ./results/report.json

# Specify format
autosubmit-scan export ./results/report.json --template html

# Specify output file
autosubmit-scan export ./results/report.json --template markdown --output report.md
```

## Template Customization

Templates are Jinja2 files in `src/reporting/templates/`.

### Available Templates

- `report.md.j2`: Markdown format
- `report.html.j2`: HTML format
- `summary.txt.j2`: Plain text summary

### Template Data Structure

```python
{
    "report": {
        # Full scan report (JSON-LD format)
    },
    "summary": {
        "totalMatches": int,
        "errorTypes": int,
        "filesScanned": int,
        "hostsScanned": [...]
    },
    "matches": [
        {
            "error_id": str,
            "file_uri": str,
            "line_number": int,
            "matched_text": str,
            "meaning": str,
            "suggestion": str,
            # ...
        }
    ],
    "matches_by_error": {
        "error_id": [matches...]
    },
    "metadata": {
        "generated_at": str,
        "report_date": str,
        "author": str
    }
}
```

### Creating Custom Templates

1. Create template file in `src/reporting/templates/`:

```jinja2
# my_template.j2
# Custom Report
Generated: {{ metadata.generated_at }}

## Summary
- Total Matches: {{ summary.totalMatches }}
- Error Types: {{ summary.errorTypes }}

{% for error_id, matches in matches_by_error.items() %}
## {{ error_id }} ({{ matches|length }} matches)

{% for match in matches %}
- Line {{ match.line_number }}: {{ match.matched_text }}
{% endfor %}
{% endfor %}
```

2. Render with TemplateRenderer:

```python
from src.reporting.templates import TemplateRenderer

renderer = TemplateRenderer()
renderer.render("my_template.j2", data, "output.txt")
```

## Remote File Access

The tool can scan files on different systems using [remote file access](GLOSSARY.md#remote-file-access). It uses [fsspec](GLOSSARY.md#fsspec) (a file access library) behind the scenes - you don't need to configure it directly.

### Local Files

```yaml
files:
  - "/var/log/**/*.log"
  - "file:///var/log/system/messages"
```

### S3 Buckets

```yaml
files:
  - "s3://my-bucket/logs/**/*.log"
  - "s3://my-bucket/slurm/*.out"
```

**Requirements:**
- AWS credentials configured
- boto3 and s3fs installed (via pixi)

### SFTP

```yaml
files:
  - "sftp://user@host.example.com/var/log/**/*.log"
```

**Requirements:**
- SSH credentials/keys configured
- paramiko and sshfs installed (via pixi)

### FTP

```yaml
files:
  - "ftp://user:password@ftp.example.com/logs/**/*.log"
```

**Requirements:**
- FTP credentials in URI or .netrc
- fsspec installed (via pixi)

### Authentication

**S3:** Use AWS CLI configuration or environment variables:
```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

**SFTP:** Use SSH keys or password in URI:
```yaml
files:
  - "sftp://user:password@host/path/**/*.log"  # Not recommended
  - "sftp://user@host/path/**/*.log"           # Uses SSH keys
```

**FTP:** Use .netrc file or password in URI:
```yaml
files:
  - "ftp://user:pass@host/path/**/*.log"
```

## Best Practices

### 1. Catalog Organization

- One catalog per system/application
- Group related errors together
- Use descriptive error IDs
- Document meaning and suggestions clearly

### 2. Pattern Design

- Start simple (literal), add complexity as needed
- Test regex patterns before deployment
- Use callable patterns for complex logic
- Consider performance for large files

### 3. Railway Pattern

- Keep chains shallow (2-3 levels)
- Avoid circular dependencies
- Use meaningful condition logic
- Document chain flow in metadata

### 4. File Patterns

- Use specific globs to reduce scanning
- Group files by error type
- Consider network latency for remote files
- Use appropriate protocols (SFTP faster than FTP)

### 5. Performance

- Use multiple cores (`--cores 8`)
- Smart caching (automatic - only re-scans changed files)
- Limit [context_lines](GLOSSARY.md#context-lines) for large files

### 6. SSH Connection Reuse

**Critical for remote scans!** When scanning files over SSH/SFTP, you MUST configure [SSH connection reuse](GLOSSARY.md#ssh-connection-reuse) to avoid connection timeouts.

**Problem:** Without connection reuse:
- The tool creates new SSH connections for each file operation
- Typical scan = 44+ connections (11 errors × 4 operations)
- Connection timeouts after 2 minutes
- Slow performance due to repeated SSH handshakes

**Solution:** SSH connection reuse (ControlMaster) shares connections across all processes:
- Reduces 44+ connections to 1-2 per host
- Makes scans 10-40x faster
- Prevents timeouts
- Works transparently with parallel execution

**Analogy:** Like carpooling vs everyone driving separately - connection reuse is more efficient and faster.

**Quick Setup:**

1. Check your current configuration:
   ```bash
   as-scan check-ssh [hostname]
   ```

2. If needed, add to `~/.ssh/config`:
   ```ssh-config
   Host *
       ControlMaster auto
       ControlPath ~/.ssh/control-%C
       ControlPersist 10m
   ```

3. Verify it works:
   ```bash
   as-scan check-ssh [hostname]
   ```

**See detailed guide:** [docs/SSH_CONNECTION_POOLING.md](SSH_CONNECTION_POOLING.md)
- Use dry run to test patterns first

## Troubleshooting

### Validation Errors

```bash
# Check YAML syntax
autosubmit-scan validate my_catalog.yaml

# Check detailed errors
autosubmit-scan validate my_catalog.yaml --verbose
```

### No Matches Found

- Verify file patterns are correct
- Check pattern syntax (test regex separately)
- Ensure files are accessible
- Review logs for file discovery

### Remote Access Issues

**S3:**
- Check AWS credentials
- Verify bucket permissions
- Test with AWS CLI first

**SFTP:**
- Verify SSH keys are configured
- Test connection with sftp command
- Check firewall rules

### Performance Issues

- Reduce file count with specific patterns
- Increase cores for parallel processing
- Use local cache for remote files
- Profile with `--dryrun` first

## Examples

See [examples/sample_catalog.yaml](../examples/sample_catalog.yaml) for comprehensive examples covering all features.
