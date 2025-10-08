#!/usr/bin/env python3
"""
MinIO Setup Script for CI/CD

This script configures MinIO (S3-compatible storage) for testing by:
1. Creating test buckets
2. Uploading test fixture log files
3. Verifying connectivity and permissions

Environment variables required:
- MINIO_ENDPOINT: MinIO server endpoint (default: localhost:9000)
- MINIO_ACCESS_KEY: Access key (default: minioadmin)
- MINIO_SECRET_KEY: Secret key (default: minioadmin)
- MINIO_SECURE: Use HTTPS (default: false)
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

from loguru import logger

try:
    import boto3
    from botocore.exceptions import ClientError, EndpointConnectionError
except ImportError:
    logger.error("boto3 is not installed. Install it with: pip install boto3")
    sys.exit(1)


class MinIOSetup:
    """Setup MinIO for CI/CD testing."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
    ):
        """Initialize MinIO client."""
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure

        # Configure boto3 client for MinIO
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if secure else 'http'}://{endpoint}",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",  # MinIO doesn't care about region
        )

        logger.info(f"MinIO client configured for {endpoint}")

    def wait_for_service(self, timeout: int = 60, retry_interval: int = 2) -> bool:
        """
        Wait for MinIO service to be ready.

        Args:
            timeout: Maximum time to wait in seconds
            retry_interval: Time between retries in seconds

        Returns:
            True if service is ready, False otherwise
        """
        start_time = time.time()
        attempt = 0

        logger.info(f"Waiting for MinIO service to be ready (timeout: {timeout}s)")

        while time.time() - start_time < timeout:
            attempt += 1
            try:
                # Try to list buckets as a health check
                self.s3_client.list_buckets()
                logger.success(f"MinIO service is ready (attempt {attempt})")
                return True
            except (ClientError, EndpointConnectionError) as e:
                logger.debug(f"Attempt {attempt} failed: {e}")
                time.sleep(retry_interval)

        logger.error(f"MinIO service did not become ready within {timeout}s")
        return False

    def create_bucket(self, bucket_name: str) -> bool:
        """
        Create a bucket if it doesn't exist.

        Args:
            bucket_name: Name of the bucket to create

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if bucket already exists
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Bucket '{bucket_name}' already exists")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                # Bucket doesn't exist, create it
                try:
                    self.s3_client.create_bucket(Bucket=bucket_name)
                    logger.success(f"Created bucket '{bucket_name}'")
                    return True
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket '{bucket_name}': {create_error}")
                    return False
            else:
                logger.error(f"Error checking bucket '{bucket_name}': {e}")
                return False

    def upload_file(
        self, local_path: Path, bucket_name: str, object_key: str
    ) -> bool:
        """
        Upload a file to MinIO.

        Args:
            local_path: Path to local file
            bucket_name: Target bucket name
            object_key: Object key (path) in the bucket

        Returns:
            True if successful, False otherwise
        """
        try:
            if not local_path.exists():
                logger.error(f"Local file not found: {local_path}")
                return False

            self.s3_client.upload_file(
                str(local_path),
                bucket_name,
                object_key,
            )
            logger.success(
                f"Uploaded {local_path.name} to s3://{bucket_name}/{object_key}"
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False

    def verify_file(self, bucket_name: str, object_key: str) -> bool:
        """
        Verify that a file exists in MinIO.

        Args:
            bucket_name: Bucket name
            object_key: Object key

        Returns:
            True if file exists, False otherwise
        """
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            size = response.get("ContentLength", 0)
            logger.info(f"Verified s3://{bucket_name}/{object_key} ({size} bytes)")
            return True
        except ClientError as e:
            logger.error(f"File verification failed for s3://{bucket_name}/{object_key}: {e}")
            return False


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
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

    logger.info("Starting MinIO setup for CI/CD")
    logger.info(f"Endpoint: {endpoint}")
    logger.info(f"Secure: {secure}")

    # Initialize MinIO client
    minio = MinIOSetup(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )

    # Wait for MinIO to be ready
    if not minio.wait_for_service(timeout=60):
        logger.error("MinIO service is not available")
        sys.exit(1)

    # Create test buckets
    buckets = ["test-logs", "test-checkpoints", "test-output"]
    for bucket in buckets:
        if not minio.create_bucket(bucket):
            logger.error(f"Failed to create bucket: {bucket}")
            sys.exit(1)

    # Get fixtures directory
    project_root = Path(__file__).parent.parent.parent
    fixtures_dir = project_root / "tests" / "fixtures"

    if not fixtures_dir.exists():
        logger.error(f"Fixtures directory not found: {fixtures_dir}")
        sys.exit(1)

    # Upload test log files to various paths
    test_files = [
        (fixtures_dir / "slurm_oom.log", "test-logs", "slurm/job123456.log"),
        (fixtures_dir / "slurm_timeout.log", "test-logs", "slurm/job789012.log"),
        (fixtures_dir / "application_error.log", "test-logs", "app/data_processor.log"),
        # Add duplicates in different buckets for testing
        (fixtures_dir / "slurm_oom.log", "test-checkpoints", "logs/oom_error.log"),
        (fixtures_dir / "slurm_timeout.log", "test-output", "failures/timeout.log"),
    ]

    success = True
    for local_path, bucket, key in test_files:
        if not minio.upload_file(local_path, bucket, key):
            success = False

    # Verify all uploads
    logger.info("Verifying uploaded files...")
    for local_path, bucket, key in test_files:
        if not minio.verify_file(bucket, key):
            success = False

    if success:
        logger.success("MinIO setup completed successfully")
        sys.exit(0)
    else:
        logger.error("MinIO setup completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
