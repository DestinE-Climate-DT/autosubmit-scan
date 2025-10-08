# GitHub Actions Workflows

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows

### `test.yml` - Test Suite

Comprehensive test suite that runs on every push and pull request.

**Features:**
- Runs on Ubuntu latest
- Tests multiple remote file protocols: S3 (MinIO), SFTP, FTP
- Generates coverage reports
- Uploads artifacts to GitHub

**Service Containers:**
- **MinIO**: S3-compatible object storage (port 9000)
- **SFTP**: OpenSSH server using `atmoz/sftp` (port 2222)
- **FTP**: FTP server using `delfer/alpine-ftp-server` (port 2121)

**Test Stages:**
1. Service health verification
2. Setup test data on all services
3. Run unit tests
4. Run integration tests (with remote services)
5. Run end-to-end tests
6. Generate and upload coverage reports

**Environment Variables:**

MinIO/S3:
- `MINIO_ENDPOINT`: MinIO server endpoint (default: localhost:9000)
- `MINIO_ACCESS_KEY`: Access key (default: minioadmin)
- `MINIO_SECRET_KEY`: Secret key (default: minioadmin)
- `MINIO_SECURE`: Use HTTPS (default: false)

SFTP:
- `SFTP_HOST`: SFTP server host (default: localhost)
- `SFTP_PORT`: SFTP server port (default: 2222)
- `SFTP_USER`: SFTP username (default: testuser)
- `SFTP_PASSWORD`: SFTP password (default: testpass)

FTP:
- `FTP_HOST`: FTP server host (default: localhost)
- `FTP_PORT`: FTP server port (default: 2121)
- `FTP_USER`: FTP username (default: testuser)
- `FTP_PASSWORD`: FTP password (default: testpass)

## Running Locally

While you can't run the exact GitHub Actions workflow locally, you can:

1. **Run tests locally without remote services:**
   ```bash
   pixi run test-unit
   ```

2. **Run integration tests with local remote services:**

   First, start the services using Docker Compose (create a `docker-compose.yml` if needed):
   ```bash
   docker-compose up -d
   ```

   Then run setup scripts:
   ```bash
   pixi run ci-setup-minio
   pixi run ci-setup-sftp
   pixi run ci-setup-ftp
   ```

   Finally, run integration tests:
   ```bash
   pixi run test-integration
   ```

3. **Use act to run GitHub Actions locally:**
   ```bash
   # Install act: https://github.com/nektos/act
   brew install act  # macOS

   # Run the workflow
   act push
   ```

## CI/CD Best Practices

This workflow follows GitHub Actions best practices:

1. **Service containers** for isolated test environments
2. **Health checks** to ensure services are ready
3. **Artifact uploads** for debugging and archival
4. **Coverage reporting** for code quality metrics
5. **Matrix builds** ready to test multiple Python versions
6. **Caching** with Pixi for faster builds
7. **Secret management** via GitHub Secrets
8. **OIDC authentication** ready for cloud deployments

## Adding New Tests

When adding new test categories:

1. Add a new pytest marker in `tests/conftest.py`
2. Update `pytest.ini` with the marker definition
3. Add a new task in `pixi.toml` if needed
4. Add a new step in the workflow to run the tests

## Troubleshooting

**Services not healthy:**
- Check service logs in the Actions run
- Verify port conflicts
- Ensure health check commands are correct

**Tests failing in CI but passing locally:**
- Check environment variable differences
- Verify service configuration matches
- Check for timing/race conditions

**Coverage reports not uploading:**
- Ensure `CODECOV_TOKEN` secret is set in repository settings
- Check that coverage files are generated in the correct location
