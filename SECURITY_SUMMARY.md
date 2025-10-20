# Security Review - Executive Summary

**Review Date:** 2025-10-20
**Status:** Pre-release security review completed
**Recommendation:** Address critical issues before public release

---

## Quick Summary

📊 **Issues Found:**
- 🔴 **3 Critical** (blocks release)
- 🟠 **4 High** (should fix)
- 🟡 **5 Medium** (document)
- ⚪ **3 Low** (future releases)

⏱️ **Estimated Time to Secure Release:** 2 weeks

---

## Critical Issues (MUST FIX)

### 1. Arbitrary Code Execution via Callable Patterns
**File:** `src/matching/callable_loader.py`

**Problem:** Catalogs can execute any Python code without restrictions.

**Fix:** Add whitelist of allowed modules:
```python
ALLOWED_MODULES = {"examples.custom_matchers", "examples.custom_conditions"}
# Reject modules not in whitelist
```

---

### 2. Arbitrary Code Execution via Custom Conditions
**File:** `src/orchestration/conditions.py`

**Problem:** Railway pattern custom conditions can execute any code.

**Fix:** Apply same whitelist approach, add audit logging.

---

### 3. Windows Command Injection
**File:** `src/cli/commands/dag.py:386`

**Problem:** `shell=True` on Windows allows command injection.

**Fix:**
```python
# Replace this:
subprocess.run(["start", str(file_path)], shell=True)

# With this:
import os
os.startfile(str(file_path))  # No shell needed
```

---

## High Priority Issues (SHOULD FIX)

### 4. Missing Security Documentation
**Fix:** Create `SECURITY.md` with responsible disclosure policy ✅ (DONE)

### 5. Credentials in Log Output
**Files:** `src/cli/commands/scan.py:66`, various

**Problem:** URLs with passwords get logged:
```
logger.info(f"Loading catalog from ftp://user:pass@host/path")
```

**Fix:** Sanitize URLs before logging:
```python
def sanitize_url(url):
    # Mask passwords in URLs
    return re.sub(r':([^@]+)@', ':***@', url)
```

### 6. GitHub Username Logging
**File:** `src/domain/catalog.py:94`

**Fix:** Remove username from log message or move to TRACE level.

### 7. No SSH Host Key Verification Documentation
**Fix:** Document SSH security requirements in SECURITY.md ✅ (DONE)

---

## Action Items by Priority

### Immediate (Before Release)

1. ✅ Create `SECURITY.md` - DONE
2. ⬜ Implement callable module whitelist
3. ⬜ Fix Windows subprocess vulnerability
4. ⬜ Add URL sanitization to all log statements
5. ⬜ Add security warnings to documentation

### Code Changes Needed

**File:** `src/matching/callable_loader.py`
```python
# Add at top of file
ALLOWED_MODULES = {
    "examples.custom_matchers",
    "examples.custom_conditions",
}

def load_callable(callable_string: str, allow_arbitrary: bool = False) -> Callable:
    """Load callable with security checks."""
    if ":" not in callable_string:
        raise ValueError(f"Invalid callable format: {callable_string}")

    module_path, function_name = callable_string.split(":", 1)

    # Security check
    if not allow_arbitrary and module_path not in ALLOWED_MODULES:
        raise SecurityError(
            f"Module '{module_path}' is not in allowed modules. "
            f"This is a security restriction. Allowed modules: {ALLOWED_MODULES}"
        )

    # Rest of existing implementation...
```

**File:** `src/cli/commands/dag.py`
```python
# Replace line 386
if sys.platform == "win32":
    import os
    os.startfile(str(file_path))  # No shell injection risk
elif sys.platform == "darwin":
    subprocess.run(["open", str(file_path)], shell=False)
elif sys.platform == "linux":
    subprocess.run(["xdg-open", str(file_path)], shell=False)
```

**New File:** `src/utils/security.py`
```python
import re
import urllib.parse

def sanitize_url_for_logging(url: str) -> str:
    """Remove sensitive credentials from URLs before logging."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.password:
            # Replace password with ***
            netloc = parsed.netloc.replace(f":{parsed.password}", ":***")
            sanitized = parsed._replace(netloc=netloc)
            return urllib.parse.urlunparse(sanitized)
    except:
        # Fallback: regex replacement
        return re.sub(r':([^:@]+)@', ':***@', url)
    return url
```

**Update All Log Statements:**
```python
# Before
logger.info(f"Loading catalog from {catalog}")

# After
from src.utils.security import sanitize_url_for_logging
logger.info(f"Loading catalog from {sanitize_url_for_logging(catalog)}")
```

---

## Testing Checklist

Before release, test:

- [ ] Load catalog with malicious callable pattern (should be blocked)
- [ ] Verify URL sanitization in logs
- [ ] Test Windows file opening (no shell injection)
- [ ] Run `bandit -r src/` (security linter)
- [ ] Run `pip-audit` (dependency vulnerabilities)
- [ ] Review all subprocess.run() calls
- [ ] Test with path traversal attempts
- [ ] Verify SSH host key checking

---

## Documentation Updates Needed

1. **README.md** - Add security warning section:
```markdown
## Security Notice

⚠️ **Important:** Only use error catalogs from trusted sources.

Catalogs with `callable` pattern types can execute arbitrary code.
See [SECURITY.md](SECURITY.md) for details.
```

2. **docs/USER_GUIDE.md** - Add security considerations:
- Credential management best practices
- Catalog trust model
- SSH host key verification

3. **examples/sample_catalog.yaml** - Add security comment:
```yaml
# SECURITY WARNING: Callable patterns execute arbitrary Python code.
# Only use callables from trusted sources. Prefer regex patterns when possible.
```

---

## CI/CD Additions

**New File:** `.github/workflows/security.yml`
```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install security tools
        run: |
          pip install bandit safety pip-audit

      - name: Run Bandit
        run: bandit -r src/ -f json -o bandit-report.json

      - name: Run pip-audit
        run: pip-audit --desc

      - name: Run Safety
        run: safety check --json
```

**Enable Dependabot:** `.github/dependabot.yml`
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

---

## Medium Priority Issues (Document)

These don't block release but should be documented in release notes:

1. **Path Traversal** - Document that file access uses user permissions
2. **Template Injection** - Use SandboxedEnvironment for Jinja2
3. **No Dependency Scanning** - Add to CI
4. **Snakemake Security** - Document workflow trust model
5. **No Rate Limiting** - Add to future roadmap

---

## Files Created

1. ✅ `SECURITY.md` - Comprehensive security policy and user guidance
2. ✅ `SECURITY_REVIEW.md` - Detailed technical security review
3. ✅ `SECURITY_SUMMARY.md` - This executive summary

---

## Next Steps

1. **Review** these findings with the team
2. **Prioritize** critical fixes for immediate implementation
3. **Assign** tasks to developers
4. **Test** security fixes thoroughly
5. **Document** security considerations in user-facing docs
6. **Release** when critical issues are addressed

**Estimated Timeline:**
- Critical fixes: 3-5 days
- Testing: 2-3 days
- Documentation: 1-2 days
- **Total: ~10 working days**

---

## Questions?

Contact: paul.gierz@awi.de

**Full Details:** See `SECURITY_REVIEW.md` for complete technical analysis.
