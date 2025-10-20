# autosubmit-scan Documentation

<div class="hero-section" markdown="1">

```{image} ../assets/title-svg.svg
:alt: DestinE Climate DT
:width: 400px
:align: center
```

**A comprehensive remote error monitoring and scanning system for analyzing log files across distributed systems.**

Built for climate scientists, HPC users, and DevOps engineers working with large-scale computational workflows.

[Get Started](getting-started/quickstart.md){.btn .btn-primary .btn-lg}
[View on GitHub](https://github.com/DestinE-Climate-DT/autosubmit-scan){.btn .btn-secondary .btn-lg}

</div>

---

## What is autosubmit-scan?

autosubmit-scan (`as-scan`) is an intelligent log analysis tool designed for distributed computing environments. It provides:

- **Pattern-based error detection** across local and remote filesystems
- **Conditional error chaining** using the Railway pattern
- **Parallel workflow execution** powered by Snakemake
- **Multi-protocol support** for S3, SFTP, SSH, FTP, and local files
- **Efficient connection pooling** for remote file scanning

```{admonition} Use Case: Climate Model Workflows
:class: tip

Monitor thousands of SLURM job logs across HPC clusters, automatically detect out-of-memory errors, connection timeouts, and filesystem issues, then chain related errors to identify root causes.
```

---

## Key Features

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} Pattern Matching Engine
:class-header: bg-light

Support for **literal**, **regex**, and **custom callable** patterns with full regex flag support.

```yaml
pattern:
  type: "regex"
  pattern: "ERROR|CRITICAL|FATAL"
  flags: ["IGNORECASE"]
```
:::

:::{grid-item-card} Railway Pattern
:class-header: bg-light

Chain errors conditionally based on context, severity, or custom logic.

```yaml
next_errors:
  - error_id: "escalate"
    when:
      type: "field_equals"
      field: "severity"
      value: "critical"
```
:::

:::{grid-item-card} Remote File Access
:class-header: bg-light

Scan files across **S3**, **SFTP**, **SSH**, **FTP**, and local filesystems with unified glob patterns.

```yaml
files:
  - "ssh://hpc-cluster:/logs/**/*.out"
  - "s3://bucket/logs/**/*.err"
```
:::

:::{grid-item-card} Parallel Execution
:class-header: bg-light

Snakemake-powered workflow orchestration with automatic checkpointing and caching.

```bash
as-scan scan --catalog errors.yaml --cores 8
```
:::

::::

---

## Quick Start

### Installation

::::{tab-set}

:::{tab-item} Pixi (Recommended)
```bash
git clone https://github.com/DestinE-Climate-DT/autosubmit-scan.git
cd autosubmit-scan
pixi install
pixi run as-scan --help
```
:::

:::{tab-item} pip
```bash
pip install -e .
as-scan --help
```
:::

::::

### Basic Workflow

```bash
# 1. Create sample catalog
as-scan init --output my_catalog.yaml

# 2. Validate syntax
as-scan validate my_catalog.yaml

# 3. Run scan
as-scan scan --catalog my_catalog.yaml --output ./results --cores 4

# 4. View results interactively
as-scan view ./results/report.json

# 5. Export to markdown
as-scan export ./results/report.json --template markdown --output report.md
```

---

## Architecture Overview

```{mermaid}
flowchart TB
    subgraph User["User Interface"]
        CLI[CLI Commands<br/>scan, view, export, validate]
    end

    subgraph Core["Core Components"]
        Domain[Domain Layer<br/>Models & Validation]
        Matching[Pattern Matching<br/>Literal, Regex, Callable]
        Railway[Railway Pattern<br/>Conditional Chaining]
    end

    subgraph Orchestration["Workflow Engine"]
        Snake[Snakemake Pipeline]
        Discovery[File Discovery]
        Fingerprint[Fingerprinting]
        Scan[Pattern Scanning]
        Extract[Context Extraction]
    end

    subgraph Storage["Data Sources"]
        Local[Local Files]
        S3[AWS S3]
        SFTP[SFTP/SSH]
        FTP[FTP Servers]
    end

    subgraph Output["Results"]
        JSON[JSON-LD Report]
        TUI[Terminal UI]
        Templates[Export Templates]
    end

    CLI --> Domain
    CLI --> Snake
    Domain --> Matching
    Domain --> Railway
    Snake --> Discovery
    Discovery --> Fingerprint
    Fingerprint --> Scan
    Scan --> Extract
    Extract --> Railway
    Railway --> JSON
    JSON --> TUI
    JSON --> Templates

    Discovery -.->|fsspec| Local
    Discovery -.->|fsspec| S3
    Discovery -.->|fsspec| SFTP
    Discovery -.->|fsspec| FTP

    classDef userClass fill:#4A90E2,stroke:#2E5C8A,color:#fff
    classDef coreClass fill:#7ED321,stroke:#5A9C1A,color:#000
    classDef orchClass fill:#F5A623,stroke:#C17D11,color:#000
    classDef storageClass fill:#BD10E0,stroke:#8B0BA8,color:#fff
    classDef outputClass fill:#50E3C2,stroke:#2FB89C,color:#000

    class User,CLI userClass
    class Core,Domain,Matching,Railway coreClass
    class Orchestration,Snake,Discovery,Fingerprint,Scan,Extract orchClass
    class Storage,Local,S3,SFTP,FTP storageClass
    class Output,JSON,TUI,Templates outputClass
```

