# Installation Guide

Complete installation instructions for all platforms.

## Prerequisites

- Python >= 3.12
- Git
- (Optional) Pixi package manager

## Method 1: Pixi (Recommended)

Pixi manages all dependencies automatically.

```bash
# Install Pixi (if not already installed)
curl -fsSL https://pixi.sh/install.sh | bash

# Clone repository
git clone https://github.com/DestinE-Climate-DT/autosubmit-scan.git
cd autosubmit-scan

# Install dependencies
pixi install

# Run commands
pixi run as-scan --help
```

## Method 2: pip

```bash
# Clone repository
git clone https://github.com/DestinE-Climate-DT/autosubmit-scan.git
cd autosubmit-scan

# Install in editable mode
pip install -e .

# Verify
as-scan --help
```

## Verification

```bash
# Check version
as-scan --version

# Run tests
pixi run test

# Validate sample catalog
as-scan validate examples/sample_catalog.yaml
```

## Optional Dependencies

### For S3 Support

```bash
pip install boto3 s3fs
```

### For SFTP Support

```bash
pip install paramiko sshfs
```

### For Development

```bash
pip install -e ".[dev]"
```

## Next Steps

- [Quickstart Guide](quickstart.md)
- [Basic Concepts](concepts.md)
