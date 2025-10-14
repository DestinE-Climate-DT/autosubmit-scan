"""Example callable pattern matchers.

These functions demonstrate how to write custom pattern matching functions
for use with the callable pattern matcher type.

All callable pattern matchers must have the signature:
    def matcher_name(text: str) -> bool

The function should return True if the pattern matches, False otherwise.
"""


def detect_memory_leak(text: str) -> bool:
    """Detect potential memory leak patterns.

    Looks for progressive memory increases or OOM warnings.

    Args:
        text: Log line to check

    Returns:
        True if memory leak pattern detected

    Example:
        >>> detect_memory_leak("Memory usage: 95.2 GB / 96.0 GB")
        True
        >>> detect_memory_leak("Memory leak detected in module xyz")
        True
        >>> detect_memory_leak("Normal operation")
        False
    """
    text_lower = text.lower()

    # Check for explicit memory leak mentions
    if "memory leak" in text_lower:
        return True

    # Check for memory exhaustion patterns
    if "out of memory" in text_lower or "oom" in text_lower:
        return True

    # Check for high memory usage (>90%)
    if "memory usage:" in text_lower or "mem:" in text_lower:
        # Simple heuristic: look for percentages >90 or nearly full ratios
        import re

        # Pattern: XX.X GB / YY.Y GB where XX is close to YY
        match = re.search(r"(\d+\.?\d*)\s*gb\s*/\s*(\d+\.?\d*)\s*gb", text_lower)
        if match:
            used = float(match.group(1))
            total = float(match.group(2))
            if total > 0 and (used / total) > 0.90:
                return True

        # Pattern: XX%
        match = re.search(r"(\d+)%", text)
        if match:
            percent = int(match.group(1))
            if percent > 90:
                return True

    return False


def detect_timeout_cascade(text: str) -> bool:
    """Detect timeout cascade patterns.

    A timeout cascade occurs when one timeout leads to others,
    often indicating a systemic issue.

    Args:
        text: Log line to check

    Returns:
        True if timeout cascade pattern detected

    Example:
        >>> detect_timeout_cascade("Timeout waiting for response")
        True
        >>> detect_timeout_cascade("Connection timeout exceeded")
        True
        >>> detect_timeout_cascade("Task completed successfully")
        False
    """
    text_lower = text.lower()

    timeout_keywords = [
        "timeout",
        "timed out",
        "time out",
        "deadline exceeded",
        "connection timeout",
        "read timeout",
        "write timeout",
        "request timeout",
    ]

    return any(keyword in text_lower for keyword in timeout_keywords)


def detect_slurm_oom_kill(text: str) -> bool:
    """Detect SLURM OOM (Out of Memory) kill events.

    Specifically looks for SLURM's characteristic OOM messages.

    Args:
        text: Log line to check

    Returns:
        True if SLURM OOM kill detected

    Example:
        >>> detect_slurm_oom_kill("slurmstepd: error: Detected 1 oom-kill event")
        True
        >>> detect_slurm_oom_kill("slurmstepd: error: Exceeded step memory limit")
        True
        >>> detect_slurm_oom_kill("Job started successfully")
        False
    """
    text_lower = text.lower()

    # SLURM-specific OOM patterns
    slurm_oom_patterns = [
        "oom-kill event",
        "exceeded step memory limit",
        "exceeded memory limit",
        "slurmstepd: error:",
    ]

    # Must have slurmstepd and some OOM indicator
    if "slurmstepd" in text_lower:
        if any(pattern in text_lower for pattern in slurm_oom_patterns):
            return True

    return False


def detect_disk_full(text: str) -> bool:
    """Detect disk full or quota exceeded errors.

    Args:
        text: Log line to check

    Returns:
        True if disk full pattern detected

    Example:
        >>> detect_disk_full("No space left on device")
        True
        >>> detect_disk_full("Disk quota exceeded")
        True
        >>> detect_disk_full("Write operation successful")
        False
    """
    text_lower = text.lower()

    disk_full_patterns = [
        "no space left on device",
        "disk quota exceeded",
        "quota exceeded",
        "disk full",
        "filesystem full",
        "enospc",  # Error number for "no space"
        "out of disk space",
    ]

    return any(pattern in text_lower for pattern in disk_full_patterns)