**Layer Architecture:**
- **CLI Layer**: User-facing commands with Click framework
- **Domain Layer**: Pydantic models and business logic
- **Matching Layer**: Pattern matching strategies
- **Orchestration Layer**: Snakemake workflow execution
- **Railway Layer**: Conditional error chaining
- **Reporting Layer**: JSON-LD generation and export

[Learn more about architecture](explanation/architecture.md)

---

## How It Works: Railway Pattern

The Railway pattern enables intelligent error chaining based on runtime conditions:

```{mermaid}
flowchart LR
    Start([Scan Logs]) --> OOM{OOM Error<br/>Detected?}
    OOM -->|Yes| Match1[ErrorMatch:<br/>OOM killed]
    OOM -->|No| Continue1[Continue Scan]

    Match1 --> Condition1{severity<br/>== critical?}
    Condition1 -->|Yes| Check[Check Memory<br/>Allocation]
    Condition1 -->|No| End1([End])

    Check --> Condition2{memory<br/>> 100GB?}
    Condition2 -->|Yes| Escalate[Escalate to Ops]
    Condition2 -->|No| Suggest[Suggest Increase<br/>Memory]

    Escalate --> Notify[Send Alert]
    Suggest --> Ticket[Create Ticket]

    Notify --> End2([End])
    Ticket --> End2
    Continue1 --> End3([End])

    classDef errorClass fill:#E74C3C,stroke:#C0392B,color:#fff
    classDef checkClass fill:#F39C12,stroke:#E67E22,color:#fff
    classDef actionClass fill:#3498DB,stroke:#2980B9,color:#fff
    classDef endClass fill:#95A5A6,stroke:#7F8C8D,color:#fff

    class OOM,Condition1,Condition2 checkClass
    class Match1,Check errorClass
    class Escalate,Suggest,Notify,Ticket actionClass
    class Start,End1,End2,End3,Continue1 endClass
```

**Example Catalog:**

```yaml
errors:
  oom_error:
    id: "oom_error"
    pattern:
      type: "literal"
      pattern: "OOM killed"
    next_errors:
      - error_id: "memory_check"
        when:
          type: "field_equals"
          field: "severity"
          value: "critical"

  memory_check:
    id: "memory_check"
    pattern:
      type: "callable"
      pattern: "checks:verify_memory_allocation"
    next_errors:
      - error_id: "escalate"
        when:
          type: "custom"
          callable: "checks:should_escalate"
```

[Learn more about the Railway pattern](how-to/railway-pattern.md)

---

## Use Cases

::::{grid} 1 1 2 3
:gutter: 2

:::{grid-item-card} Climate Model Monitoring
Monitor SLURM job failures across distributed HPC clusters (LUMI, MareNostrum, ECMWF).
:::

:::{grid-item-card} DevOps Log Analysis
Aggregate and analyze logs from S3 buckets, identify cascading failures.
:::

:::{grid-item-card} Research Workflow Debugging
Track errors in long-running computational workflows with automatic root cause analysis.
:::

:::{grid-item-card} CI/CD Pipeline Monitoring
Integrate error scanning into automated testing and deployment pipelines.
:::

:::{grid-item-card} Multi-Cloud Operations
Unified error monitoring across AWS, Azure, and on-premise infrastructure.
:::

:::{grid-item-card} Security Audit Logging
Pattern-based detection of security events and compliance violations.
:::

::::

---

## Documentation Structure

```{admonition} Following the Diátaxis Framework
:class: note

Our documentation is organized into four categories for optimal learning:

- **Tutorials**: Hands-on lessons for beginners
- **How-To Guides**: Goal-oriented practical guides
- **Reference**: Technical specifications and API docs
- **Explanation**: Conceptual discussion and background
```

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} Getting Started
:link: getting-started/quickstart
:link-type: doc

- [Quickstart Guide](getting-started/quickstart.md)
- [Installation](getting-started/installation.md)
- [Basic Concepts](getting-started/concepts.md)
:::

