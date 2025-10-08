# Testing Documentation

This directory contains the test suite for autosubmit-scan, including unit tests, integration tests, and end-to-end tests.

## Directory Structure

```
tests/
├── __init__.py                       # Test package initialization
├── conftest.py                       # Pytest configuration and fixtures
├── fixtures/                         # Test data files
│   ├── slurm_oom.log                # Out of memory error log
│   ├── slurm_timeout.log            # Timeout error log
│   └── application_error.log        # Application error log
├── unit/                            # Unit tests (fast, no external deps)
│   └── __init__.py
├── integration/                     # Integration tests (require services)
│   ├── __init__.py
│   ├── test_remote_connections.py  # Test basic service connectivity
│   └── test_fsspec_protocols.py    # Test fsspec protocol support
└── e2e/                            # End-to-end tests (future)
```

## Test Categories

### Unit Tests (`tests/unit/`)

Fast tests with no external dependencies. Test individual functions and classes in isolation.

**Characteristics:**
- Run in < 100ms
- No network access
- No database access
- No file I/O (use mocks)
- 100% deterministic

**Run with:**
```bash
pixi run test-unit
```

### Integration Tests (`tests/integration/`)

Tests that interact with external services (MinIO, SFTP, FTP).

**Characteristics:**
- Require running services
- Test protocol implementations
- Verify data flow
- May take several seconds

**Run with:**
```bash
pixi run test-integration
```

### End-to-End Tests (`tests/e2e/`)

Full system tests that exercise complete workflows.

**Characteristics:**
- Test entire features
- Use real services
- Verify user scenarios
- Longest running tests

**Run with:**
```bash
pixi run test-e2e
```

## Pytest Markers

Tests are marked with decorators to categorize them:

- `@pytest.mark.unit`: Unit test
- `@pytest.mark.integration`: Integration test
- `@pytest.mark.e2e`: End-to-end test
- `@pytest.mark.remote`: Requires remote services
- `@pytest.mark.slow`: Takes > 1 second

**Example:**
```python
@pytest.mark.integration
@pytest.mark.remote
def test_sftp_connection(sftp_config):
    # Test SFTP connectivity
    pass
```

## Running Tests

### All Tests
```bash
pixi run test
```

### Specific Categories
```bash
pixi run test-unit           # Unit tests only
pixi run test-integration    # Integration tests with remote services
pixi run test-e2e           # End-to-end tests
pixi run test-fast          # All tests except slow ones
```

### With Coverage
```bash
pixi run coverage-report
```

### Specific Test File
```bash
pixi run pytest tests/integration/test_remote_connections.py
```

### Specific Test Function
```bash
pixi run pytest tests/integration/test_remote_connections.py::test_minio_connection
```

### With Verbose Output
```bash
pixi run pytest -v
```

### With Debug Output
```bash
pixi run pytest -vv --log-cli-level=DEBUG
```

## Test Fixtures

Pytest fixtures are defined in `conftest.py` and provide reusable test data and setup.

### Configuration Fixtures

- `minio_config`: MinIO/S3 configuration from environment
- `sftp_config`: SFTP configuration from environment
- `ftp_config`: FTP configuration from environment

### URI Fixtures

- `s3_test_uri`: S3 URI for test log file
- `sftp_test_uri`: SFTP URI for test log file
- `ftp_test_uri`: FTP URI for test log file
- `local_test_file`: Local file path for testing

### Filesystem Fixtures

- `s3_filesystem`: fsspec S3 filesystem
- `sftp_filesystem`: fsspec SFTP filesystem
- `ftp_filesystem`: fsspec FTP filesystem
- `local_filesystem`: fsspec local filesystem

### Parametrized Fixtures

- `all_protocols_uri`: Test all protocols (S3, SFTP, FTP, local)
- `remote_protocols_uri`: Test remote protocols only
- `remote_filesystem`: Test all remote filesystems

### Data Fixtures

- `fixtures_dir`: Path to test fixtures directory
- `sample_log_files`: Dictionary of sample log files
- `expected_oom_error`: Expected OOM error patterns
- `expected_timeout_error`: Expected timeout error patterns
- `expected_app_error`: Expected application error patterns

## Environment Variables

Tests use environment variables for configuration:

### MinIO/S3
- `MINIO_ENDPOINT`: localhost:9000
- `MINIO_ACCESS_KEY`: minioadmin
- `MINIO_SECRET_KEY`: minioadmin
- `MINIO_SECURE`: false

