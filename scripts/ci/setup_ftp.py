#!/usr/bin/env python3
"""
FTP Setup Script for CI/CD

This script configures an FTP server for testing by:
1. Establishing connection to FTP server
2. Creating test directory structure
3. Uploading test fixture log files
4. Verifying connectivity and permissions

Environment variables required:
- FTP_HOST: FTP server host (default: localhost)
- FTP_PORT: FTP server port (default: 2121)
- FTP_USER: FTP username (default: testuser)
- FTP_PASSWORD: FTP password (default: testpass)
"""

import os
import sys
import time
from ftplib import FTP, error_perm, error_temp
from pathlib import Path
from typing import Optional

from loguru import logger


class FTPSetup:
    """Setup FTP server for CI/CD testing."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
    ):
        """Initialize FTP client."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ftp_client: Optional[FTP] = None

        logger.info(f"FTP client configured for {username}@{host}:{port}")

    def connect(self, timeout: int = 10) -> bool:
        """
        Establish FTP connection.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create FTP client
            self.ftp_client = FTP()
            self.ftp_client.set_debuglevel(0)

            # Connect to FTP server
            logger.info(f"Connecting to {self.host}:{self.port}...")
            self.ftp_client.connect(host=self.host, port=self.port, timeout=timeout)

            # Login
            self.ftp_client.login(user=self.username, passwd=self.password)

            # Get welcome message
            welcome = self.ftp_client.getwelcome()
            logger.success(f"Connected to FTP server: {welcome}")
            return True

        except error_perm as e:
            logger.error(f"FTP permission error: {e}")
            return False
        except error_temp as e:
            logger.error(f"FTP temporary error: {e}")
            return False
        except OSError as e:
            logger.error(f"Connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            return False

    def wait_for_service(self, timeout: int = 60, retry_interval: int = 2) -> bool:
        """
        Wait for FTP service to be ready.

        Args:
            timeout: Maximum time to wait in seconds
            retry_interval: Time between retries in seconds

        Returns:
            True if service is ready, False otherwise
        """
        start_time = time.time()
        attempt = 0

        logger.info(f"Waiting for FTP service to be ready (timeout: {timeout}s)")

        while time.time() - start_time < timeout:
            attempt += 1
            try:
                if self.connect(timeout=5):
                    logger.success(f"FTP service is ready (attempt {attempt})")
                    return True
            except Exception as e:
                logger.debug(f"Attempt {attempt} failed: {e}")

            # Clean up failed connection
            self.disconnect()
            time.sleep(retry_interval)

        logger.error(f"FTP service did not become ready within {timeout}s")
        return False

    def create_directory(self, remote_path: str) -> bool:
        """
        Create a directory on the FTP server (recursive).

        Args:
            remote_path: Path to create on remote server

        Returns:
            True if successful, False otherwise
        """
        if not self.ftp_client:
            logger.error("FTP client is not connected")
            return False

        try:
            # Normalize path (remove leading/trailing slashes for consistency)
            remote_path = remote_path.strip("/")

            # Try to change to the directory first
            try:
                current_dir = self.ftp_client.pwd()
                self.ftp_client.cwd(remote_path)
                self.ftp_client.cwd(current_dir)  # Go back to original directory
                logger.info(f"Directory already exists: {remote_path}")
                return True
            except error_perm:
                # Directory doesn't exist, create it
                pass

            # Create parent directories recursively
            parts = remote_path.split("/")
            current_path = ""

            for part in parts:
                if not part:
                    continue

                current_path = f"{current_path}/{part}" if current_path else part

                try:
                    # Try to change to directory
                    saved_dir = self.ftp_client.pwd()
                    self.ftp_client.cwd(current_path)
                    self.ftp_client.cwd(saved_dir)
                except error_perm:
                    # Directory doesn't exist, create it
                    try:
                        self.ftp_client.mkd(current_path)
                        logger.debug(f"Created directory: {current_path}")
                    except error_perm as e:
                        logger.error(f"Failed to create directory {current_path}: {e}")
                        return False

            logger.success(f"Created directory: {remote_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create directory {remote_path}: {e}")
            return False

    def upload_file(
        self, local_path: Path, remote_path: str
    ) -> bool:
        """
        Upload a file to FTP server.

        Args:
            local_path: Path to local file
            remote_path: Target path on remote server

        Returns:
            True if successful, False otherwise
        """
        if not self.ftp_client:
            logger.error("FTP client is not connected")
            return False

        try:
            if not local_path.exists():
                logger.error(f"Local file not found: {local_path}")
                return False

            # Ensure parent directory exists
            remote_path = remote_path.strip("/")
            remote_dir = "/".join(remote_path.rsplit("/", 1)[:-1])
            if remote_dir:
                self.create_directory(remote_dir)

            # Upload file in binary mode
            with open(local_path, "rb") as f:
                self.ftp_client.storbinary(f"STOR {remote_path}", f)

            logger.success(
                f"Uploaded {local_path.name} to {self.username}@{self.host}:{remote_path}"
            )
            return True

        except error_perm as e:
            logger.error(f"FTP permission error uploading {local_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False

    def verify_file(self, remote_path: str) -> bool:
        """
        Verify that a file exists on FTP server.

        Args:
            remote_path: Path to file on remote server

        Returns:
            True if file exists, False otherwise
        """
        if not self.ftp_client:
            logger.error("FTP client is not connected")
            return False

        try:
            remote_path = remote_path.strip("/")

            # Get file size
            size = self.ftp_client.size(remote_path)
            if size is None:
                # Some FTP servers don't support SIZE command
                # Try LIST instead
                files = []
                self.ftp_client.retrlines(f"LIST {remote_path}", files.append)
                if files:
                    logger.info(f"Verified {remote_path}")
                    return True
                else:
                    logger.error(f"File not found: {remote_path}")
                    return False
            else:
                logger.info(f"Verified {remote_path} ({size} bytes)")
                return True

        except error_perm as e:
            logger.error(f"File not found or no permission: {remote_path} - {e}")
            return False
        except Exception as e:
            logger.error(f"File verification failed for {remote_path}: {e}")
            return False

    def disconnect(self):
        """Close FTP connection."""
        if self.ftp_client:
            try:
                self.ftp_client.quit()
            except Exception:
                try:
                    self.ftp_client.close()
                except Exception:
                    pass
            self.ftp_client = None


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
    host = os.getenv("FTP_HOST", "localhost")
    port = int(os.getenv("FTP_PORT", "2121"))
    username = os.getenv("FTP_USER", "testuser")
    password = os.getenv("FTP_PASSWORD", "testpass")

    logger.info("Starting FTP setup for CI/CD")
    logger.info(f"Server: {username}@{host}:{port}")

    # Initialize FTP client
    ftp = FTPSetup(
        host=host,
        port=port,
        username=username,
        password=password,
    )

    # Wait for FTP to be ready
    if not ftp.wait_for_service(timeout=60):
        logger.error("FTP service is not available")
        sys.exit(1)

    # Create test directory structure
    directories = [
        "logs/slurm",
        "logs/app",
        "checkpoints",
        "output",
    ]

    for directory in directories:
        if not ftp.create_directory(directory):
            logger.error(f"Failed to create directory: {directory}")
            ftp.disconnect()
            sys.exit(1)

    # Get fixtures directory
    project_root = Path(__file__).parent.parent.parent
    fixtures_dir = project_root / "tests" / "fixtures"

    if not fixtures_dir.exists():
        logger.error(f"Fixtures directory not found: {fixtures_dir}")
        ftp.disconnect()
        sys.exit(1)

    # Upload test log files to various paths
    test_files = [
        (fixtures_dir / "slurm_oom.log", "logs/slurm/job123456.log"),
        (fixtures_dir / "slurm_timeout.log", "logs/slurm/job789012.log"),
        (fixtures_dir / "application_error.log", "logs/app/data_processor.log"),
        # Add duplicates in different locations for testing
        (fixtures_dir / "slurm_oom.log", "checkpoints/oom_error.log"),
        (fixtures_dir / "slurm_timeout.log", "output/timeout.log"),
    ]

    success = True
    for local_path, remote_path in test_files:
        if not ftp.upload_file(local_path, remote_path):
            success = False

    # Verify all uploads
    logger.info("Verifying uploaded files...")
    for local_path, remote_path in test_files:
        if not ftp.verify_file(remote_path):
            success = False

    # Clean up
    ftp.disconnect()

    if success:
        logger.success("FTP setup completed successfully")
        sys.exit(0)
    else:
        logger.error("FTP setup completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
