# Security Review Report: autosubmit-scan

**Review Date:** 2025-10-20
**Reviewer:** Security Engineer (Claude)
**Project Version:** 0.1.0 (Pre-release)

---

## Executive Summary

This security review identified **3 Critical**, **4 High**, **5 Medium**, and **3 Low** priority security concerns that should be addressed before public release. The project has good foundational security practices (environment variable-based credential management, .gitignore configuration) but lacks important security controls around arbitrary code execution, input validation, and security documentation.

**Recommendation:** Address all Critical and High priority issues before release. Medium priority issues should be documented in release notes. Low priority issues can be tracked for future releases.

---

## Critical Severity Issues (Blocks Release)

### 1. Arbitrary Code Execution via Callable Pattern Matchers

**Severity:** CRITICAL
**Component:** `src/matching/callable_loader.py`, `src/matching/pattern_matcher.py`

**Issue:**
The system allows loading and executing arbitrary Python code via the `callable` pattern type. While documented, there are NO security controls preventing malicious catalog files from executing dangerous code.

**Attack Scenario:**
```yaml
# Malicious catalog
errors:
  backdoor:
    pattern:
      type: "callable"
      pattern: "os:system"  # Could execute shell commands
    files: ["/etc/passwd"]
```

**Current Code:**
```python
# src/matching/callable_loader.py:46
module = importlib.import_module(module_path)  # No restrictions
func = getattr(module, function_name)  # No validation
```

**Risk:**
- Remote catalogs from GitHub can contain malicious callables
- No sandboxing or permission checks
- Could lead to: data exfiltration, system compromise, lateral movement

**Recommended Fixes:**
1. **Implement a whitelist of allowed modules** for callable patterns
2. **Add security warnings** when loading catalogs with callable patterns
3. **Require explicit user confirmation** for remote catalogs with callables
4. **Consider removing callable pattern support** or restricting to trusted catalogs only
5. **Add code signing verification** for catalogs with callables

**Code Changes Needed:**
```python
# Add to callable_loader.py
ALLOWED_MODULES = {
    "examples.custom_matchers",
    "examples.custom_conditions",
    # User-defined allowlist
}

def load_callable(callable_string: str, allow_arbitrary=False) -> Callable:
    module_path, function_name = callable_string.split(":")

    if not allow_arbitrary and module_path not in ALLOWED_MODULES:
        raise SecurityError(
            f"Module '{module_path}' is not in allowed modules list. "
            f"Set allow_arbitrary=True to bypass (not recommended for untrusted catalogs)."
        )
    # ... rest of implementation
```

---

### 2. Arbitrary Code Execution via Custom Conditions

**Severity:** CRITICAL
**Component:** `src/orchestration/conditions.py`

**Issue:**
Similar to callable patterns, the railway pattern's `CUSTOM` condition type allows loading arbitrary Python functions without restrictions.

**Current Code:**
```python
# src/orchestration/conditions.py:194-200
def _evaluate_custom(self, condition: ConditionSpec, error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    try:
        func = load_callable(condition.callable)  # No security check
        result = func(error_match, catalog)
        return bool(result)
    except Exception:
        return False
```

**Risk:**
- Custom conditions have access to full ErrorMatch and ErrorCatalog objects
- Could extract sensitive data from file paths or matched content
- Error suppression (bare except) hides security violations

**Recommended Fixes:**
1. Apply same whitelist approach as callable patterns
2. **Remove bare except** - log security violations
3. Add audit logging for custom condition execution
4. Consider restricting custom condition capabilities

---

### 3. Subprocess Command Injection Risk

**Severity:** CRITICAL
**Component:** `src/cli/commands/dag.py:386`

**Issue:**
On Windows, subprocess uses `shell=True` which is vulnerable to command injection.

**Current Code:**
```python
# src/cli/commands/dag.py:386
subprocess.run(["start", str(file_path)], shell=True)
```

**Risk:**
- If `file_path` contains special characters or is user-controlled, could lead to command injection
- `shell=True` on Windows executes via cmd.exe, allowing chaining with `&`, `|`, etc.

