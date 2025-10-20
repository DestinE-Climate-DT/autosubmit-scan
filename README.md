# `as-scan`: The Autosubmit Error Scanner

<p align="center">
  <img src="assets/title-svg.svg" alt="DestinE Earth" width="400"/>
</p>

A comprehensive remote error monitoring and scanning system for analyzing log files across distributed systems. Built with pattern matching, smart workflow management, and automatic error flowcharts for intelligent error tracking.

**What does this tool do?** It automatically scans your log files (local or remote) to find errors, and can intelligently check for related errors based on what it finds. Think of it as a smart search that follows error chains for you.

**Key concept - [Railway Pattern](docs/GLOSSARY.md#railway-pattern):** Automatic error flowcharts. When the tool finds one error, it can automatically check for related errors based on conditions you define. Example: Find "Out of Memory" → Automatically check which process failed.

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

## What is the Railway Pattern?

The Railway Pattern is like an automatic troubleshooting flowchart for your log files.

**Example: Medical Diagnosis Flowchart**
```
Find symptom: "Fever"
   → Automatically check: "Is temperature > 38C?"
   → If yes, automatically check: "Any other symptoms?"
   → If headache found, automatically check: "Recent travel?"
```

**How it works for log files:**
```
Find error: "Out of Memory"
   → Automatically check: "Which process failed?"
   → If Python process, automatically check: "Memory leak pattern?"
   → If leak found, create ticket
```

**Without Railway Pattern:** You manually search for each error, one at a time
**With Railway Pattern:** The tool follows your flowchart automatically, finding error chains in one scan

This saves hours of manual log searching and ensures you never miss related errors.

**Visual diagram:**

```mermaid
flowchart LR
    A[Find: Out of Memory] --> B{Check: Which process?}
    B -->|Python| C[Check: Memory leak pattern?]
    B -->|Other| D[Log and continue]
    C -->|Leak found| E[Create alert ticket]
    C -->|No leak| D

    style A fill:#ff6b6b
    style E fill:#51cf66
    style B fill:#ffd43b
    style C fill:#ffd43b
```

**Comparison:**

```mermaid
flowchart TD
    subgraph "Without Railway Pattern"
    M1[Manual search for Error A] --> M2[Find Error A]
    M2 --> M3[Manually search for Error B]
    M3 --> M4[Find Error B]
    M4 --> M5[Manually search for Error C]
    M5 --> M6[Find Error C]
    end

    subgraph "With Railway Pattern"
    A1[Scan once] --> A2[Find Error A]
    A2 --> A3[Auto-check Error B]
    A3 --> A4[Auto-check Error C]
    A4 --> A5[All results ready]
    end

    style M1 fill:#ff6b6b
    style M3 fill:#ff6b6b
    style M5 fill:#ff6b6b
    style A1 fill:#51cf66
    style A5 fill:#51cf66
```

---

## Features

- **[Pattern Matching](docs/GLOSSARY.md#pattern-matching)**: Three ways to find errors - exact text (literal), flexible patterns (regex), or custom logic (Python functions)
- **[Remote File Access](docs/GLOSSARY.md#remote-file-access)**: Scan files on any system - local files, SSH/SFTP servers, or cloud storage (S3)
- **[SSH Connection Reuse](docs/GLOSSARY.md#ssh-connection-reuse)**: Fast connection sharing for remote scans (critical for HPC systems - prevents timeouts)
- **[Railway Pattern](docs/GLOSSARY.md#railway-pattern)**: Automatic error flowcharts that follow error chains based on conditions you define
- **[Smart Caching](docs/GLOSSARY.md#snakemake)**: Only re-scans files that changed since last time (powered by Snakemake working behind the scenes)

## Bonus Features (WIP and not critical)

- **[Interactive Results Viewer](docs/GLOSSARY.md#interactive-results-viewer)**: Browse results with keyboard navigation in your terminal
- **Report Export**: Export to Markdown, HTML, or plain text formats
- **[Scan Reports](docs/GLOSSARY.md#scan-report)**: Structured error reports (JSON-LD format)

---

## Prerequisites

Before using autosubmit-scan, you should have:

**Required:**
- Basic command line skills (navigating directories, running commands)
- Can edit text files
- Have log files you want to scan (local or remote)
- Python 3.12 or higher

**Helpful but NOT required** (the tool explains as you go):
- Basic [YAML](docs/GLOSSARY.md#yaml) syntax - [5-minute tutorial](https://learnxinyminutes.com/docs/yaml/)
- [Regular expressions](docs/GLOSSARY.md#regex) (regex) basics - only needed for advanced pattern matching
- SSH configuration - only needed for remote file scanning
- Understanding of [glob patterns](docs/GLOSSARY.md#glob-patterns) (`*.log`, `**/*.log`) for matching multiple files

**You DON'T need to know:**
- Snakemake (works behind the scenes automatically)
- Pydantic (internal implementation detail)
- Design patterns (for developers only)
- JSON-LD (results can be viewed without understanding the format)

**What this guide will teach you:**
- How to create [error catalogs](docs/GLOSSARY.md#catalog) (configuration files)
- How to scan local and remote [log files](docs/GLOSSARY.md#log-file)
- How to set up automatic error chains ([Railway Pattern](docs/GLOSSARY.md#railway-pattern))
- How to view and export [results](docs/GLOSSARY.md#scan-report)

**Estimated time to first scan:** 30 minutes

---

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

### IMPORTANT: SSH Setup (Required for Remote Scans)

If you plan to scan files over SSH/SFTP, you MUST configure [SSH connection reuse](docs/GLOSSARY.md#ssh-connection-reuse):

**WARNING:** Without this setup, remote scans will fail with timeout errors after 2 minutes!

**Quick setup** (one-time, takes 2 minutes):

1. Add to your `~/.ssh/config` file:
   ```ssh-config
   Host *
       ControlMaster auto
       ControlPath ~/.ssh/control-%C
       ControlPersist 10m
   ```

2. Test it works:
   ```bash
   as-scan check-ssh your-hostname
   ```

**What this does:**
- Reuses SSH connections instead of creating new ones for each file
- Makes scans 10-40x faster
- Prevents timeout errors
- Works automatically with all SSH/SFTP file access

**Analogy:** Like carpooling vs everyone driving separately - connection reuse is more efficient and faster.

**Detailed guide:** See [docs/SSH_CONNECTION_POOLING.md](docs/SSH_CONNECTION_POOLING.md) for troubleshooting and advanced configuration.

**Skip this if:** You're only scanning local files (no SSH/SFTP).

---

## Quick Start

### 1. Create a Sample Catalog

```bash
as-scan init --output my_catalog.yaml
```

This creates a sample [catalog](docs/GLOSSARY.md#catalog) with example error definitions.

### 2. Validate Your Catalog

```bash
as-scan validate my_catalog.yaml
```

Ensures your [catalog](docs/GLOSSARY.md#catalog) is syntactically correct and follows the schema.

### 3. Run a Scan

```bash
as-scan scan --catalog my_catalog.yaml --output ./results --cores 4
```

This will:
- Discover files matching your [patterns](docs/GLOSSARY.md#glob-patterns)
- Scan for errors in parallel
- Apply [railway pattern](docs/GLOSSARY.md#railway-pattern) [conditions](docs/GLOSSARY.md#condition)
- Generate a [scan report](docs/GLOSSARY.md#scan-report)

### 4. View Results Interactively

```bash
as-scan view ./results/report.json
```

Launches an [interactive results viewer](docs/GLOSSARY.md#interactive-results-viewer) for browsing errors by type and file.

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

An [error catalog](docs/GLOSSARY.md#catalog) is a [YAML](docs/GLOSSARY.md#yaml) configuration file that tells the tool what errors to search for and how to handle them:

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

See [Pattern Matching](docs/GLOSSARY.md#pattern-matching) in the glossary for details.

- **[literal](docs/GLOSSARY.md#literal-pattern)**: Exact string matching
- **[regex](docs/GLOSSARY.md#regex-pattern)**: Regular expression with optional flags
- **[callable](docs/GLOSSARY.md#callable-pattern)**: Custom Python function

### File URIs

Supported [URI](docs/GLOSSARY.md#uri) schemes with **rsync-style notation** for SSH/SFTP:
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

See [Glob Patterns](docs/GLOSSARY.md#glob-patterns) for file matching details.

### Railway Pattern

Chain errors conditionally using the `next_errors` field. See [Railway Pattern](docs/GLOSSARY.md#railway-pattern) and [Condition](docs/GLOSSARY.md#condition) in the glossary for details.

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

## How It Works (Simple Workflow)

**What happens when you run a scan:**

```mermaid
flowchart TD
    Start([You run: as-scan scan]) --> Read[Tool reads your catalog file]
    Read --> Discover[Tool finds all matching files]
    Discover --> Scan[Tool scans files for errors]
    Scan --> Railway{Railway Pattern<br/>chains?}
    Railway -->|Yes| Chain[Auto-check related errors]
    Railway -->|No| Save
    Chain --> Save[Tool saves results]
    Save --> View([You view results])

    style Start fill:#4dabf7
    style View fill:#51cf66
    style Railway fill:#ffd43b
    style Scan fill:#ff6b6b
```

**More details:**

```mermaid
flowchart LR
    subgraph "1. Setup"
    C1[Create catalog.yaml] --> C2[Define error patterns]
    C2 --> C3[Specify file locations]
    end

    subgraph "2. Scan"
    S1[Run as-scan scan] --> S2[Discover files]
    S2 --> S3[Match patterns]
    S3 --> S4[Apply railway chains]
    end

    subgraph "3. Results"
    R1[Generate report.json] --> R2[View in TUI]
    R1 --> R3[Export to Markdown]
    R1 --> R4[Export to HTML]
    end

    C3 --> S1
    S4 --> R1

    style C1 fill:#e7f5ff
    style S1 fill:#fff3bf
    style R1 fill:#d3f9d8
```

**File pattern matching visualization:**

```mermaid
graph TD
    subgraph "Your Project"
    P[project/] --> L[logs/]
    P --> D[data/]
    L --> R1[run1.log]
    L --> R2[run2.log]
    D --> OUT[output.csv]
    P --> SUM[summary.log]
    end

    Pattern["Pattern: **/*.log"] -.Match.-> R1
    Pattern -.Match.-> R2
    Pattern -.Match.-> SUM
    Pattern -.No match.-> OUT

    style Pattern fill:#ffd43b
    style R1 fill:#51cf66
    style R2 fill:#51cf66
    style SUM fill:#51cf66
    style OUT fill:#ced4da
```

---

## Architecture

The system follows a modular architecture (for developers):

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

**Step 1: Create sample log file** (so the example actually works!)

```bash
# Create a directory for test logs
mkdir -p ~/test-logs

# Create a sample log file with some errors
cat > ~/test-logs/application.log << 'LOG'
2024-01-15 10:00:00 INFO Application started
2024-01-15 10:01:23 INFO Processing data batch 1
2024-01-15 10:02:45 ERROR Failed to connect to database
2024-01-15 10:02:46 INFO Retrying connection...
2024-01-15 10:03:10 CRITICAL Database connection timeout
2024-01-15 10:03:11 ERROR Unable to process batch 1
2024-01-15 10:04:00 INFO Application shutting down
LOG
```

**Step 2: Create error catalog**

```bash
# Create catalog that will scan the file we just created
cat > local_errors.yaml << 'EOF'
version: "1.0.0"
schema_version: "1.0.0"
metadata:
  name: "Local Errors Example"
  description: "Scan local log files for errors"
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
      # Works on Mac, Linux, and Windows (with Git Bash)
      - "~/test-logs/**/*.log"
    meaning: "Critical error detected in application logs"
    suggestion: "Review logs for details and check database connectivity"
    context_lines: 2
    next_errors: []
    metadata:
      severity: "high"
EOF
```

**Step 3: Run scan**

```bash
as-scan scan --catalog local_errors.yaml --output ./results
```

**Expected output:**
```
[INFO] Scanning files...
[INFO] Found 3 matches for error_keyword
[INFO] Results saved to ./results/report.json
```

**Step 4: View results**

```bash
as-scan view ./results/report.json
```

**What you should see:** 3 errors found (2 ERROR lines, 1 CRITICAL line) with 2 lines of context before/after each.

**Clean up when done:**
```bash
rm -rf ~/test-logs results local_errors.yaml
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
