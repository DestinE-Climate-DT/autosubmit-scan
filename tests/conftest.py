"""
Pytest configuration and fixtures for autosubmit-scan tests.

This module provides fixtures for testing various remote file protocols:
- S3 (MinIO)
- SSH
- SFTP
- FTP
- Local filesystem

Fixtures are configured based on environment variables and CI detection.
"""

import os
from pathlib import Path

import pytest


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests (fast, no external dependencies)")
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (require external services)",
    )
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests (full system tests)")
    config.addinivalue_line("markers", "remote: marks tests that require remote services (S3, SFTP, FTP)")
    config.addinivalue_line("markers", "slow: marks tests as slow running (> 1 second)")


def is_ci() -> bool:
    """Check if running in CI environment."""
    return os.getenv("CI", "false").lower() == "true"


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection based on environment.

    Skip remote tests if not in CI and --remote flag is not set.
    """
    run_remote = config.getoption("--remote", default=False) or is_ci()

    if not run_remote:
        skip_remote = pytest.mark.skip(reason="Remote tests require --remote flag or CI environment")
        for item in items:
            if "remote" in item.keywords:
                item.add_marker(skip_remote)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--remote",
        action="store_true",
        default=False,
        help="Run tests that require remote services (S3, SFTP, FTP)",
    )


# ============================================================================
# Environment Configuration Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def minio_config() -> dict[str, str]:
    """MinIO/S3 configuration from environment."""
    return {
        "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        "access_key": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        "secret_key": os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        "secure": os.getenv("MINIO_SECURE", "false").lower() == "true",
    }


@pytest.fixture(scope="session")
def sftp_config() -> dict[str, str]:
    """SFTP configuration from environment."""
    return {
        "host": os.getenv("SFTP_HOST", "localhost"),
        "port": int(os.getenv("SFTP_PORT", "2222")),
        "user": os.getenv("SFTP_USER", "testuser"),
        "password": os.getenv("SFTP_PASSWORD", "testpass"),
    }


@pytest.fixture(scope="session")
def ftp_config() -> dict[str, str]:
    """FTP configuration from environment."""
    return {
        "host": os.getenv("FTP_HOST", "localhost"),
        "port": int(os.getenv("FTP_PORT", "2121")),
        "user": os.getenv("FTP_USER", "testuser"),
        "password": os.getenv("FTP_PASSWORD", "testpass"),
    }


# ============================================================================
# URI Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def s3_test_uri(minio_config) -> str:
    """S3 URI for test log file."""
    return "s3://test-logs/slurm/job123456.log"


@pytest.fixture(scope="session")
def ssh_test_uri(sftp_config) -> str:
    """SSH URI for test log file."""
    host = sftp_config["host"]
    port = sftp_config["port"]
    user = sftp_config["user"]
    password = sftp_config["password"]
    return f"ssh://{user}:{password}@{host}:{port}/upload/logs/slurm/job123456.log"


@pytest.fixture(scope="session")
def sftp_test_uri(sftp_config) -> str:
    """SFTP URI for test log file."""
    host = sftp_config["host"]
    port = sftp_config["port"]
    user = sftp_config["user"]
    password = sftp_config["password"]
    return f"sftp://{user}:{password}@{host}:{port}/upload/logs/slurm/job123456.log"


@pytest.fixture(scope="session")
def ftp_test_uri(ftp_config) -> str:
    """FTP URI for test log file."""
    host = ftp_config["host"]
    port = ftp_config["port"]
    user = ftp_config["user"]
    password = ftp_config["password"]
    return f"ftp://{user}:{password}@{host}:{port}/logs/slurm/job123456.log"


@pytest.fixture(scope="session")
def local_test_file(tmp_path_factory) -> Path:
    """Local test file path."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    return fixtures_dir / "slurm_oom.log"


# ============================================================================
# fsspec Filesystem Fixtures
# ============================================================================


@pytest.fixture
def s3_filesystem(minio_config):
    """Create an S3 filesystem using fsspec."""
    import fsspec

    endpoint = minio_config["endpoint"]
    secure = minio_config["secure"]
    protocol = "https" if secure else "http"

    fs = fsspec.filesystem(
        "s3",
        key=minio_config["access_key"],
        secret=minio_config["secret_key"],
        client_kwargs={
            "endpoint_url": f"{protocol}://{endpoint}",
        },
    )
    return fs