### SFTP
- `SFTP_HOST`: localhost
- `SFTP_PORT`: 2222
- `SFTP_USER`: testuser
- `SFTP_PASSWORD`: testpass

### FTP
- `FTP_HOST`: localhost
- `FTP_PORT`: 2121
- `FTP_USER`: testuser
- `FTP_PASSWORD`: testpass

### CI Detection
- `CI`: Set to "true" in CI environments

## Writing New Tests

### 1. Choose the Right Category

- **Unit**: Testing a pure function or isolated class
- **Integration**: Testing interaction with external services
- **E2E**: Testing a complete user workflow

### 2. Follow Naming Conventions

- File: `test_<feature>.py`
- Class: `Test<Feature>`
- Function: `test_<scenario>`

### 3. Use Appropriate Markers

```python
@pytest.mark.integration
@pytest.mark.remote
def test_new_feature(sftp_config):
    # Your test here
    pass
```

### 4. Use Fixtures

```python
def test_read_s3_file(s3_filesystem, s3_test_uri):
    with s3_filesystem.open("test-logs/file.log", "r") as f:
        content = f.read()
    assert len(content) > 0
```

### 5. Write Clear Assertions

```python
# Good
assert error_count == 3, "Expected 3 errors in log file"

# Bad
assert error_count == 3
```

### 6. Test Error Cases

```python
def test_invalid_uri():
    with pytest.raises(ValueError, match="Invalid URI"):
        parse_uri("not-a-uri")
```

### 7. Clean Up Resources

```python
def test_with_cleanup():
    client = create_client()
    try:
        # Test code
        pass
    finally:
        client.disconnect()
```

Or use fixtures with cleanup:

```python
@pytest.fixture
def client():
    c = create_client()
    yield c
    c.disconnect()
```

## Test Data

Sample log files in `tests/fixtures/`:

### `slurm_oom.log`
- Out of memory error
- Exit code: 137
- Pattern: "Out of memory", "oom-kill"

### `slurm_timeout.log`
- Job timeout error
- Exit code: 140
- Pattern: "time limit", "TIMEOUT"

### `application_error.log`
- Application error with traceback
- Exit code: 1
- Pattern: "ERROR:", "FATAL:", "Traceback"

## Coverage

Coverage reports are generated automatically:

- **Terminal**: Shows missing lines
- **HTML**: Open `htmlcov/index.html` in browser
- **XML**: Used by CI/CD for reporting

### Coverage Thresholds

Aim for:
- Overall: > 80%
- Core logic: > 90%
- UI/CLI: > 70%

## Continuous Integration

Tests run automatically in GitHub Actions on:
- Every push to main/develop
- Every pull request
- Manual workflow dispatch

See `.github/workflows/test.yml` for details.

## Troubleshooting

### Tests fail with "remote tests require --remote flag"

Run with the `--remote` flag or set `CI=true`:
```bash
pytest --remote
# or
CI=true pytest
```

### "Connection refused" errors

Ensure services are running:
```bash
docker ps  # Check running containers
```

Start missing services:
```bash
pixi run ci-setup-minio
pixi run ci-setup-sftp
pixi run ci-setup-ftp
```

### Fixture not found

Check that:
1. Fixture is defined in `conftest.py`
2. You're importing pytest: `import pytest`
3. Fixture name matches exactly

### Import errors

Ensure:
1. `__init__.py` exists in test directories
2. Project root is in PYTHONPATH
3. Dependencies are installed: `pixi install`

## Best Practices

1. **Keep tests independent**: Each test should run in isolation
2. **Use descriptive names**: Test name should describe what's being tested
3. **Test one thing**: Each test should verify one specific behavior
4. **Use fixtures**: Reuse setup code via fixtures
5. **Mock external services**: Use mocks for unit tests
6. **Test edge cases**: Test invalid inputs, boundaries, errors
7. **Keep tests fast**: Unit tests should run in milliseconds
8. **Clean up resources**: Always close connections, delete temp files
9. **Document complex tests**: Add comments explaining why, not what
10. **Review coverage**: Ensure new code is tested

## Resources

- [Pytest documentation](https://docs.pytest.org/)
- [Pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [fsspec documentation](https://filesystem-spec.readthedocs.io/)
- [Test-driven development](https://en.wikipedia.org/wiki/Test-driven_development)