**Recommended Fix:**
```python
# Use os.startfile on Windows (no shell)
if sys.platform == "win32":
    import os
    os.startfile(str(file_path))
else:
    # Keep existing behavior for other platforms
    subprocess.run(["open", str(file_path)], shell=False)
```

---

## High Severity Issues (Should Fix Before Release)

### 4. Missing Security Documentation

**Severity:** HIGH
**Component:** Project root

**Issue:**
No SECURITY.md file with responsible disclosure policy. No security warnings in documentation about risks of:
- Loading untrusted catalogs from GitHub
- Using callable patterns
- Remote file access with credentials

**Recommended Fix:**
Create `SECURITY.md` with:
- Responsible disclosure process and contact information
- Security considerations for users
- Known limitations and attack surface
- Credential management best practices

---

### 5. Credentials in URLs - FTP Pattern

**Severity:** HIGH
**Component:** Documentation and validation

**Issue:**
The URI validation and documentation encourage embedding credentials in URLs:

```yaml
# docs/USER_GUIDE.md:479
files:
  - "ftp://user:password@ftp.example.com/logs/**/*.log"
```

**Risk:**
- URLs get logged (see scan.py line 66)
- URLs stored in catalog YAML files
- URLs may be committed to version control
- URLs shared in reports

**Current Logging:**
```python
# src/cli/commands/scan.py:66
logger.info(f"Loading catalog from {catalog}")  # Logs full path with credentials
```

**Recommended Fixes:**
1. **Sanitize URLs in all log statements** - mask credentials
2. **Warn against credential-in-URL pattern** in documentation
3. **Recommend environment-based authentication** for all protocols
4. Add URL sanitization utility:

```python
def sanitize_url_for_logging(url: str) -> str:
    """Remove credentials from URL for safe logging."""
    parsed = urllib.parse.urlparse(url)
    if parsed.password:
        netloc = parsed.netloc.replace(f":{parsed.password}", ":***")
        return parsed._replace(netloc=netloc).geturl()
    return url
```

---

### 6. GitHub Token Logging Risk

**Severity:** HIGH
**Component:** `src/domain/catalog.py:94`

**Issue:**
Username is logged when using GitHub authentication, potentially leaking sensitive information in shared logs.

**Current Code:**
```python
logger.debug(f"Using authenticated GitHub access as {github_username}")
```

**Recommendation:**
While username is less sensitive than token, consider:
1. Logging only in TRACE mode, not DEBUG
2. Using a generic message: "Using authenticated GitHub access"
3. Add warning about log security in documentation

---

### 7. No SSH Host Key Verification Documented

**Severity:** HIGH
**Component:** Remote access (fsspec/paramiko)

**Issue:**
Documentation doesn't mention SSH host key verification. fsspec with paramiko might auto-accept host keys (depending on configuration), creating MITM vulnerability.

**Risk:**
- Man-in-the-middle attacks on SSH connections
- Credential theft
- Malicious log file injection

**Recommended Fixes:**
1. Document SSH host key verification requirements
2. Add configuration for `~/.ssh/known_hosts` requirement
3. Consider adding host key pinning for production use
4. Test and document StrictHostKeyChecking behavior

---

## Medium Severity Issues (Document Risk)

### 8. Path Traversal in File URIs

**Severity:** MEDIUM
**Component:** `src/domain/validation.py`

**Issue:**
While file URIs are validated for format, there's no protection against path traversal attacks:

```yaml
files:
  - "/legitimate/path/../../etc/passwd"
  - "ssh://host:/../../../root/.ssh/id_rsa"
```

**Mitigation:**
The workflow uses fsspec which provides some protection, but:
1. Add path normalization and traversal checks
2. Document that file access uses same permissions as running user
3. Warn about running as privileged user

**Recommended Addition:**
```python
def validate_uri(uri: str) -> str:
    # ... existing validation ...

    # Check for path traversal
    if ".." in uri:
        logger.warning(f"Path traversal pattern detected in URI: {uri}")

    return uri
```

---

### 9. Template Injection in Jinja2 Variable Rendering