@pytest.fixture
def sftp_filesystem(sftp_config):
    """Create an SFTP filesystem using fsspec."""
    import fsspec

    # Note: sshfs (fsspec SSH backend) uses paramiko internally
    fs = fsspec.filesystem(
        "sftp",
        host=sftp_config["host"],
        port=sftp_config["port"],
        username=sftp_config["user"],
        password=sftp_config["password"],
    )
    return fs


@pytest.fixture
def ftp_filesystem(ftp_config):
    """Create an FTP filesystem using fsspec."""
    import fsspec

    fs = fsspec.filesystem(
        "ftp",
        host=ftp_config["host"],
        port=ftp_config["port"],
        username=ftp_config["user"],
        password=ftp_config["password"],
    )
    return fs


@pytest.fixture
def local_filesystem():
    """Create a local filesystem using fsspec."""
    import fsspec

    return fsspec.filesystem("file")


# ============================================================================
# Parametrized Fixtures for Testing All Protocols
# ============================================================================


@pytest.fixture(
    params=["s3", "sftp", "ftp", "local"],
    ids=["s3", "sftp", "ftp", "local"],
)
def all_protocols_uri(
    request,
    s3_test_uri,
    sftp_test_uri,
    ftp_test_uri,
    local_test_file,
):
    """Parametrized fixture that yields URIs for all protocols."""
    protocol = request.param

    if protocol == "s3":
        pytest.skip("S3 tests require --remote flag")
        return s3_test_uri
    elif protocol == "sftp":
        pytest.skip("SFTP tests require --remote flag")
        return sftp_test_uri
    elif protocol == "ftp":
        pytest.skip("FTP tests require --remote flag")
        return ftp_test_uri
    elif protocol == "local":
        return str(local_test_file)


@pytest.fixture(
    params=["s3", "sftp", "ftp"],
    ids=["s3", "sftp", "ftp"],
)
def remote_protocols_uri(
    request,
    s3_test_uri,
    sftp_test_uri,
    ftp_test_uri,
):
    """Parametrized fixture that yields URIs for remote protocols only."""
    protocol = request.param

    if protocol == "s3":
        return s3_test_uri
    elif protocol == "sftp":
        return sftp_test_uri
    elif protocol == "ftp":
        return ftp_test_uri


@pytest.fixture(
    params=["s3", "sftp", "ftp"],
    ids=["s3-fs", "sftp-fs", "ftp-fs"],
)
def remote_filesystem(
    request,
    s3_filesystem,
    sftp_filesystem,
    ftp_filesystem,
):
    """Parametrized fixture that yields filesystem objects for remote protocols."""
    protocol = request.param

    if protocol == "s3":
        return s3_filesystem
    elif protocol == "sftp":
        return sftp_filesystem
    elif protocol == "ftp":
        return ftp_filesystem


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_log_files(fixtures_dir) -> dict[str, Path]:
    """Dictionary of sample log files."""
    return {
        "oom": fixtures_dir / "slurm_oom.log",
        "timeout": fixtures_dir / "slurm_timeout.log",
        "app_error": fixtures_dir / "application_error.log",
    }


@pytest.fixture
def expected_oom_error() -> dict[str, str]:
    """Expected error patterns for OOM log."""
    return {
        "error_type": "out_of_memory",
        "pattern": r"Out of memory|oom-kill|Exceeded.*memory limit",
        "exit_code": 137,
    }


@pytest.fixture
def expected_timeout_error() -> dict[str, str]:
    """Expected error patterns for timeout log."""
    return {
        "error_type": "timeout",
        "pattern": r"time limit|TIMEOUT|CANCELLED.*TIME LIMIT",
        "exit_code": 140,
    }


@pytest.fixture
def expected_app_error() -> dict[str, str]:
    """Expected error patterns for application error log."""
    return {
        "error_type": "application_error",
        "pattern": r"ERROR:|FATAL:|Traceback",
        "exit_code": 1,
    }


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def temp_output_dir(tmp_path) -> Path:
    """Temporary directory for test outputs."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture(autouse=True)
def reset_env_vars():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
