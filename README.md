# `as-scan`: The Autosubmit Error Scanner

<p align="center">
  <img src="assets/title-svg.svg" alt="DestinE Earth" width="400"/>
</p>

A comprehensive remote error monitoring and scanning system for analyzing log files across distributed systems. Built with pattern matching, workflow orchestration (Snakemake), and the Railway pattern for conditional error chaining.

---

## 🎬 Quick Demo

> **Coming Soon**: Interactive demos showcasing real-world error scanning workflows

### Featured Use Cases

<details>
<summary><b>📊 Scanning Remote HPC Cluster Logs via SSH</b></summary>

```bash
# Full-featured demo coming soon
# - Create error catalog for SLURM job failures
# - Scan remote logs with SSH aliases from ~/.ssh/config
# - Track out-of-memory errors, time limits, and node failures
# - Generate comprehensive reports with context
```

</details>

<details>
<summary><b>🔗 Railway Pattern: Chaining Related Errors</b></summary>

```bash
# Full-featured demo coming soon
# - Define conditional error chains
# - Automatically detect cascading failures
# - Track error propagation through logs
# - Generate causal dependency graphs
```

</details>

<details>
<summary><b>🌐 Multi-Cloud Log Aggregation</b></summary>

```bash
# Full-featured demo coming soon
# - Scan logs from S3, SSH, SFTP, and local sources
# - Parallel processing across distributed systems
# - Unified error reporting
# - Integration with monitoring dashboards
```

</details>

---

## Features

- **Pattern Matching**: Support for literal, regex, and callable patterns
- **Remote File Access**: Scan files via S3, SFTP, FTP, and local filesystems
- **Railway Pattern**: Conditional error chaining based on match context
- **Workflow Orchestration**: Powered by Snakemake for scalable, parallel execution

## Bonus Features (WIP and not critical)

- **Interactive TUI**: Browse results with a terminal user interface (Textual)
- **Report Generation**: Export to Markdown, HTML, or plain text via Jinja2 Templates
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

Supported URI schemes with **rsync-style notation** for SSH/SFTP:
- `/path/to/file` - Local filesystem
- `ssh://hostname:/path/**/*.log` - SSH (rsync-style with colon)
- `sftp://hostname:/path/**/*.log` - SFTP (rsync-style with colon)
- `s3://bucket/path/**/*.log` - Amazon S3
- `ftp://user:pass@host/path/**/*.log` - FTP

**SSH Config Support**: The tool automatically reads `~/.ssh/config` to resolve:
- Host aliases (e.g., `ssh://lumi:/path` resolves to actual hostname)
- Usernames, ports, and identity files
- All SSH configuration options

Example:
```yaml
files:
  - "ssh://lumi:/scratch/project_12345/logs/**/*.out"
  - "sftp://mn5:/gpfs/projects/myproject/**/*.err"
  - "/local/path/to/logs/**/*.log"
```

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

---

## Funding & Attribution

<p align="center">
  <img src="assets/DestinE_logo_line_2_POS.png" alt="DestinE - Funded by the European Union" width="600"/>
</p>

The `as-scan` software is proudly funded by the European Union 🇪🇺 and developed by:

<!-- AUTO-GENERATED: Run `python scripts/generate_author_badges.py` to update -->
<!-- Edit AUTHORS.yaml to add/modify authors -->

<div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin: 20px 0;">
<div align="center" style="display: inline-block; margin: 10px; padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 50%; width: 180px; height: 180px; position: relative;">
    <a href="mailto:paul.gierz@awi.de">
        <img src="https://secure.gravatar.com/avatar/709ea66dc102e6bc4547032f85ff6c95?s=100&d=identicon" alt="Dr. Paul Gierz" style="border-radius: 50%; width: 100px; height: 100px; border: 3px solid white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    </a>
    <h4 style="margin: 8px 0 3px 0; font-size: 0.95em;">Dr. Paul Gierz</h4>
    <p style="margin: 3px 0; font-size: 0.75em; color: #555;">Alfred Wegener Institute (AWI)</p>
    <p style="margin: 5px 0; font-size: 1.2em;">
        <a href="https://orcid.org/0000-0002-4512-087X" target="_blank"><img src="https://orcid.org/assets/vectors/orcid.logo.icon.svg" width="16" height="16" alt="ORCID"></a>
        <a href="mailto:paul.gierz@awi.de" style="text-decoration: none;">📧</a>
    </p>
    <p style="margin: 3px 0; font-size: 0.7em; font-style: italic; color: #666;">Lead Developer, Architecture</p>
</div>
</div>

<!-- > **Adding authors**: Edit [`AUTHORS.yaml`](AUTHORS.yaml) and run `python scripts/generate_author_badges.py` to regenerate badges. -->

---

### About DestinE Climate Digital Twin

This project is part of the **Destination Earth (DestinE) Climate Change Adaptation Digital Twin** initiative, a flagship programme of the European Union's digital strategy for climate adaptation and resilience.

**DestinE** aims to develop a highly accurate digital model of the Earth to monitor and predict the interaction between natural phenomena and human activities. The Climate Change Adaptation Digital Twin specifically focuses on:

- 🌡️ **Extreme Weather Events**: High-resolution modeling of hurricanes, floods, droughts, and heatwaves
- 🌊 **Climate Change Impacts**: Long-term climate projections and impact assessments
- 🛡️ **Adaptation Strategies**: Testing and optimizing climate adaptation measures
- 🔬 **Scientific Research**: Providing cutting-edge tools for climate scientists and decision-makers

**Key Infrastructure Partners**:
- **European Centre for Medium-Range Weather Forecasts (ECMWF)** - Core Platform
- **European Space Agency (ESA)** - Earth Observation Data
- **European Organisation for the Exploitation of Meteorological Satellites (EUMETSAT)** - Satellite Data

**Learn more**: [https://destination-earth.eu/](https://destination-earth.eu/)

---

## Acknowledgments

This project is supported by the **European Union's Digital Europe Programme** under the DestinE initiative.

We acknowledge the computational resources and infrastructure provided by:

- **Barcelona Supercomputing Center (BSC)** - MareNostrum supercomputer
- **LUMI consortium** - Pre-exascale European supercomputer
- **ECMWF** - High-performance computing facilities for climate modeling

Special thanks to the **Autosubmit** workflow management team at BSC for their collaboration and support in developing this error scanning framework.
