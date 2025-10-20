# Common Errors and Troubleshooting

This guide helps you fix the most common problems when using autosubmit-scan.

**How to use this guide:**
1. Find the error message you're seeing
2. Read "What it means"
3. Follow "How to fix" steps
4. If still stuck, see "Still not working?"

---

## Quick Navigation

- [Catalog/Configuration Errors](#catalogconfiguration-errors)
- [SSH/Connection Errors](#sshconnection-errors)
- [Pattern Matching Errors](#pattern-matching-errors)
- [File Access Errors](#file-access-errors)
- [Installation Errors](#installation-errors)

---

## Catalog/Configuration Errors

### Error: "ValidationError: field required"

**Full error message:**
```
ValidationError: 1 validation error for ErrorCatalog
errors -> my_error -> pattern
  field required
```

**What it means:** Your error catalog is missing a required field (in this case, the `pattern` field).

**How to fix:**

1. Open your catalog file
2. Find the error definition mentioned in the error (e.g., `my_error`)
3. Add the missing field:

```yaml
errors:
  my_error:
    id: "my_error"
    pattern:  # ← Add this section
      type: "literal"
      pattern: "ERROR"
    files:
      - "logs/*.log"
    meaning: "An error occurred"
    suggestion: "Check logs"
    context_lines: 5
```

**Common missing fields:**
- `pattern` - Pattern configuration
- `files` - File locations to scan
- `meaning` - What the error means
- `suggestion` - How to fix it

**Validate your fix:**
```bash
as-scan validate my_catalog.yaml
```

---

### Error: "YAML syntax error"

**Full error messages:**
```
yaml.scanner.ScannerError: while scanning for the next token
found character '\t' that cannot start any token
```

or

```
yaml.parser.ParserError: while parsing a block mapping
expected <block end>, but found '<block mapping start>'
```

**What it means:** Your YAML file has syntax errors (usually indentation problems).

**Common causes:**
1. Mixed tabs and spaces (YAML requires spaces only)
2. Wrong indentation levels
3. Missing colons
4. Unquoted special characters

**How to fix:**

**Problem 1: Tabs instead of spaces**
```yaml
# WRONG (has tabs)
errors:
→my_error:
→→pattern:

# CORRECT (spaces only)
errors:
  my_error:
    pattern:
```

**Fix:** Replace all tabs with spaces. Most editors have "Convert Tabs to Spaces" option.

**Problem 2: Wrong indentation**
```yaml
# WRONG (inconsistent indentation)
errors:
  my_error:
  pattern:  # Should be indented more
    type: "literal"

# CORRECT
errors:
  my_error:
    pattern:  # Indented 2 more spaces
      type: "literal"
```

**Fix:** Check that child elements are indented 2 spaces from their parent.

**Problem 3: Special characters need quotes**
```yaml
# WRONG
pattern: ERROR: failed

# CORRECT
pattern: "ERROR: failed"
```

**Validation tools:**
- Online: [YAML Lint](http://www.yamllint.com/)
- Command line: `as-scan validate my_catalog.yaml`

---

### Error: "No such file or directory: my_catalog.yaml"

**What it means:** The catalog file doesn't exist at the path you specified.

**How to fix:**

1. Check the file exists:
   ```bash
   ls -la my_catalog.yaml
   ```

2. If it doesn't exist, create it:
   ```bash
   as-scan init --output my_catalog.yaml
   ```

3. Or use absolute path:
   ```bash
   as-scan scan --catalog /full/path/to/my_catalog.yaml
   ```

4. Check for typos in filename:
   ```bash
   # Common mistakes
   my_catalog.yaml  # Correct
   my_catalog.yml   # Different extension
   my-catalog.yaml  # Dash instead of underscore
   ```

---

## SSH/Connection Errors

### Error: "SSH connection timeout after 120 seconds"

**Full error:**
```
[ERROR] SSH connection timeout after 120 seconds
Failed to connect to ssh://hostname:/path/file.log
```

**What it means:** You haven't configured SSH connection reuse. Each file access creates a new SSH connection, which times out.

**This is the #1 most common error for remote scans!**

**How to fix (required for remote scans):**

1. Edit `~/.ssh/config`:
   ```bash
   nano ~/.ssh/config
   ```

2. Add these lines:
   ```ssh-config
   Host *
       ControlMaster auto
       ControlPath ~/.ssh/control-%C
       ControlPersist 10m
   ```

3. Save and exit (Ctrl+O, Enter, Ctrl+X in nano)

4. Verify it works:
   ```bash
   as-scan check-ssh hostname
   ```

5. Try your scan again:
   ```bash
   as-scan scan --catalog my_catalog.yaml
   ```

**See also:** [SSH_CONNECTION_POOLING.md](SSH_CONNECTION_POOLING.md) for detailed guide

---

### Error: "Permission denied (publickey)"

**Full error:**
```
Permission denied (publickey).
Lost connection
```

**What it means:** SSH authentication failed. You don't have permission to access the server.

**How to fix:**

1. Test SSH connection manually:
   ```bash
   ssh hostname
   ```

2. If that fails, check SSH key setup:
   ```bash
   # Check if you have SSH keys
   ls -la ~/.ssh/id_rsa.pub

   # If no key exists, create one
   ssh-keygen -t rsa -b 4096
   ```

3. Copy your SSH key to the server:
   ```bash
   ssh-copy-id username@hostname
   ```

4. Or add your key to `~/.ssh/config`:
   ```ssh-config
   Host my-server
       HostName actual-hostname.com
       User myusername
       IdentityFile ~/.ssh/id_rsa
   ```

5. Test again:
   ```bash
   ssh my-server
   as-scan scan --catalog my_catalog.yaml
   ```

---

### Error: "Host key verification failed"

**Full error:**
```
Host key verification failed.
Lost connection
```

**What it means:** SSH doesn't recognize the server's fingerprint (first-time connection or server changed).

**How to fix:**

1. Connect manually first to accept the fingerprint:
   ```bash
   ssh hostname
   ```

2. Type "yes" when prompted:
   ```
   The authenticity of host 'hostname (192.168.1.1)' can't be established.
   Are you sure you want to continue connecting (yes/no)? yes
   ```

3. Now try your scan again:
   ```bash
   as-scan scan --catalog my_catalog.yaml
   ```

**Security note:** Only accept if you trust the server!

---

## Pattern Matching Errors

### Error: "No files matched pattern"

**Full error:**
```
[WARNING] No files matched pattern: /var/log/**/*.log
[INFO] Scan completed: 0 errors found
```

**What it means:** The file glob pattern didn't match any files, or files don't exist.

**How to fix:**

1. Test the glob pattern manually:
   ```bash
   # On Linux/Mac
   ls -la /var/log/**/*.log

   # If that doesn't work, try
   ls -la /var/log/*.log
   ls -la /var/log/
   ```

2. Common mistakes:

   **Wrong:** `/var/log/**/*.log` (might not have permission)
   **Better:** `~/logs/**/*.log` (your home directory)

   **Wrong:** `logs/*.log` (relative path - depends on where you run command)
   **Better:** `~/project/logs/*.log` (absolute or home-relative)

3. Check permissions:
   ```bash
   ls -la /var/log
   # If you see "Permission denied", you can't access those files
   ```

4. Use a path you own:
   ```yaml
   files:
     - "~/test-logs/**/*.log"  # Your home directory
     - "/tmp/logs/**/*.log"    # Temp directory
   ```

---

### Error: "regex error: invalid pattern"

**Full error:**
```
re.error: nothing to repeat at position 10
```

**What it means:** Your regex pattern has syntax errors.

**How to fix:**

1. Test your regex at [regex101.com](https://regex101.com/)

2. Common regex mistakes:

   **Wrong:** `ERROR*` (means "ERRO" + zero or more "R")
   **Correct:** `ERROR.*` (means "ERROR" + any characters)

   **Wrong:** `Error (` (unmatched parenthesis)
   **Correct:** `Error \\(` (escaped parenthesis) or `Error \\(`

   **Wrong:** `test.log` (dot matches any character)
   **Correct:** `test\\.log` (escaped dot matches literal dot)

3. Use raw strings in YAML:
   ```yaml
   pattern:
     type: "regex"
     pattern: "ERROR\\s+\\d+"  # Need double backslashes in YAML
   ```

4. Start simple:
   ```yaml
   # Start with literal
   pattern:
     type: "literal"
     pattern: "ERROR"

   # Then add complexity
   pattern:
     type: "regex"
     pattern: "ERROR|CRITICAL|FATAL"
   ```

---

### Error: "No matches found for error_id"

**Full error:**
```
[INFO] No matches found for error 'my_error'
[INFO] Scan completed: 0 errors found
```

**What it means:** The pattern ran but didn't find any matching errors in the files.

**Not necessarily an error!** This could mean:
- Files don't contain the error pattern (good news!)
- Pattern is too specific
- Pattern syntax is wrong

**How to verify:**

1. Check the pattern matches manually:
   ```bash
   grep "OOM killed" ~/logs/*.log
   ```

2. If grep finds matches but autosubmit-scan doesn't:
   - Check pattern syntax in catalog
   - Verify file paths are correct
   - Check for case sensitivity

3. Test with a known error:
   ```yaml
   errors:
     test_error:
       pattern:
         type: "literal"
         pattern: "ERROR"  # Very common, should match something
       files:
         - "~/logs/*.log"
   ```

4. Check scan output for file discovery:
   ```
   [INFO] Discovered 0 files  ← Problem: no files found
   [INFO] Discovered 42 files ← Good: files found
   [INFO] No matches          ← Pattern didn't match
   ```

---

## File Access Errors

### Error: "Permission denied" (local files)

**Full error:**
```
PermissionError: [Errno 13] Permission denied: '/var/log/system.log'
```

**What it means:** You don't have permission to read the file.

**How to fix:**

1. Check file permissions:
   ```bash
   ls -la /var/log/system.log
   # Example output:
   # -rw-r----- 1 root adm 12345 Jan 15 10:00 system.log
   #            ↑       ↑
   #            owner   group
   ```

2. Options:

   **Option A:** Use files you own
   ```yaml
   files:
     - "~/my-logs/**/*.log"  # Your files
   ```

   **Option B:** Add yourself to the group (if applicable)
   ```bash
   sudo usermod -a -G adm $USER
   # Log out and back in for group to take effect
   ```

   **Option C:** Copy files to accessible location
   ```bash
   cp /var/log/system.log ~/logs/
   # Then scan ~/logs/system.log
   ```

---

### Error: "No such file or directory" (in scan results)

**Full error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'logs/run.log'
```

**What it means:** The file path in your catalog doesn't exist or is relative (not absolute).

**How to fix:**

1. Use absolute paths or home-relative paths:
   ```yaml
   # WRONG (relative path - depends on where you run command)
   files:
     - "logs/*.log"

   # CORRECT (absolute path)
   files:
     - "/home/username/logs/*.log"

   # CORRECT (home-relative)
   files:
     - "~/logs/*.log"
   ```

2. Test the path:
   ```bash
   ls -la ~/logs/*.log
   ```

3. For remote files, include full URI:
   ```yaml
   files:
     - "ssh://hostname:/full/path/to/logs/*.log"
   ```

---

### Error: "S3 access denied"

**Full error:**
```
ClientError: An error occurred (403) when calling the GetObject operation: Forbidden
```

**What it means:** You don't have permission to access the S3 bucket, or credentials are missing.

**How to fix:**

1. Check AWS credentials are configured:
   ```bash
   cat ~/.aws/credentials
   # Should show your access key and secret
   ```

2. If missing, configure AWS CLI:
   ```bash
   pip install awscli
   aws configure
   # Enter your Access Key ID and Secret Access Key
   ```

3. Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your_key_here
   export AWS_SECRET_ACCESS_KEY=your_secret_here
   ```

4. Test access:
   ```bash
   aws s3 ls s3://your-bucket/path/
   ```

5. Check bucket permissions (ask your AWS admin)

---

## Installation Errors

### Error: "command not found: as-scan"

**What it means:** The command isn't installed or not in your PATH.

**How to fix:**

**If using pixi:**
```bash
# Use pixi run prefix
pixi run as-scan --help
```

**If using pip:**
```bash
# Install in editable mode
pip install -e .

# Or add to PATH
export PATH="$PATH:$HOME/.local/bin"
```

**Verify installation:**
```bash
which as-scan
as-scan --version
```

---

### Error: "Python version mismatch"

**Full error:**
```
This project requires Python >= 3.12, but you have 3.9
```

**What it means:** You need Python 3.12 or higher.

**How to fix:**

1. Check Python version:
   ```bash
   python --version
   python3 --version
   ```

2. Install Python 3.12 (platform-specific):

   **Mac (with Homebrew):**
   ```bash
   brew install python@3.12
   ```

   **Ubuntu/Debian:**
   ```bash
   sudo apt install python3.12
   ```

   **Windows:**
   Download from [python.org](https://python.org)

3. Use pyenv for version management:
   ```bash
   pyenv install 3.12
   pyenv local 3.12
   ```

4. Or use pixi (handles Python version automatically):
   ```bash
   pixi install
   pixi run as-scan --help
   ```

---

## Still Not Working?

### General Debugging Steps

1. **Enable verbose logging:**
   ```bash
   as-scan scan --catalog my_catalog.yaml --verbose
   ```

2. **Check catalog syntax:**
   ```bash
   as-scan validate my_catalog.yaml
   ```

3. **Test with minimal example:**
   ```bash
   # Create test log
   echo "ERROR test message" > ~/test.log

   # Create minimal catalog
   cat > test_catalog.yaml << 'EOF'
   version: "1.0.0"
   schema_version: "1.0.0"
   metadata:
     name: "Test"
     author: "Me"
     created: "2024-01-01T00:00:00Z"
     updated: "2024-01-01T00:00:00Z"
   errors:
     test_error:
       id: "test_error"
       pattern:
         type: "literal"
         pattern: "ERROR"
       files:
         - "~/test.log"
       meaning: "Test"
       suggestion: "Test"
       context_lines: 2
       next_errors: []
       metadata:
         severity: "low"
   EOF

   # Scan
   as-scan scan --catalog test_catalog.yaml --output ./test_results
   ```

4. **Check for file conflicts:**
   ```bash
   # Remove old results
   rm -rf output/ results/ test_results/

   # Try again
   as-scan scan --catalog my_catalog.yaml --output ./fresh_results
   ```

### Getting Help

If you're still stuck:

1. **Check documentation:**
   - [USER_GUIDE.md](USER_GUIDE.md)
   - [GLOSSARY.md](GLOSSARY.md)
   - [SSH_CONNECTION_POOLING.md](SSH_CONNECTION_POOLING.md)

2. **Search existing issues:**
   - [GitHub Issues](https://github.com/DestinE-Climate-DT/autosubmit-scan/issues)

3. **File a new issue with:**
   - Full error message
   - Your catalog file (remove sensitive info)
   - Command you ran
   - Operating system and Python version
   - Output from `as-scan validate my_catalog.yaml`

4. **Ask in community forums:**
   - Include minimal reproducible example
   - Describe what you've already tried

---

## Quick Reference: Common Fixes

| Error | Quick Fix |
|-------|-----------|
| SSH timeout | Add SSH connection reuse to `~/.ssh/config` |
| No files matched | Use absolute paths (`~/logs/*.log`) |
| Permission denied | Use files you own or check permissions |
| ValidationError | Run `as-scan validate` and add missing fields |
| YAML syntax | Check indentation (spaces, not tabs) |
| command not found | Use `pixi run as-scan` or install with pip |
| Regex error | Test pattern at regex101.com |
| S3 access denied | Configure AWS credentials |

---

**Last updated:** 2025-10-20
**Maintained by:** Documentation team
**Feedback:** Please report issues or suggest additions
