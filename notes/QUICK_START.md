# Quick Start Guide

## Overview

This project now has a complete CI/CD infrastructure ready for TDD (Test-Driven Development). All test infrastructure is configured to work with multiple remote file protocols: S3, SFTP, FTP, and local files.

## Installation

```bash
# Install all dependencies
pixi install
```

## Running Tests

### All Tests
```bash
pixi run test
```

### Unit Tests Only (Fast)
```bash
pixi run test-unit
```

### Integration Tests (Requires Services)
```bash
pixi run test-integration
```

### With Coverage Report
```bash
pixi run coverage-report
```

## Local Development with Remote Services

### 1. Start Service Containers

```bash
# MinIO (S3)
docker run -d -p 9000:9000 -p 9001:9001 \
  --name minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"

# SFTP
docker run -d -p 2222:22 \
  --name sftp \
  -e SFTP_USERS=testuser:testpass:1001 \
  atmoz/sftp

# FTP
docker run -d -p 2121:21 -p 21000-21010:21000-21010 \
  --name ftp \
  -e USERS=testuser|testpass \
  -e ADDRESS=localhost \
  delfer/alpine-ftp-server
```

### 2. Setup Test Data

```bash
pixi run ci-setup-minio
pixi run ci-setup-sftp
pixi run ci-setup-ftp
```

### 3. Run Integration Tests

```bash
pixi run test-integration
```

### 4. Stop Services

```bash
docker stop minio sftp ftp
docker rm minio sftp ftp
```

## Project Structure

```
.
├── .github/workflows/
│   ├── test.yml              # CI/CD workflow
│   └── README.md             # Workflow documentation
├── scripts/ci/
│   ├── setup_minio.py        # MinIO setup script
│   ├── setup_sftp.py         # SFTP setup script
│   ├── setup_ftp.py          # FTP setup script
│   └── README.md             # Setup scripts docs
├── tests/
│   ├── fixtures/             # Test log files
│   │   ├── slurm_oom.log
│   │   ├── slurm_timeout.log
│   │   └── application_error.log
│   ├── integration/          # Integration tests
│   │   ├── test_remote_connections.py
│   │   └── test_fsspec_protocols.py
│   ├── unit/                 # Unit tests (to be added)
│   ├── conftest.py           # Pytest configuration
│   └── README.md             # Testing documentation
├── pixi.toml                 # Dependencies and tasks
├── pytest.ini                # Pytest configuration
└── CI_SETUP_SUMMARY.md       # Complete setup summary
```

## Writing Your First Test

### 1. Unit Test (Fast)

Create `tests/unit/test_example.py`:

```python
import pytest

@pytest.mark.unit
def test_simple_function():
    """Test a simple function."""
    result = 1 + 1
    assert result == 2
```

### 2. Integration Test (With Services)

Create `tests/integration/test_example.py`:

```python
import pytest

@pytest.mark.integration
@pytest.mark.remote
def test_s3_read(s3_filesystem):
    """Test reading from S3."""
    with s3_filesystem.open("test-logs/slurm/job123456.log", "r") as f:
        content = f.read()

    assert len(content) > 0
    assert "Out of memory" in content
```

## Available Fixtures

### Configuration Fixtures
- `minio_config`: MinIO/S3 configuration
- `sftp_config`: SFTP configuration
- `ftp_config`: FTP configuration

### URI Fixtures
- `s3_test_uri`: S3 test file URI
- `sftp_test_uri`: SFTP test file URI
- `ftp_test_uri`: FTP test file URI
- `local_test_file`: Local test file path

### Filesystem Fixtures
- `s3_filesystem`: fsspec S3 filesystem
- `sftp_filesystem`: fsspec SFTP filesystem
- `ftp_filesystem`: fsspec FTP filesystem

### Test Data Fixtures
- `fixtures_dir`: Test fixtures directory path
- `sample_log_files`: Dictionary of log files
- `expected_oom_error`: OOM error patterns
- `expected_timeout_error`: Timeout error patterns
- `expected_app_error`: Application error patterns

## Environment Variables

### MinIO/S3
- `MINIO_ENDPOINT=localhost:9000`
- `MINIO_ACCESS_KEY=minioadmin`
- `MINIO_SECRET_KEY=minioadmin`
- `MINIO_SECURE=false`

### SFTP
- `SFTP_HOST=localhost`
- `SFTP_PORT=2222`
- `SFTP_USER=testuser`
- `SFTP_PASSWORD=testpass`

### FTP
- `FTP_HOST=localhost`
- `FTP_PORT=2121`
- `FTP_USER=testuser`
- `FTP_PASSWORD=testpass`

## Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit           # Fast, no external deps
@pytest.mark.integration    # Requires services
@pytest.mark.e2e           # Full system tests
@pytest.mark.remote        # Requires remote services
@pytest.mark.slow          # Takes > 1 second
```

## Next Steps

1. **Implement Core Logic**:
   - Create protocol parsers
   - Implement error detection
   - Add streaming capabilities

2. **Write Tests First (TDD)**:
   - Write failing test
   - Implement feature
   - Make test pass
   - Refactor

3. **Run Tests Often**:
   ```bash
   # Fast feedback loop
   pixi run test-unit

   # Before committing
   pixi run test
   ```

4. **Check Coverage**:
   ```bash
   pixi run coverage-report
   open htmlcov/index.html
   ```

## CI/CD

Tests run automatically on:
- Push to main/develop
- Pull requests
- Manual workflow dispatch

View results at: `https://github.com/DestinE-Climate-DT/autosubmit-scan/actions`

## Troubleshooting

### Tests fail with "remote tests require --remote flag"
Run with CI environment variable:
```bash
CI=true pixi run test
```

### "Connection refused" errors
Ensure services are running:
```bash
docker ps
```

### Import errors
Reinstall dependencies:
```bash
pixi install
```

## Documentation

- **Testing**: `tests/README.md`
- **CI/CD**: `.github/workflows/README.md`
- **Setup Scripts**: `scripts/ci/README.md`
- **Complete Summary**: `CI_SETUP_SUMMARY.md`

## Getting Help

1. Check documentation in `tests/README.md`
2. Review examples in `tests/integration/`
3. Check fixture definitions in `tests/conftest.py`
4. Review CI workflow in `.github/workflows/test.yml`

---

**Ready to start development!** Begin with `pixi run test-unit` to verify your setup.
