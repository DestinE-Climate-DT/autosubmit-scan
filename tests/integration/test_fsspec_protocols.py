"""
Integration tests for fsspec protocol support.

Tests that fsspec can successfully:
1. Open files from various remote protocols
2. Read content from remote files
3. Stream files without downloading
4. Handle protocol-specific URIs

These tests validate the core functionality needed for the
remote error monitoring system.
"""

import re

import pytest


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_s3_open_file(s3_filesystem):
    """Test opening a file from S3 using fsspec."""
    # Open file
    with s3_filesystem.open("test-logs/slurm/job123456.log", "r") as f:
        content = f.read()

    # Verify content is not empty
    assert len(content) > 0
    assert "Out of memory" in content or "OOM" in content.upper()


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_s3_read_lines(s3_filesystem):
    """Test reading lines from S3 file using fsspec."""
    # Open file and read lines
    with s3_filesystem.open("test-logs/slurm/job123456.log", "r") as f:
        lines = f.readlines()

    # Verify we got lines
    assert len(lines) > 0
    assert any("memory" in line.lower() for line in lines)


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_s3_file_info(s3_filesystem):
    """Test getting file information from S3 using fsspec."""
    # Get file info
    info = s3_filesystem.info("test-logs/slurm/job123456.log")

    # Verify info
    assert info is not None
    assert info["size"] > 0
    assert info["type"] == "file"


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_sftp_open_file(sftp_filesystem):
    """Test opening a file from SFTP using fsspec."""
    # Open file
    with sftp_filesystem.open("upload/logs/slurm/job123456.log", "r") as f:
        content = f.read()

    # Verify content is not empty
    assert len(content) > 0
    assert "Out of memory" in content or "OOM" in content.upper()


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_sftp_read_lines(sftp_filesystem):
    """Test reading lines from SFTP file using fsspec."""
    # Open file and read lines
    with sftp_filesystem.open("upload/logs/slurm/job123456.log", "r") as f:
        lines = f.readlines()

    # Verify we got lines
    assert len(lines) > 0
    assert any("memory" in line.lower() for line in lines)


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_sftp_file_info(sftp_filesystem):
    """Test getting file information from SFTP using fsspec."""
    # Get file info
    info = sftp_filesystem.info("upload/logs/slurm/job123456.log")

    # Verify info
    assert info is not None
    assert info["size"] > 0
    assert info["type"] == "file"


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_ftp_open_file(ftp_filesystem):
    """Test opening a file from FTP using fsspec."""
    # Open file
    with ftp_filesystem.open("logs/slurm/job123456.log", "r") as f:
        content = f.read()

    # Verify content is not empty
    assert len(content) > 0
    assert "Out of memory" in content or "OOM" in content.upper()


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_ftp_read_lines(ftp_filesystem):
    """Test reading lines from FTP file using fsspec."""
    # Open file and read lines
    with ftp_filesystem.open("logs/slurm/job123456.log", "r") as f:
        lines = f.readlines()

    # Verify we got lines
    assert len(lines) > 0
    assert any("memory" in line.lower() for line in lines)


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_ftp_file_info(ftp_filesystem):
    """Test getting file information from FTP using fsspec."""
    # Get file info
    info = ftp_filesystem.info("logs/slurm/job123456.log")

    # Verify info
    assert info is not None
    assert info["size"] > 0


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_open_uri_s3(s3_test_uri, minio_config):
    """Test opening S3 file using URI with fsspec.open()."""
    import fsspec

    # Configure storage options for MinIO
    endpoint = minio_config["endpoint"]
    secure = minio_config["secure"]
    protocol = "https" if secure else "http"

    storage_options = {
        "key": minio_config["access_key"],
        "secret": minio_config["secret_key"],
        "client_kwargs": {
            "endpoint_url": f"{protocol}://{endpoint}",
        },
    }

    # Open file using URI
    with fsspec.open(s3_test_uri, "r", **storage_options) as f:
        content = f.read()

    # Verify content
    assert len(content) > 0
    assert "Out of memory" in content or "OOM" in content.upper()


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_open_uri_sftp(sftp_test_uri):
    """Test opening SFTP file using URI with fsspec.open()."""
    import fsspec

    # Open file using URI (credentials are in the URI)
    with fsspec.open(sftp_test_uri, "r") as f:
        content = f.read()

    # Verify content
    assert len(content) > 0
    assert "Out of memory" in content or "OOM" in content.upper()


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_open_uri_ftp(ftp_test_uri):
    """Test opening FTP file using URI with fsspec.open()."""
    import fsspec

    # Open file using URI (credentials are in the URI)
    with fsspec.open(ftp_test_uri, "r") as f:
        content = f.read()

    # Verify content
    assert len(content) > 0
    assert "Out of memory" in content or "OOM" in content.upper()


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_streaming_s3(s3_filesystem):
    """Test streaming file content from S3 line by line."""
    error_pattern = re.compile(r"ERROR|Out of memory|oom-kill", re.IGNORECASE)
    errors_found = []

    # Stream file line by line
    with s3_filesystem.open("test-logs/slurm/job123456.log", "r") as f:
        for line_num, line in enumerate(f, 1):
            if error_pattern.search(line):
                errors_found.append((line_num, line.strip()))

    # Verify we found errors
    assert len(errors_found) > 0
    assert any("memory" in line.lower() for _, line in errors_found)


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_streaming_sftp(sftp_filesystem):
    """Test streaming file content from SFTP line by line."""
    error_pattern = re.compile(r"ERROR|Out of memory|oom-kill", re.IGNORECASE)
    errors_found = []

    # Stream file line by line
    with sftp_filesystem.open("upload/logs/slurm/job123456.log", "r") as f:
        for line_num, line in enumerate(f, 1):
            if error_pattern.search(line):
                errors_found.append((line_num, line.strip()))

    # Verify we found errors
    assert len(errors_found) > 0
    assert any("memory" in line.lower() for _, line in errors_found)


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_streaming_ftp(ftp_filesystem):
    """Test streaming file content from FTP line by line."""
    error_pattern = re.compile(r"ERROR|Out of memory|oom-kill", re.IGNORECASE)
    errors_found = []

    # Stream file line by line
    with ftp_filesystem.open("logs/slurm/job123456.log", "r") as f:
        for line_num, line in enumerate(f, 1):
            if error_pattern.search(line):
                errors_found.append((line_num, line.strip()))

    # Verify we found errors
    assert len(errors_found) > 0
    assert any("memory" in line.lower() for _, line in errors_found)


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_multiple_files_s3(s3_filesystem):
    """Test reading multiple files from S3."""
    files = [
        "test-logs/slurm/job123456.log",
        "test-logs/slurm/job789012.log",
        "test-logs/app/data_processor.log",
    ]

    contents = {}
    for file_path in files:
        with s3_filesystem.open(file_path, "r") as f:
            contents[file_path] = f.read()

    # Verify all files were read
    assert len(contents) == len(files)
    for content in contents.values():
        assert len(content) > 0


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_multiple_files_sftp(sftp_filesystem):
    """Test reading multiple files from SFTP."""
    files = [
        "upload/logs/slurm/job123456.log",
        "upload/logs/slurm/job789012.log",
        "upload/logs/app/data_processor.log",
    ]

    contents = {}
    for file_path in files:
        with sftp_filesystem.open(file_path, "r") as f:
            contents[file_path] = f.read()

    # Verify all files were read
    assert len(contents) == len(files)
    for content in contents.values():
        assert len(content) > 0


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_multiple_files_ftp(ftp_filesystem):
    """Test reading multiple files from FTP."""
    files = [
        "logs/slurm/job123456.log",
        "logs/slurm/job789012.log",
        "logs/app/data_processor.log",
    ]

    contents = {}
    for file_path in files:
        with ftp_filesystem.open(file_path, "r") as f:
            contents[file_path] = f.read()

    # Verify all files were read
    assert len(contents) == len(files)
    for content in contents.values():
        assert len(content) > 0


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_error_detection_oom(s3_filesystem, expected_oom_error):
    """Test detecting OOM errors in log file."""
    error_pattern = re.compile(expected_oom_error["pattern"], re.IGNORECASE)

    with s3_filesystem.open("test-logs/slurm/job123456.log", "r") as f:
        content = f.read()

    # Check for error pattern
    matches = error_pattern.findall(content)
    assert len(matches) > 0, "Should find OOM error pattern"

    # Check for exit code
    assert str(expected_oom_error["exit_code"]) in content


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_error_detection_timeout(s3_filesystem, expected_timeout_error):
    """Test detecting timeout errors in log file."""
    error_pattern = re.compile(expected_timeout_error["pattern"], re.IGNORECASE)

    with s3_filesystem.open("test-logs/slurm/job789012.log", "r") as f:
        content = f.read()

    # Check for error pattern
    matches = error_pattern.findall(content)
    assert len(matches) > 0, "Should find timeout error pattern"

    # Check for exit code
    assert str(expected_timeout_error["exit_code"]) in content


@pytest.mark.integration
@pytest.mark.remote
def test_fsspec_error_detection_app_error(s3_filesystem, expected_app_error):
    """Test detecting application errors in log file."""
    error_pattern = re.compile(expected_app_error["pattern"], re.IGNORECASE)

    with s3_filesystem.open("test-logs/app/data_processor.log", "r") as f:
        content = f.read()

    # Check for error pattern
    matches = error_pattern.findall(content)
    assert len(matches) > 0, "Should find application error pattern"

    # Check for exit code
    assert str(expected_app_error["exit_code"]) in content