**Severity:** MEDIUM
**Component:** `src/domain/catalog.py:308`, `src/domain/variable_extractor.py:240`

**Issue:**
File paths and variable values are rendered with Jinja2 without input sanitization. Could allow template injection if variables come from untrusted sources.

**Current Code:**
```python
# src/domain/catalog.py:308
template = Template(file_uri)
rendered = template.render(**variables)
```

**Attack Scenario:**
If a variable extractor reads from an attacker-controlled file:
```yaml
variables:
  expid:
    source: file
    path: /tmp/attacker_controlled.txt
    # File contains: {{ config.__class__.__init__.__globals__['os'].system('evil') }}
```

**Risk Level:** Medium because:
- Variables typically come from local files the user controls
- Remote variable extraction requires network access user already has
- But could be chained with other vulnerabilities

**Recommended Fixes:**
1. Use `SandboxedEnvironment` instead of `Template`:
```python
from jinja2.sandbox import SandboxedEnvironment
env = SandboxedEnvironment()
template = env.from_string(file_uri)
```

2. Document that variable sources should be trusted
3. Add configuration to disable variable rendering for security-sensitive deployments

---

### 10. No Dependency Vulnerability Scanning

**Severity:** MEDIUM
**Component:** CI/CD pipeline

**Issue:**
No automated dependency vulnerability scanning in place. Current dependencies include:
- `fsspec 2025.9.0` (very recent, good)
- `paramiko 4.0.0` (recent)
- `asyncssh 2.21.1` (recent)
- `pyyaml 6.0.3` (recent)
- `jinja2 3.1.6` (recent)

**Recommendation:**
1. Add GitHub Dependabot for automated dependency updates
2. Add `pip-audit` or `safety` to CI pipeline
3. Add Snyk or similar scanning
4. Document dependency update policy

**Proposed GitHub Action:**
```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]
jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit
```

---

### 11. Snakemake Workflow Security

**Severity:** MEDIUM
**Component:** Snakemake workflow execution

**Issue:**
Snakemake workflows can execute arbitrary Python code in rules. While this is a documented Snakemake feature, it increases attack surface if malicious catalogs could modify workflow behavior.

**Current Implementation:**
- Snakefile is embedded in the package (good)
- Cannot be overridden by catalogs (good)
- Uses subprocess for Python execution (potential isolation)

**Recommendation:**
1. Document that Snakefile is trusted and cannot be modified by catalogs
2. Review Snakefile for any dynamic code execution based on catalog data
3. Consider running Snakemake in restricted mode if available

---

### 12. No Rate Limiting for Remote Access

**Severity:** MEDIUM
**Component:** Remote file access via fsspec

**Issue:**
No rate limiting or connection pooling documented for remote operations. Could lead to:
- DOS of remote systems
- Account lockouts
- IP bans

**Recommendation:**
1. Document rate limiting considerations
2. Add configurable delays between remote operations
3. Document connection pool settings for S3/SFTP
4. Add `--rate-limit` flag to scan command

---

## Low Severity Issues (Consider for Future Releases)

### 13. Error Suppression Hides Security Issues

**Severity:** LOW
**Component:** Multiple files

**Issue:**
Broad exception handling suppresses security-relevant errors:

```python
# src/orchestration/conditions.py:198
except Exception:
    return False  # Silently fails
```

**Recommendation:**
1. Log exceptions at WARNING level minimum
2. Distinguish between expected errors and security violations
3. Add metrics for security-relevant errors

---

### 14. No Audit Logging

**Severity:** LOW
**Component:** Overall architecture

**Issue:**
No audit trail for security-sensitive operations:
- Loading callable patterns
- Executing custom conditions
- Remote file access
- Variable extraction from remote sources

**Recommendation:**
For future release, add structured audit logging:
```python
audit_logger.info("callable_loaded", extra={
    "module": module_path,
    "function": function_name,
    "catalog": catalog_path,
    "user": os.getenv("USER"),
    "timestamp": datetime.utcnow()
})
```

---

### 15. Secrets in Test Files

**Severity:** LOW
**Component:** Test fixtures