def detect_network_error(text: str) -> bool:
    """Detect network connectivity errors.

    Args:
        text: Log line to check

    Returns:
        True if network error detected

    Example:
        >>> detect_network_error("Connection refused")
        True
        >>> detect_network_error("Network unreachable")
        True
        >>> detect_network_error("Request completed")
        False
    """
    text_lower = text.lower()

    network_patterns = [
        "connection refused",
        "connection reset",
        "connection timeout",
        "network unreachable",
        "host unreachable",
        "no route to host",
        "connection lost",
        "connection closed",
        "broken pipe",
        "network error",
    ]

    return any(pattern in text_lower for pattern in network_patterns)


def detect_mpi_error(text: str) -> bool:
    """Detect MPI (Message Passing Interface) errors.

    Common in HPC applications.

    Args:
        text: Log line to check

    Returns:
        True if MPI error detected

    Example:
        >>> detect_mpi_error("MPI_Init failed")
        True
        >>> detect_mpi_error("MPI process rank 5 terminated")
        True
        >>> detect_mpi_error("Processing data")
        False
    """
    text_lower = text.lower()

    mpi_patterns = [
        "mpi error",
        "mpi_",
        "mpi abort",
        "mpi_init failed",
        "mpi_finalize",
        "rank terminated",
        "mpi process",
        "pmix",  # Process Management Interface for Exascale
    ]

    # Check for MPI-related keywords
    if any(pattern in text_lower for pattern in mpi_patterns):
        # Also check for error indicators
        error_indicators = ["error", "fail", "abort", "terminate", "exception"]
        if any(indicator in text_lower for indicator in error_indicators):
            return True

    return False


def detect_segmentation_fault(text: str) -> bool:
    """Detect segmentation faults and similar memory errors.

    Args:
        text: Log line to check

    Returns:
        True if segmentation fault detected

    Example:
        >>> detect_segmentation_fault("Segmentation fault (core dumped)")
        True
        >>> detect_segmentation_fault("SIGSEGV received")
        True
        >>> detect_segmentation_fault("Program running")
        False
    """
    text_lower = text.lower()

    segfault_patterns = [
        "segmentation fault",
        "segfault",
        "sigsegv",
        "core dumped",
        "signal 11",  # SIGSEGV signal number
        "bus error",
        "sigbus",
    ]

    return any(pattern in text_lower for pattern in segfault_patterns)


def detect_python_traceback(text: str) -> bool:
    """Detect Python exception tracebacks.

    Args:
        text: Log line to check

    Returns:
        True if Python traceback detected

    Example:
        >>> detect_python_traceback("Traceback (most recent call last):")
        True
        >>> detect_python_traceback("  File \"script.py\", line 42, in function")
        True
        >>> detect_python_traceback("import numpy")
        False
    """
    # Look for Python traceback indicators
    traceback_patterns = [
        "Traceback (most recent call last)",
        "Traceback (innermost last)",
    ]

    if any(pattern in text for pattern in traceback_patterns):
        return True

    # Look for typical traceback file location pattern
    import re

    if re.search(r'File ".*\.py", line \d+', text):
        return True

    # Look for common Python exceptions
    exception_names = [
        "Error:",  # All exceptions end in Error
        "Exception:",
        "Warning:",
    ]

    if any(exc in text for exc in exception_names):
        return True

    return False


# Helper function for testing
def always_true(text: str) -> bool:
    """Always returns True - useful for testing.

    Args:
        text: Ignored

    Returns:
        Always True
    """
    return True


def always_false(text: str) -> bool:
    """Always returns False - useful for testing.

    Args:
        text: Ignored

    Returns:
        Always False
    """
    return False
