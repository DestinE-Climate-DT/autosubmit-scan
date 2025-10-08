# `as-scan`: The Autosubmit Error Scanner 

A comprehensive remote error monitoring and scanning system for analyzing log files across distributed systems. Built with pattern matching, workflow orchestration (Snakemake), and the Railway pattern for conditional error chaining.

## Features

- **Pattern Matching**: Support for literal, regex, and callable patterns
- **Remote File Access**: Scan files via S3, SFTP, FTP, and local filesystems
- **Railway Pattern**: Conditional error chaining based on match context
- **Workflow Orchestration**: Powered by Snakemake for scalable, parallel execution

## Bonus Features (WIP and not critical)

- **Interactive TUI**: Browse results with a terminal user interface (Textual)
- **Report Generation**: Export to Markdown, HTML, or plain text
- **JSON-LD Format**: Structured, semantic error reports

## Installation

### Using Pixi (Recommended)

```bash
# Clone the repository
git clone https://github.com/DestinE-Climate-DT/autosubmit-scan.git
cd autosubmit-scan

# Install dependencies with pixi
pixi install

# Run commands via pixi
pixi run as-scan --help
```

### Using pip

```bash
pip install -e .
as-scan --help
```

## Quick Start

### 1. Create a Sample Catalog

```bash
as-scan init --output my_catalog.yaml
```

This creates a sample catalog with example error definitions.

### 2. Validate Your Catalog

```bash
as-scan validate my_catalog.yaml
```

Ensures your catalog is syntactically correct and follows the schema.

### 3. Run a Scan

```bash
as-scan scan --catalog my_catalog.yaml --output ./results --cores 4
```

This will:
- Discover files matching your patterns
- Scan for errors in parallel
- Apply railway pattern conditions
- Generate a JSON-LD report

### 4. View Results Interactively

```bash
as-scan view ./results/report.json
```

Launches a TUI for browsing errors by type and file.

### 5. Export to Markdown

```bash
as-scan export ./results/report.json --template markdown --output report.md
```

## Command Reference

### `scan` - Run error scanning workflow

```bash
as-scan scan --catalog CATALOG --output OUTPUT [OPTIONS]

Options:
  --catalog PATH    Error catalog YAML file [required]
  --output DIR      Output directory [default: ./output]
  --cores INT       Number of CPU cores [default: 4]
  --dryrun          Show workflow plan without execution
  --force           Force re-execution of all rules
```

### `view` - Launch interactive TUI

```bash
as-scan view REPORT_PATH

Arguments:
  REPORT_PATH       Path to JSON-LD report file
```

### `export` - Export report with template

```bash
as-scan export REPORT_PATH [OPTIONS]

Arguments:
  REPORT_PATH       Path to JSON-LD report file

Options:
  --template TEXT   Template format: markdown, html, text [default: markdown]
  --output PATH     Output file path
```

### `validate` - Validate error catalog

```bash
as-scan validate CATALOG_PATH [OPTIONS]

Arguments:
  CATALOG_PATH      Path to catalog YAML file

Options:
  --schema PATH     Optional JSON schema file for validation
```

### `init` - Create sample catalog

```bash
as-scan init [OPTIONS]

Options:
  --output PATH     Output path [default: ./error_catalog.yaml]
  --force           Overwrite existing file
```

## Error Catalog Format

An error catalog defines patterns to search for and how to handle them:

```yaml
version: "1.0.0"
schema_version: "1.0.0"

metadata:
  name: "My Error Catalog"
  description: "Catalog for monitoring system errors"
  author: "Your Name"
  created: "2024-01-01T00:00:00+00:00"
  updated: "2024-01-01T00:00:00+00:00"

errors:
  out_of_memory:
    id: "out_of_memory"
    pattern:
      type: "literal"
      pattern: "OOM killed"
    files:
      - "s3://logs/slurm/**/*.out"
      - "/var/log/jobs/**/*.err"
    meaning: "Job was killed due to out-of-memory"
    suggestion: "Increase memory allocation in job script"
    context_lines: 10
    next_errors:
      - error_id: "memory_check"
        when:
          type: "always"
    metadata:
      severity: "high"
```

### Pattern Types

- **literal**: Exact string matching
- **regex**: Regular expression with optional flags
- **callable**: Custom Python function

### File URIs

Supported URI schemes:
- `file:///path/to/file` or `/path/to/file` - Local filesystem
- `s3://bucket/path/**/*.log` - Amazon S3
- `sftp://user@host/path/**/*.log` - SFTP
- `ftp://user:pass@host/path/**/*.log` - FTP

### Railway Pattern

Chain errors conditionally using the `next_errors` field:

```yaml
next_errors:
  - error_id: "follow_up_error"
    when:
      type: "and"
      conditions:
        - type: "field_equals"
          field: "severity"
          value: "critical"
        - type: "field_contains"
          field: "matched_text"
          value: "urgent"
```

## Architecture

The system follows a modular architecture:

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Interface                        │
│  (scan, view, export, validate, init)                   │
└────────────┬────────────────────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
┌─────▼─────┐  ┌───▼──────┐
│  Domain   │  │ Matching │
│  Models   │  │ Engine   │
└─────┬─────┘  └───┬──────┘
      │            │
      │     ┌──────▼──────┐
      │     │ Snakemake   │
      │     │ Workflow    │
      │     └──────┬──────┘
      │            │
┌─────▼────────────▼─────┐
│   Railway Pattern      │
│   Executor             │
└─────┬──────────────────┘
      │
┌─────▼──────────────────┐
│  Report Generation     │
│  (JSON-LD, TUI, etc)   │
└────────────────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architectural views.

## Testing

```bash
# Run all tests
pixi run test

# Run only unit tests
pixi run test-unit

# Run integration tests (requires remote services)
pixi run test-integration

# Run E2E tests
pixi run test-e2e

# Generate coverage report
pixi run coverage-report
```

## Examples

### Basic Local File Scanning

```bash
# Create catalog for local logs
cat > local_errors.yaml << EOF
version: "1.0.0"
schema_version: "1.0.0"
metadata:
  name: "Local Errors"
  description: "Scan local log files"
  author: "Me"
  created: "2024-01-01T00:00:00Z"
  updated: "2024-01-01T00:00:00Z"

errors:
  error_keyword:
    id: "error_keyword"
    pattern:
      type: "regex"
      pattern: "ERROR|CRITICAL|FATAL"
      flags: ["IGNORECASE"]
    files:
      - "/var/log/**/*.log"
    meaning: "Critical error detected"
    suggestion: "Review logs for details"
    context_lines: 5
    next_errors: []
    metadata:
      severity: "high"
EOF

# Scan
as-scan scan --catalog local_errors.yaml --output ./results

# View
as-scan view ./results/report.json
```

### S3 Bucket Scanning

```bash
# Scan S3 logs (requires AWS credentials)
as-scan scan \
  --catalog s3_catalog.yaml \
  --output ./s3_results \
  --cores 8
```

### Railway Pattern Example

See [examples/sample_catalog.yaml](examples/sample_catalog.yaml) for comprehensive railway pattern examples.

## Documentation

- [User Guide](docs/USER_GUIDE.md) - Detailed usage instructions
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Quick Start](QUICK_START.md) - Get started quickly

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass: `pixi run test`
5. Submit a pull request

## License

See [LICENSE](LICENSE) for details.

## Authors

- Paul Gierz <pgierz@awi.de> (ORCID: 0000-0002-4512-087X)

## Acknowledgments

This project is part of the DestinE Climate Digital Twin initiative.