**Issue:**
Test credentials are hardcoded but clearly marked as test credentials:
- `minioadmin` for MinIO
- `testpass` for SFTP/FTP

This is acceptable for testing but should be documented as **test-only**.

**Recommendation:**
1. Add comment in test fixtures: "# TEST CREDENTIALS ONLY - DO NOT USE IN PRODUCTION"
2. Document rotating test credentials in CI environment
3. Consider using random credentials in integration tests

---

## Security Best Practices - Implemented ✓

The following security practices are correctly implemented:

1. **Credentials from Environment Variables** ✓
   - `GITHUB_TOKEN`, `AWS_SECRET_ACCESS_KEY`, etc.
   - No hardcoded credentials in source code

2. **.gitignore Configuration** ✓
   - `.env` files excluded
   - Environment files properly ignored

3. **Input Validation** ✓
   - URI format validation
   - Semver validation
   - Callable string format validation
   - Field type validation with Pydantic

4. **Recent Dependencies** ✓
   - Using modern, actively maintained versions
   - Pydantic v2 (security improvements)
   - Python 3.12+ (latest security patches)

5. **Subprocess Security** ✓ (mostly)
   - `capture_output=True` prevents console injection
   - `shell=False` on most platforms (except Windows issue above)
   - Command arrays used instead of string concatenation

---

## Recommended Security Enhancements

### Immediate (Pre-Release)

1. **Create SECURITY.md** with responsible disclosure policy
2. **Add callable pattern whitelist** with security warnings
3. **Fix Windows subprocess shell=True vulnerability**
4. **Sanitize URLs in all log output**
5. **Add security warnings to documentation**

### Short-term (v0.2.0)

1. **Implement audit logging** for security-sensitive operations
2. **Add dependency vulnerability scanning** to CI
3. **Use Jinja2 SandboxedEnvironment** for template rendering
4. **Document SSH host key verification** requirements
5. **Add path traversal checks** to URI validation

### Long-term (v1.0.0)

1. **Code signing for catalogs** with callables
2. **Catalog permission model** (trust levels)
3. **Sandboxed callable execution** (containers/VMs)
4. **Rate limiting framework** for remote operations
5. **Security audit mode** with detailed logging

---

## Compliance Considerations

### GDPR / Data Protection

- **Issue:** Logs may contain file paths with personal information
- **Recommendation:** Document data minimization practices, add PII redaction for logs

### EU Cybersecurity Act

- **Issue:** No security certification or attestation
- **Recommendation:** Consider ISO 27001 controls alignment for future certification

### DestinE Requirements

- **Issue:** Handling sensitive climate model data
- **Recommendation:** Add classification labels, implement data handling controls

---

## Security Testing Recommendations

### Required Before Release

1. **Static Analysis:**
   - Run Bandit: `bandit -r src/`
   - Run Semgrep with security rules
   - Review all subprocess calls

2. **Dependency Scanning:**
   - Run `pip-audit`
   - Check for known CVEs

3. **Manual Security Testing:**
   - Test malicious catalog loading
   - Test credential exposure in logs
   - Test path traversal attempts
   - Test template injection

### Recommended for Future

1. Penetration testing by third party
2. Fuzzing of catalog parser
3. Integration with SIEM for audit logs
4. Regular security audits (quarterly)

---

## Conclusion

The autosubmit-scan project has a solid foundation but requires addressing critical arbitrary code execution risks before public release. The main security concerns stem from the flexible design (callable patterns, custom conditions) which, while powerful, introduce significant attack surface.

**Release Recommendation:**
- **Block release** until Critical issues (#1, #2, #3) are addressed
- **Strong recommendation** to fix High issues (#4-#7) before release
- Document Medium issues in release notes
- Track Low issues for future releases

**Timeline Estimate:**
- Critical fixes: 2-3 days
- High priority fixes: 3-5 days
- Documentation: 1-2 days
- Security testing: 2-3 days
- **Total: ~2 weeks** for secure release

---

## Contact

For questions about this security review, contact the security team or create a private security advisory on GitHub.

**Review Version:** 1.0
**Next Review:** After critical issues are addressed
