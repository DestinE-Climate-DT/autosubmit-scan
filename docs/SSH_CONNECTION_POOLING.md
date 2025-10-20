# SSH Connection Reuse Guide

**For unfamiliar terms, see the [Glossary](GLOSSARY.md).**

This document explains how to set up [SSH connection reuse](GLOSSARY.md#ssh-connection-reuse) (also called "SSH ControlMaster" or "connection pooling"). **This setup is REQUIRED for scanning [remote files](GLOSSARY.md#remote-file-access) over SSH/SFTP** - without it, scans will fail with timeout errors.

**Quick setup:** See the one-time setup in the [README](../README.md#important-ssh-setup-required-for-remote-scans).

**Analogy:** SSH connection reuse is like carpooling vs everyone driving separately - more efficient and faster.

## Why This Is Required

When scanning remote files over SSH/SFTP, the tool creates multiple connections for different operations:
- File discovery (glob expansion)
- File fingerprinting (metadata extraction)
- Pattern matching (content scanning)
- Context extraction (detailed matches)

For a typical scan with 11 error types and 4 glob patterns each, this could create **44+ SSH connections**, leading to:
- Connection timeouts after 2 minutes
- Slow performance due to repeated SSH handshakes
- Resource exhaustion on SSH servers with connection limits

## Solution: SSH Connection Reuse

autosubmit-scan uses a **three-layer approach** to minimize SSH connections:

### Layer 1: SSH ControlMaster (YOU MUST SET THIS UP)

SSH's built-in connection sharing allows multiple operations to share a single network connection. **This is the critical setup you need to configure.**

**Setup** (add to `~/.ssh/config`):

```ssh-config
# SSH connection reuse for autosubmit-scan
Host *
    ControlMaster auto
    ControlPath ~/.ssh/control-%C
    ControlPersist 10m
```

**What this does**:
- First SSH connection creates a control socket
- All subsequent connections reuse the existing socket
- Works transparently across all operations (parallel scanning)
- Connection stays alive for 10 minutes after last use

**Benefits**:
- ✅ One-time setup (just edit `~/.ssh/config`)
- ✅ Works with any SSH client
- ✅ Makes scans 10-40x faster
- ✅ Reduces connections from 44+ to ~1-2 per host
- ✅ Prevents timeout errors
- ✅ Works automatically (no code changes)

**Testing**:
```bash
# First connection creates the control socket
ssh climatedt-wf echo "test"

# Check that control socket exists
ls ~/.ssh/control-*

# Subsequent connections are instant
time ssh climatedt-wf echo "test"  # Should be < 0.1s
```

### Layer 2: In-Process Connection Cache

The `get_fsspec_filesystem()` function (in `src/cli/completion.py`) maintains an in-memory cache of fsspec filesystem objects.

**How it works**:
```python
_FILESYSTEM_CACHE = {}  # Global cache

def get_fsspec_filesystem(uri: str):
    # Create cache key from connection details
    cache_key = f"ssh://{user}@{hostname}:{port}"

    # Check cache
    if cache_key in _FILESYSTEM_CACHE:
        cached_fs = _FILESYSTEM_CACHE[cache_key]
        # Test if connection is still alive
        try:
            cached_fs.ls("/", detail=False)
            return cached_fs
        except Exception:
            # Connection dead, remove from cache
            del _FILESYSTEM_CACHE[cache_key]

    # Create new filesystem and cache it
    fs = fsspec.filesystem("ssh", host=hostname, username=user, port=port)
    _FILESYSTEM_CACHE[cache_key] = fs
    return fs
```

**Benefits**:
- ✅ Reuses connections within a single process
- ✅ Validates connections before reuse
- ✅ Automatic cleanup of dead connections

**Limitations**:
- ❌ Doesn't work across Snakemake processes (each rule runs in separate process)
- ❌ Only helps when multiple operations occur in same rule

### Layer 3: asyncssh Configuration

fsspec's SSH backend uses asyncssh, which has its own connection pooling capabilities.

**Configuration** (in `src/cli/completion.py`):
```python
fs_kwargs = {
    "host": hostname,
    "username": user,
    "port": port,
    # asyncssh automatically discovers keys from ~/.ssh/ and ssh-agent
}

fs = fsspec.filesystem("ssh", **fs_kwargs)
```

**How it helps**:
- asyncssh reuses authentication credentials
- Automatically finds SSH keys without repeated password prompts
- Works with ssh-agent for key management

## Performance Comparison

| Scenario | Without ControlMaster | With ControlMaster |
|----------|----------------------|-------------------|
| 11 errors × 4 operations | 44 connections | 1-2 connections |
| Connection time | ~2s × 44 = 88s | ~2s + (0.01s × 43) = 2.4s |
| Timeout risk | High (after 2min) | Low |

## Troubleshooting

### Check if ControlMaster is Working

```bash
# Run a scan and check active control sockets
as-scan scan --catalog catalog.yaml --output results --cores 4

# In another terminal, check control sockets
ls -l ~/.ssh/control-*

# You should see socket files like:
# ~/.ssh/control-C2562ac0e...
```

### Connection Still Timing Out?

1. **Check SSH config**:
   ```bash
   ssh -G climatedt-wf | grep -i control
   ```
   Should show:
   ```
   controlmaster auto
   controlpath ~/.ssh/control-%C
   controlpersist 10m
   ```

2. **Check server limits**:
   ```bash
   ssh climatedt-wf 'ulimit -n'  # Check max open files
   ```

3. **Increase ControlPersist**:
   ```ssh-config
   ControlPersist 30m  # Keep connections alive longer
   ```

4. **Check file permissions**:
   ```bash
   ls -ld ~/.ssh/control-*
   # Should be owned by you with mode 600
   ```

### Manual Connection Testing

```bash
# Enable SSH debug mode
ssh -vvv climatedt-wf

# Look for these lines:
# "Requesting mux connect"  ← Reusing connection
# "ControlSocket ~/.ssh/control-..." ← Using control socket
```

## Best Practices

1. **Always configure ControlMaster** for remote file scanning
2. **Set ControlPersist ≥ 10m** to cover typical scan duration
3. **Monitor connection count** on SSH server during scans
4. **Use SSH keys** (not passwords) for authentication
5. **Configure ssh-agent** to avoid repeated key passphrase prompts

## Environment Variables

No environment variables are needed for connection pooling to work. The system automatically:
- Reads `~/.ssh/config` for SSH settings
- Uses `~/.ssh/known_hosts` for host key verification
- Finds SSH keys in `~/.ssh/` directory
- Connects to ssh-agent if running

## Integration with Snakemake

Snakemake's parallel execution creates separate processes for each rule. SSH ControlMaster is the **only** method that enables connection sharing across these processes.

The workflow creates connections in these stages:
1. **discover_files** checkpoint → glob pattern expansion
2. **fingerprint_file** checkpoint → file metadata extraction
3. **match_pattern** rule → pattern scanning
4. **extract_context** rule → context extraction

Without ControlMaster, each stage creates new connections **for each file**.
With ControlMaster, all stages share **one connection per host**.

## Security Considerations

### ControlMaster Security

- Control sockets are created with mode `0600` (owner-only)
- Control sockets are stored in `~/.ssh/` (user-private directory)
- Only the user who created the control socket can use it
- Control sockets automatically clean up after `ControlPersist` timeout

### Recommendations

1. **Don't use `ControlMaster auto` on shared systems** where you don't trust other users with your account access
2. **Use restrictive permissions** on `~/.ssh/` directory (mode `0700`)
3. **Rotate SSH keys** regularly
4. **Use ssh-agent** instead of storing passphrases in plain text
5. **Audit control sockets** periodically:
   ```bash
   find ~/.ssh -name 'control-*' -mtime +1 -delete
   ```

## References

- [OpenSSH ControlMaster Documentation](https://en.wikibooks.org/wiki/OpenSSH/Cookbook/Multiplexing)
- [fsspec SSH Backend](https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.implementations.sftp.SFTPFileSystem)
- [asyncssh Documentation](https://asyncssh.readthedocs.io/)