:::{grid-item-card} Tutorials
:link: tutorials/basic-scan
:link-type: doc

- [Your First Scan](tutorials/basic-scan.md)
- [Remote File Scanning](tutorials/remote-scan.md)
- [Using the Railway Pattern](tutorials/railway-tutorial.md)
:::

:::{grid-item-card} How-To Guides
:link: how-to/catalog-syntax
:link-type: doc

- [Catalog Syntax](how-to/catalog-syntax.md)
- [Pattern Matching](how-to/patterns.md)
- [Railway Pattern](how-to/railway-pattern.md)
- [SSH Connection Pooling](how-to/ssh-pooling.md)
:::

:::{grid-item-card} Reference
:link: reference/cli
:link-type: doc

- [CLI Reference](reference/cli.md)
- [API Documentation](reference/api.md)
- [Catalog Schema](reference/catalog-schema.md)
- [Template Variables](reference/templates.md)
:::

::::

---

## Performance & Optimization

### SSH Connection Pooling

```{important}
For remote scans, configure SSH ControlMaster to avoid connection timeouts!
```

**Without pooling:** 44+ connections per scan (11 errors × 4 operations)
**With pooling:** 1-2 connections per host

```bash
# Check configuration
as-scan check-ssh hostname

# Add to ~/.ssh/config
Host *
    ControlMaster auto
    ControlPath ~/.ssh/control-%C
    ControlPersist 10m
```

**Performance comparison:**

| Metric | Without Pooling | With Pooling |
|--------|----------------|--------------|
| Connections | 44 | 1-2 |
| Setup Time | ~88s | ~2.4s |
| Timeout Risk | High | Low |

[Complete SSH Pooling Guide](how-to/ssh-pooling.md)

---

## Community & Support

::::{grid} 1 1 3 3
:gutter: 2

:::{grid-item-card} GitHub Repository
:link: https://github.com/DestinE-Climate-DT/autosubmit-scan

View source code, report issues, and contribute.
:::

:::{grid-item-card} Contributing Guide
:link: contributing
:link-type: doc

Learn how to contribute code, documentation, or bug reports.
:::

:::{grid-item-card} API Reference
:link: reference/api
:link-type: doc

Complete API documentation for developers.
:::

::::

---

## Funding & Attribution

<div align="center">

```{image} ../assets/DestinE_logo_line_2_POS.png
:alt: DestinE - Funded by the European Union
:width: 600px
```

</div>

This project is proudly funded by the **European Union** under the **Destination Earth (DestinE) Climate Change Adaptation Digital Twin** initiative.

**DestinE** develops highly accurate digital models of Earth to monitor and predict interactions between natural phenomena and human activities, focusing on:

- High-resolution extreme weather event modeling
- Long-term climate projections and impact assessments
- Testing and optimizing climate adaptation measures
- Providing cutting-edge tools for climate scientists

**Learn more:** [https://destination-earth.eu/](https://destination-earth.eu/)

---

## License

This project is licensed under the terms specified in the [LICENSE](https://github.com/DestinE-Climate-DT/autosubmit-scan/blob/main/LICENSE) file.

---

## Next Steps

::::{grid} 1 1 3 3
:gutter: 2

:::{grid-item-card} Try the Quickstart
:link: getting-started/quickstart
:link-type: doc

Install and run your first scan in 5 minutes.
:::

:::{grid-item-card} Read the Architecture Guide
:link: explanation/architecture
:link-type: doc

Understand the system design and components.
:::

:::{grid-item-card} Explore Examples
:link: tutorials/examples
:link-type: doc

See real-world catalog configurations.
:::

::::

```{toctree}
:hidden:
:maxdepth: 2
:caption: Getting Started

getting-started/quickstart
getting-started/installation
getting-started/concepts
```

```{toctree}
:hidden:
:maxdepth: 2
:caption: Tutorials

tutorials/basic-scan
tutorials/remote-scan
tutorials/railway-tutorial
tutorials/examples
```

```{toctree}
:hidden:
:maxdepth: 2
:caption: How-To Guides

how-to/catalog-syntax
how-to/patterns
how-to/conditions
how-to/railway-pattern
how-to/ssh-pooling
how-to/templates
```

```{toctree}
:hidden:
:maxdepth: 2
:caption: Reference

reference/cli
reference/api
reference/catalog-schema
reference/templates
reference/snakemake-workflow
```

```{toctree}
:hidden:
:maxdepth: 2
:caption: Explanation

explanation/architecture
explanation/railway-pattern
explanation/connection-pooling
explanation/design-patterns
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Additional Resources

contributing
changelog
security
```
