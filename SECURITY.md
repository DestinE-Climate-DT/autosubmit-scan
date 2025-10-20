# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of autosubmit-scan seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security issues by:

1. **Email:** Send details to `paul.gierz@awi.de` with subject line: `[SECURITY] autosubmit-scan vulnerability`
2. **GitHub Security Advisories:** Use the [GitHub Security Advisory](https://github.com/DestinE-Climate-DT/autosubmit-scan/security/advisories/new) feature (preferred)

### What to Include

Please include the following information in your report:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if available)
- Your contact information for follow-up

### Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 1 week
- **Fix Timeline:** Severity-dependent (see below)

### Severity Levels

| Severity | Response Time | Fix Timeline |
|----------|---------------|--------------|
| Critical | 24 hours      | 1-3 days     |
| High     | 48 hours      | 1-2 weeks    |
| Medium   | 1 week        | 1 month      |
| Low      | 2 weeks       | Next release |

### Disclosure Policy

- We follow **coordinated disclosure** principles
- We will work with you to understand and validate the issue
- Security fixes will be released ASAP based on severity
- Public disclosure will occur after a fix is available
- We will credit security researchers (unless they prefer anonymity)

---

## Security Considerations for Users

### Catalog Trust Model

**IMPORTANT:** Only use error catalogs from trusted sources.

#### Risk Factors

1. **Callable Pattern Matchers**
   - Catalogs can specify arbitrary Python code execution via `callable` pattern type
   - This code runs with your user's permissions
   - **Never load catalogs from untrusted sources if they contain callable patterns**

2. **Custom Conditions**
   - Railway pattern conditions can execute custom Python functions
   - These have access to matched error data and catalog contents
   - Same trust requirements as callable patterns

3. **Remote File Access**
   - Catalogs specify which files to scan (local or remote)
   - Scanning is performed with your credentials
   - Verify file URIs before running scans on production systems

#### Security Best Practices

**For Catalog Authors:**
- Avoid using `callable` pattern types unless absolutely necessary
- Prefer `regex` or `literal` patterns when possible
- Document all callable functions in your catalog
- Sign your catalogs cryptographically (future feature)

**For Catalog Users:**
- Review catalogs before use: `as-scan validate catalog.yaml`
- Check for `type: callable` patterns in YAML
- Use read-only credentials for remote file access
- Run scans with minimal privileges (not as root)
- Test catalogs in isolated environments first

### Credential Management

#### Recommended Practices

1. **Use Environment Variables** (REQUIRED)
   ```bash
   export GITHUB_TOKEN="ghp_..."
   export AWS_ACCESS_KEY_ID="..."
   export AWS_SECRET_ACCESS_KEY="..."
   ```

2. **Never Embed Credentials in Catalogs**
   ```yaml
   # BAD - credentials exposed in YAML
   files:
     - "ftp://user:password@host/path"

   # GOOD - use environment-based auth
   files:
     - "s3://bucket/path"  # Uses AWS_* env vars
   ```

3. **SSH Configuration Files**
   ```bash
   # Use ~/.ssh/config for SSH/SFTP connections
   # Example ~/.ssh/config:
   Host myserver
     HostName server.example.com
     User myuser
     IdentityFile ~/.ssh/id_rsa
     StrictHostKeyChecking yes
   ```

4. **Credential Rotation**
   - Rotate credentials regularly
   - Use short-lived tokens when possible
   - Revoke credentials immediately if compromised

5. **Least Privilege**
   - Use read-only credentials for scanning
   - Restrict file access to necessary directories
   - Use dedicated service accounts (not personal credentials)

### SSH Security

#### Host Key Verification

Always verify SSH host keys to prevent MITM attacks:

1. **Add hosts to known_hosts:**
   ```bash
   ssh-keyscan hostname >> ~/.ssh/known_hosts
   ```

2. **Use StrictHostKeyChecking:**
   ```
   # In ~/.ssh/config
   Host *
     StrictHostKeyChecking yes
   ```

3. **Verify fingerprints** before first connection

### Network Security

#### Remote Scanning Considerations

1. **Firewall Rules**
   - Ensure outbound connectivity to required hosts
   - Document required ports (SSH: 22, SFTP: 22, FTP: 21, FTPS: 990)

2. **VPN/Bastion Hosts**
   - Use VPN for accessing internal networks
   - Configure SSH bastion hosts in `~/.ssh/config`:
     ```
     Host internal-server
       ProxyJump bastion.example.com
     ```

3. **TLS/SSL Verification**
   - Verify SSL certificates for HTTPS/FTPS
   - Avoid disabling certificate validation

