# CI Setup Scripts

This directory contains setup scripts for configuring remote services in CI/CD environments.

## Scripts

### `setup_minio.py`

Configures MinIO (S3-compatible storage) for testing.

**What it does:**
1. Waits for MinIO service to be ready (with retries)
2. Creates test buckets: `test-logs`, `test-checkpoints`, `test-output`
3. Uploads test fixture log files to various paths
4. Verifies all uploads succeeded

**Environment Variables:**
- `MINIO_ENDPOINT`: MinIO server endpoint (default: localhost:9000)
- `MINIO_ACCESS_KEY`: Access key (default: minioadmin)
- `MINIO_SECRET_KEY`: Secret key (default: minioadmin)
- `MINIO_SECURE`: Use HTTPS (default: false)

**Usage:**
```bash
pixi run ci-setup-minio
```

**Exit codes:**
- 0: Success
- 1: Failure (service not available or upload failed)

---

### `setup_sftp.py`

Configures SFTP server for testing.

**What it does:**
1. Waits for SFTP service to be ready (with retries)
2. Creates test directory structure: `upload/logs/slurm`, `upload/logs/app`, etc.
3. Uploads test fixture log files to various paths
4. Verifies all uploads succeeded

**Environment Variables:**
- `SFTP_HOST`: SFTP server host (default: localhost)
- `SFTP_PORT`: SFTP server port (default: 2222)
- `SFTP_USER`: SFTP username (default: testuser)
- `SFTP_PASSWORD`: SFTP password (default: testpass)

**Usage:**
```bash
pixi run ci-setup-sftp
```

**Exit codes:**
- 0: Success
- 1: Failure (service not available or upload failed)

---

### `setup_ftp.py`

Configures FTP server for testing.

**What it does:**
1. Waits for FTP service to be ready (with retries)
2. Creates test directory structure: `logs/slurm`, `logs/app`, etc.
3. Uploads test fixture log files to various paths
4. Verifies all uploads succeeded

**Environment Variables:**
- `FTP_HOST`: FTP server host (default: localhost)
- `FTP_PORT`: FTP server port (default: 2121)
- `FTP_USER`: FTP username (default: testuser)
- `FTP_PASSWORD`: FTP password (default: testpass)

**Usage:**
```bash
pixi run ci-setup-ftp
```

**Exit codes:**
- 0: Success
- 1: Failure (service not available or upload failed)

---

## Common Features

All scripts include:

- **Retry logic**: Automatic retries with exponential backoff
- **Health checks**: Wait for service to be ready before proceeding
- **Detailed logging**: Uses loguru for structured, colored logging
- **Error handling**: Graceful error handling with informative messages
- **Verification**: Verifies all uploads succeeded before exiting

## Dependencies

These scripts require:
- `boto3`: AWS SDK for Python (MinIO/S3)
- `paramiko`: SSH/SFTP client library
- `loguru`: Advanced logging library
- `fsspec`: Filesystem spec (optional, for higher-level APIs)

All dependencies are included in `pixi.toml`.

## Running Locally

To test these scripts locally with Docker containers:

1. **Start MinIO:**
   ```bash
   docker run -d -p 9000:9000 -p 9001:9001 \
     -e MINIO_ROOT_USER=minioadmin \
     -e MINIO_ROOT_PASSWORD=minioadmin \
     minio/minio server /data --console-address ":9001"
   ```

2. **Start SFTP:**
   ```bash
   docker run -d -p 2222:22 \
     -e SFTP_USERS=testuser:testpass:1001 \
     atmoz/sftp
   ```

3. **Start FTP:**
   ```bash
   docker run -d -p 2121:21 -p 21000-21010:21000-21010 \
     -e USERS=testuser|testpass \
     -e ADDRESS=localhost \
     delfer/alpine-ftp-server
   ```

4. **Run setup scripts:**
   ```bash
   pixi run ci-setup-minio
   pixi run ci-setup-sftp
   pixi run ci-setup-ftp
   ```

## Troubleshooting

**"Service not available" error:**
- Ensure the service container is running
- Check port conflicts (ports 9000, 2121, 2222)
- Verify firewall rules allow connections
- Increase timeout in script if service is slow to start

**"Authentication failed" error:**
- Verify credentials match environment variables
- Check service configuration accepts the credentials
- For SFTP: ensure user is properly created with `SFTP_USERS` env var

**"Upload failed" error:**
- Check permissions on remote directory
- Verify network connectivity
- Check disk space on remote service
- Review service logs for detailed error messages

**"File not found" error:**
- Ensure test fixtures exist in `tests/fixtures/`
- Verify project structure is correct
- Check file paths in script match actual locations

## Adding New Test Files

To add new test files to the setup scripts:

1. Add the file to `tests/fixtures/`
2. Update the `test_files` list in each setup script
3. Follow the pattern: `(local_path, bucket/directory, remote_key/path)`
4. Run the script to verify it works

## Security Notes

These scripts are designed for CI/CD testing only and should NOT be used in production:

- Credentials are passed via environment variables
- No encryption or certificate validation for local testing
- Default credentials are well-known (minioadmin, testuser, etc.)
- Services are exposed on localhost without authentication hardening

For production use, implement:
- Secure credential management (AWS Secrets Manager, HashiCorp Vault, etc.)
- TLS/SSL encryption for all connections
- Strong authentication and authorization
- Network isolation and firewalls
- Audit logging and monitoring
