#!/usr/bin/env python3
"""
SFTP Setup Script for CI/CD

This script configures an SFTP server for testing by:
1. Establishing connection to SFTP server
2. Creating test directory structure
3. Uploading test fixture log files
4. Verifying connectivity and permissions

Environment variables required:
- SFTP_HOST: SFTP server host (default: localhost)
- SFTP_PORT: SFTP server port (default: 2222)
- SFTP_USER: SFTP username (default: testuser)
- SFTP_PASSWORD: SFTP password (default: testpass)
"""

import os
import sys
import time
from pathlib import Path

from loguru import logger

try:
    import paramiko
    from paramiko.ssh_exception import (
        AuthenticationException,
        NoValidConnectionsError,
        SSHException,
    )
except ImportError:
    logger.error("paramiko is not installed. Install it with: pip install paramiko")
    sys.exit(1)


class SFTPSetup:
    """Setup SFTP server for CI/CD testing."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
    ):
        """Initialize SFTP client."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssh_client: paramiko.SSHClient | None = None
        self.sftp_client: paramiko.SFTPClient | None = None

        logger.info(f"SFTP client configured for {username}@{host}:{port}")

    def connect(self, timeout: int = 10) -> bool:
        """
        Establish SFTP connection.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to SSH server
            logger.info(f"Connecting to {self.host}:{self.port}...")
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=timeout,
                allow_agent=False,
                look_for_keys=False,
            )

            # Open SFTP session
            self.sftp_client = self.ssh_client.open_sftp()
            logger.success(f"Connected to SFTP server at {self.host}:{self.port}")
            return True

        except AuthenticationException as e:
            logger.error(f"Authentication failed: {e}")
            return False
        except NoValidConnectionsError as e:
            logger.error(f"Connection failed: {e}")
            return False
        except SSHException as e:
            logger.error(f"SSH error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            return False

    def wait_for_service(self, timeout: int = 60, retry_interval: int = 2) -> bool:
        """
        Wait for SFTP service to be ready.

        Args:
            timeout: Maximum time to wait in seconds
            retry_interval: Time between retries in seconds

        Returns:
            True if service is ready, False otherwise
        """
        start_time = time.time()
        attempt = 0

        logger.info(f"Waiting for SFTP service to be ready (timeout: {timeout}s)")

        while time.time() - start_time < timeout:
            attempt += 1
            try:
                if self.connect(timeout=5):
                    logger.success(f"SFTP service is ready (attempt {attempt})")
                    return True
            except Exception as e:
                logger.debug(f"Attempt {attempt} failed: {e}")

            # Clean up failed connection
            self.disconnect()
            time.sleep(retry_interval)

        logger.error(f"SFTP service did not become ready within {timeout}s")
        return False

    def create_directory(self, remote_path: str) -> bool:
        """
        Create a directory on the SFTP server (recursive).

        Args:
            remote_path: Path to create on remote server

        Returns:
            True if successful, False otherwise
        """
        if not self.sftp_client:
            logger.error("SFTP client is not connected")
            return False

        try:
            # Try to stat the directory first
            try:
                self.sftp_client.stat(remote_path)
                logger.info(f"Directory already exists: {remote_path}")
                return True
            except FileNotFoundError:
                # Directory doesn't exist, create it
                pass

            # Create parent directories recursively
            parts = remote_path.strip("/").split("/")
            current_path = ""

            for part in parts:
                current_path = f"{current_path}/{part}" if current_path else part
                try:
                    self.sftp_client.stat(current_path)
                except FileNotFoundError:
                    self.sftp_client.mkdir(current_path)
                    logger.debug(f"Created directory: {current_path}")

            logger.success(f"Created directory: {remote_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create directory {remote_path}: {e}")
            return False

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """
        Upload a file to SFTP server.

        Args:
            local_path: Path to local file
            remote_path: Target path on remote server

        Returns:
            True if successful, False otherwise
        """
        if not self.sftp_client:
            logger.error("SFTP client is not connected")
            return False

        try:
            if not local_path.exists():
                logger.error(f"Local file not found: {local_path}")
                return False

            # Ensure parent directory exists
            remote_dir = "/".join(remote_path.rsplit("/", 1)[:-1])
            if remote_dir:
                self.create_directory(remote_dir)

            # Upload file
            self.sftp_client.put(str(local_path), remote_path)
            logger.success(f"Uploaded {local_path.name} to {self.username}@{self.host}:{remote_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False

    def verify_file(self, remote_path: str) -> bool:
        """
        Verify that a file exists on SFTP server.

        Args:
            remote_path: Path to file on remote server

        Returns:
            True if file exists, False otherwise
        """
        if not self.sftp_client:
            logger.error("SFTP client is not connected")
            return False

        try:
            stat = self.sftp_client.stat(remote_path)
            size = stat.st_size if stat else 0
            logger.info(f"Verified {remote_path} ({size} bytes)")
            return True
        except FileNotFoundError:
            logger.error(f"File not found: {remote_path}")
            return False
        except Exception as e:
            logger.error(f"File verification failed for {remote_path}: {e}")
            return False

    def disconnect(self):
        """Close SFTP and SSH connections."""
        if self.sftp_client:
            try:
                self.sftp_client.close()
            except Exception:
                pass
            self.sftp_client = None

        if self.ssh_client:
            try:
                self.ssh_client.close()
            except Exception:
                pass
            self.ssh_client = None


def main():
    """Main setup function."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )

    # Get configuration from environment
    host = os.getenv("SFTP_HOST", "localhost")
    port = int(os.getenv("SFTP_PORT", "2222"))
    username = os.getenv("SFTP_USER", "testuser")
    password = os.getenv("SFTP_PASSWORD", "testpass")

    logger.info("Starting SFTP setup for CI/CD")
    logger.info(f"Server: {username}@{host}:{port}")

    # Initialize SFTP client
    sftp = SFTPSetup(
        host=host,
        port=port,
        username=username,
        password=password,
    )

    # Wait for SFTP to be ready
    if not sftp.wait_for_service(timeout=60):
        logger.error("SFTP service is not available")
        sys.exit(1)

    # Create test directory structure
    directories = [
        "upload/logs/slurm",
        "upload/logs/app",
        "upload/checkpoints",
        "upload/output",
    ]

    for directory in directories:
        if not sftp.create_directory(directory):
            logger.error(f"Failed to create directory: {directory}")
            sftp.disconnect()
            sys.exit(1)

    # Get fixtures directory
    project_root = Path(__file__).parent.parent.parent
    fixtures_dir = project_root / "tests" / "fixtures"

    if not fixtures_dir.exists():
        logger.error(f"Fixtures directory not found: {fixtures_dir}")
        sftp.disconnect()
        sys.exit(1)

    # Upload test log files to various paths
    test_files = [
        (fixtures_dir / "slurm_oom.log", "upload/logs/slurm/job123456.log"),
        (fixtures_dir / "slurm_timeout.log", "upload/logs/slurm/job789012.log"),
        (fixtures_dir / "application_error.log", "upload/logs/app/data_processor.log"),
        # Add duplicates in different locations for testing
        (fixtures_dir / "slurm_oom.log", "upload/checkpoints/oom_error.log"),
        (fixtures_dir / "slurm_timeout.log", "upload/output/timeout.log"),
    ]

    success = True
    for local_path, remote_path in test_files:
        if not sftp.upload_file(local_path, remote_path):
            success = False

    # Verify all uploads
    logger.info("Verifying uploaded files...")
    for _local_path, remote_path in test_files:
        if not sftp.verify_file(remote_path):
            success = False

    # Clean up
    sftp.disconnect()

    if success:
        logger.success("SFTP setup completed successfully")
        sys.exit(0)
    else:
        logger.error("SFTP setup completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