### Data Protection

#### Sensitive Data in Logs

Logs may contain:
- File paths (could reveal directory structure)
- Matched error text (could contain sensitive info)
- Hostnames and IP addresses

**Recommendations:**
- Review logs before sharing
- Redact sensitive information
- Use log aggregation with access controls
- Enable encryption for log storage

#### GDPR Considerations

If processing personal data:
- Document legal basis for processing
- Implement data minimization
- Provide data deletion capabilities
- Maintain audit trail of access

---

## Known Limitations

### Current Security Constraints

1. **No Code Sandboxing**
   - Callable patterns execute with full user privileges
   - No isolation or containerization
   - **Mitigation:** Only use trusted catalogs

2. **No Catalog Signing**
   - Cannot verify catalog authenticity
   - **Mitigation:** Use checksums, verify sources
   - **Roadmap:** Code signing in v1.0

3. **Limited Audit Logging**
   - Basic logging of operations
   - No structured audit trail
   - **Roadmap:** Enhanced audit logging in v0.2

4. **No Rate Limiting**
   - Remote operations not rate-limited
   - Could overwhelm remote systems
   - **Mitigation:** Use `--cores` to limit parallelism

### Future Security Enhancements

See our [Security Roadmap](docs/SECURITY_ROADMAP.md) (coming soon) for planned improvements.

---

## Security Architecture

### Threat Model

**Assets:**
- User credentials (SSH keys, API tokens)
- Scanned log files (may contain sensitive data)
- Scan results (error matches, file paths)
- Execution environment (file system, network)

**Threat Actors:**
- Malicious catalog authors
- Compromised catalog repositories
- Network attackers (MITM)
- Malicious log files (code injection via templates)

**Attack Vectors:**
1. Arbitrary code execution via callable patterns
2. Credential theft via logging/reports
3. Path traversal via file URIs
4. Template injection via Jinja2
5. Network MITM via unverified SSH
6. Dependency vulnerabilities

### Security Controls

**Implemented:**
- Environment-based credential management
- Input validation (URIs, versions, callables)
- Type safety (Pydantic models)
- Subprocess security (no shell injection, mostly)
- Recent dependencies

**In Progress:**
- Callable pattern whitelisting
- Enhanced audit logging
- Dependency vulnerability scanning

**Planned:**
- Catalog code signing
- Sandboxed execution environment
- Rate limiting framework
- Security certification

---

## Compliance

### Regulatory Considerations

#### EU Regulations
- **GDPR:** Data protection for EU citizens
- **NIS2 Directive:** Cybersecurity for critical infrastructure
- **EU Cybersecurity Act:** Product security requirements

#### DestinE-Specific
- Data classification requirements
- Access control policies
- Audit trail requirements

### Security Standards

We aim to align with:
- **OWASP Top 10** vulnerability prevention
- **CWE Top 25** weakness mitigation
- **NIST Cybersecurity Framework** controls
- **ISO 27001** information security management (future)

---

## Security Updates

### Notification Channels

Stay informed about security updates:

1. **GitHub Security Advisories:** https://github.com/DestinE-Climate-DT/autosubmit-scan/security/advisories
2. **Changelog:** Check `CHANGELOG.md` for security fixes
3. **Releases:** Monitor GitHub releases for security patches

### Applying Updates

```bash
# Update to latest version
pixi update
pixi install

# Or with pip
pip install --upgrade autosubmit-scan
```

Always review release notes for breaking changes or security-relevant updates.

---

## Security Testing

### For Contributors

Before submitting pull requests:

1. **Run security linters:**
   ```bash
   bandit -r src/
   safety check
   ```

2. **Review for common vulnerabilities:**
   - SQL injection (N/A - no database)
   - Command injection (check subprocess calls)
   - Path traversal (check file operations)
   - Credential exposure (check logging)

3. **Test with malicious inputs:**
   - Invalid YAML
   - Path traversal attempts
   - Large files
   - Malformed URIs

### For Security Researchers

We welcome security research! Please:
1. Follow responsible disclosure
2. Don't test on production systems without permission
3. Provide clear reproduction steps
4. Suggest mitigations when possible

---

## Contact

**Security Contact:** paul.gierz@awi.de
**Project Maintainer:** Dr. Paul Gierz (Alfred Wegener Institute)
**ORCID:** 0000-0002-4512-087X

For non-security issues, please use GitHub Issues: https://github.com/DestinE-Climate-DT/autosubmit-scan/issues

---

**Document Version:** 1.0
**Last Updated:** 2025-10-20
**Next Review:** 2026-01-20 (or after major release)
