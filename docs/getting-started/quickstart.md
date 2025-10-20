# Quickstart Guide

Get started with autosubmit-scan in 5 minutes.

**For unfamiliar terms, see the [Glossary](../GLOSSARY.md).**

## Installation

Choose your preferred installation method:

````{tab-set}
```{tab-item} Pixi (Recommended)
# Clone repository
git clone https://github.com/DestinE-Climate-DT/autosubmit-scan.git
cd autosubmit-scan

# Install with pixi
pixi install

# Verify installation
pixi run as-scan --help
```

```{tab-item} pip
# Install from source
pip install -e .

# Verify installation
as-scan --help
```
````

## Your First Scan

### 1. Create a Sample Catalog

```bash
as-scan init --output my_catalog.yaml
```

This creates an [error catalog](../GLOSSARY.md#catalog) (a [YAML](../GLOSSARY.md#yaml) configuration file) with example error [patterns](../GLOSSARY.md#pattern-matching).

### 2. Run the Scan

```bash
as-scan scan --catalog my_catalog.yaml --output ./results --cores 4
```

### 3. View Results

```bash
as-scan view ./results/report.json
```

This launches an [interactive results viewer](../GLOSSARY.md#interactive-results-viewer) (a terminal-based browser for your [scan results](../GLOSSARY.md#scan-report)).

**Navigation:**
- Arrow keys: Navigate
- Enter: Expand/collapse
- 'q': Quit

### 4. Export Report

```bash
as-scan export ./results/report.json --template markdown --output report.md
```

## Next Steps

- [Learn basic concepts](concepts.md)
- [Try the tutorials](../tutorials/01_getting_started.md)
- [Read the complete user guide](../USER_GUIDE.md)
