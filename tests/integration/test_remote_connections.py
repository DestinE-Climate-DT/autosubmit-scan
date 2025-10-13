"""
Integration tests for remote service connections.

Tests basic connectivity to all remote services:
- MinIO (S3)
- SFTP
- FTP

These tests verify that the CI services are properly configured
and accessible before running more complex tests.
"""

import pytest


@pytest.mark.integration
@pytest.mark.remote
def test_minio_connection(minio_config):
    """Test connection to MinIO/S3 service."""
    import boto3

    # Create S3 client
    endpoint = minio_config["endpoint"]
    secure = minio_config["secure"]
    protocol = "https" if secure else "http"

    s3_client = boto3.client(
        "s3",
        endpoint_url=f"{protocol}://{endpoint}",
        aws_access_key_id=minio_config["access_key"],
        aws_secret_access_key=minio_config["secret_key"],
        region_name="us-east-1",
    )

    # Try to list buckets
    response = s3_client.list_buckets()

    # Verify we can see buckets
    assert "Buckets" in response
    bucket_names = [b["Name"] for b in response["Buckets"]]
    assert "test-logs" in bucket_names, "test-logs bucket should exist"

    # Verify we can access the test bucket
    response = s3_client.list_objects_v2(Bucket="test-logs")
    assert "Contents" in response or "KeyCount" in response


@pytest.mark.integration
@pytest.mark.remote
def test_minio_test_file_exists(minio_config):
    """Test that test files exist in MinIO."""
    import boto3

    endpoint = minio_config["endpoint"]
    secure = minio_config["secure"]
    protocol = "https" if secure else "http"

    s3_client = boto3.client(
        "s3",
        endpoint_url=f"{protocol}://{endpoint}",
        aws_access_key_id=minio_config["access_key"],
        aws_secret_access_key=minio_config["secret_key"],
        region_name="us-east-1",
    )

    # Check for test file
    response = s3_client.head_object(
        Bucket="test-logs",
        Key="slurm/job123456.log",
    )

    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    assert response["ContentLength"] > 0


@pytest.mark.integration
@pytest.mark.remote
def test_sftp_connection(sftp_config):
    """Test connection to SFTP service."""
    import paramiko

    # Create SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect
    ssh_client.connect(
        hostname=sftp_config["host"],
        port=sftp_config["port"],
        username=sftp_config["user"],
        password=sftp_config["password"],
        timeout=10,
        allow_agent=False,
        look_for_keys=False,
    )

    # Open SFTP session
    sftp_client = ssh_client.open_sftp()

    # List root directory
    files = sftp_client.listdir(".")
    assert isinstance(files, list)

    # Close connections
    sftp_client.close()
    ssh_client.close()


@pytest.mark.integration
@pytest.mark.remote
def test_sftp_test_file_exists(sftp_config):
    """Test that test files exist on SFTP server."""
    import paramiko

    # Create SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect
    ssh_client.connect(
        hostname=sftp_config["host"],
        port=sftp_config["port"],
        username=sftp_config["user"],
        password=sftp_config["password"],
        timeout=10,
        allow_agent=False,
        look_for_keys=False,
    )

    # Open SFTP session
    sftp_client = ssh_client.open_sftp()

    # Check for test file
    stat = sftp_client.stat("upload/logs/slurm/job123456.log")
    assert stat.st_size > 0

    # Close connections
    sftp_client.close()
    ssh_client.close()


@pytest.mark.integration
@pytest.mark.remote
def test_ftp_connection(ftp_config):
    """Test connection to FTP service."""
    from ftplib import FTP

    # Create FTP client
    ftp_client = FTP()

    # Connect
    ftp_client.connect(
        host=ftp_config["host"],
        port=ftp_config["port"],
        timeout=10,
    )

    # Login
    ftp_client.login(
        user=ftp_config["user"],
        passwd=ftp_config["password"],
    )

    # Get welcome message
    welcome = ftp_client.getwelcome()
    assert welcome is not None

    # List root directory
    files = []
    ftp_client.retrlines("LIST", files.append)
    assert isinstance(files, list)

    # Close connection
    ftp_client.quit()


@pytest.mark.integration
@pytest.mark.remote
def test_ftp_test_file_exists(ftp_config):
    """Test that test files exist on FTP server."""
    from ftplib import FTP

    # Create FTP client
    ftp_client = FTP()

    # Connect
    ftp_client.connect(
        host=ftp_config["host"],
        port=ftp_config["port"],
        timeout=10,
    )

    # Login
    ftp_client.login(
        user=ftp_config["user"],
        passwd=ftp_config["password"],
    )

    # Check for test file
    size = ftp_client.size("logs/slurm/job123456.log")
    assert size is not None or size > 0

    # If SIZE command not supported, try LIST
    if size is None:
        files = []
        ftp_client.retrlines("LIST logs/slurm/job123456.log", files.append)
        assert len(files) > 0

    # Close connection
    ftp_client.quit()


@pytest.mark.integration
@pytest.mark.remote
def test_all_services_accessible(minio_config, sftp_config, ftp_config):
    """
    Test that all services are accessible simultaneously.

    This ensures there are no port conflicts or resource issues.
    """
    from ftplib import FTP

    import boto3
    import paramiko

    # Test MinIO
    endpoint = minio_config["endpoint"]
    secure = minio_config["secure"]
    protocol = "https" if secure else "http"

    s3_client = boto3.client(
        "s3",
        endpoint_url=f"{protocol}://{endpoint}",
        aws_access_key_id=minio_config["access_key"],
        aws_secret_access_key=minio_config["secret_key"],
        region_name="us-east-1",
    )
    s3_buckets = s3_client.list_buckets()
    assert "Buckets" in s3_buckets

    # Test SFTP
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(
        hostname=sftp_config["host"],
        port=sftp_config["port"],
        username=sftp_config["user"],
        password=sftp_config["password"],
        timeout=10,
        allow_agent=False,
        look_for_keys=False,
    )
    sftp_client = ssh_client.open_sftp()
    sftp_files = sftp_client.listdir(".")
    assert isinstance(sftp_files, list)

    # Test FTP
    ftp_client = FTP()
    ftp_client.connect(
        host=ftp_config["host"],
        port=ftp_config["port"],
        timeout=10,
    )
    ftp_client.login(
        user=ftp_config["user"],
        passwd=ftp_config["password"],
    )
    ftp_welcome = ftp_client.getwelcome()
    assert ftp_welcome is not None

    # Clean up all connections
    ftp_client.quit()
    sftp_client.close()
    ssh_client.close()
