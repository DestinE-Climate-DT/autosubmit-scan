"""Example custom condition callables for railway pattern.

This module provides example condition functions that can be used in
error catalogs with CUSTOM condition types.

All condition callables must have the signature:
    (error_match: ErrorMatch, catalog: ErrorCatalog) -> bool

Examples of condition patterns:
- File type detection (Python, C++, Java errors)
- Contextual analysis (in loop, in function)
- Resource usage checks (memory, CPU)
- Temporal patterns (weekend, night, business hours)
- Metadata-based conditions (hostname, user, job ID)
"""

from src.domain.models import ErrorCatalog, ErrorMatch


def is_python_error(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Check if error is related to Python.

    Looks for Python-specific indicators in the matched text:
    - "python" keyword (case-insensitive)
    - "Traceback" (Python stack traces)
    - ".py" file extensions
    - Common Python error types (ImportError, ValueError, etc.)

    Args:
        error_match: The error match to check
        catalog: The error catalog (unused but required by signature)

    Returns:
        True if error appears to be Python-related, False otherwise

    Examples:
        >>> match = ErrorMatch(matched_text="Traceback (most recent call last):", ...)
        >>> is_python_error(match, catalog)
        True
    """
    text = error_match.matched_text.lower()

    python_indicators = [
        "python",
        "traceback",
        ".py",
        "importerror",
        "valueerror",
        "typeerror",
        "attributeerror",
        "keyerror",
        "indexerror",
        "nameerror",
    ]

    return any(indicator in text for indicator in python_indicators)


def is_in_loop_context(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Check if error occurred within a loop context.

    Examines context_before and context_after for loop indicators:
    - "for" loops
    - "while" loops
    - "loop" keyword
    - Iteration indicators

    Args:
        error_match: The error match to check
        catalog: The error catalog (unused but required by signature)

    Returns:
        True if error appears to be in a loop, False otherwise

    Examples:
        >>> match = ErrorMatch(context_before=["for i in range(1000):"], ...)
        >>> is_in_loop_context(match, catalog)
        True
    """
    loop_indicators = ["for ", "while ", " loop", "iteration", "iterate"]

    # Check context before
    for line in error_match.context_before:
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in loop_indicators):
            return True

    # Check context after
    for line in error_match.context_after:
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in loop_indicators):
            return True

    # Check matched text itself
    text_lower = error_match.matched_text.lower()
    if any(indicator in text_lower for indicator in loop_indicators):
        return True

    return False


def has_high_memory_usage(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Check if error indicates high memory usage.

    Looks for memory-related keywords in the error:
    - "memory"
    - "OOM" (Out of Memory)
    - "heap"
    - "allocation"
    - Memory size indicators (GB, MB with large numbers)

    Args:
        error_match: The error match to check
        catalog: The error catalog (unused but required by signature)

    Returns:
        True if error indicates high memory usage, False otherwise

    Examples:
        >>> match = ErrorMatch(matched_text="OutOfMemoryError: heap space", ...)
        >>> has_high_memory_usage(match, catalog)
        True
    """
    text = error_match.matched_text.lower()

    memory_indicators = [
        "memory",
        "oom",
        "out of memory",
        "heap",
        "allocation",
        "malloc",
        "outofmemory",
        "memoryerror",
    ]

    # Check for memory indicators
    for indicator in memory_indicators:
        if indicator in text:
            return True

    # Check context for memory patterns
    all_context = error_match.context_before + error_match.context_after
    for line in all_context:
        line_lower = line.lower()
        for indicator in memory_indicators:
            if indicator in line_lower:
                return True

    return False


def occurred_on_weekend(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Check if error occurred on a weekend (Saturday or Sunday).

    Uses the error_match.timestamp to determine the day of week.

    Args:
        error_match: The error match to check
        catalog: The error catalog (unused but required by signature)

    Returns:
        True if error occurred on Saturday (5) or Sunday (6), False otherwise

    Examples:
        >>> match = ErrorMatch(timestamp=datetime(2025, 10, 11, 12, 0, 0), ...)  # Saturday
        >>> occurred_on_weekend(match, catalog)
        True
    """
    # weekday() returns 0-6 (Monday-Sunday)
    # 5 = Saturday, 6 = Sunday
    weekday = error_match.timestamp.weekday()
    return weekday in (5, 6)


def occurred_at_night(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Check if error occurred during night hours (10 PM - 6 AM).

    Uses the error_match.timestamp to determine the hour.

    Args:
        error_match: The error match to check
        catalog: The error catalog (unused but required by signature)

    Returns:
        True if error occurred between 22:00 and 06:00, False otherwise

    Examples:
        >>> match = ErrorMatch(timestamp=datetime(2025, 10, 8, 23, 30, 0), ...)
        >>> occurred_at_night(match, catalog)
        True
    """
    hour = error_match.timestamp.hour
    return hour >= 22 or hour < 6


def is_critical_severity(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Check if error has critical severity in metadata.

    Looks for a "severity" field in error_match.metadata and checks
    if it's set to "critical".

    Args:
        error_match: The error match to check
        catalog: The error catalog (unused but required by signature)

    Returns:
        True if metadata.severity == "critical", False otherwise

    Examples:
        >>> match = ErrorMatch(metadata={"severity": "critical"}, ...)
        >>> is_critical_severity(match, catalog)
        True
    """
    severity = error_match.metadata.get("severity", "").lower()
    return severity == "critical"


def is_on_compute_node(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Check if error occurred on a compute node.

    Looks for "hostname" in metadata and checks if it contains "compute"
    or "node" keywords.

    Args:
        error_match: The error match to check
        catalog: The error catalog (unused but required by signature)

    Returns:
        True if hostname suggests a compute node, False otherwise

    Examples:
        >>> match = ErrorMatch(metadata={"hostname": "compute-node-01"}, ...)
        >>> is_on_compute_node(match, catalog)
        True
    """
    hostname = error_match.metadata.get("hostname", "").lower()
    return "compute" in hostname or "node" in hostname


def has_stack_trace(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Check if error includes a stack trace.

    Looks for stack trace indicators in context:
    - "Traceback"
    - "Stack trace"
    - "at " (common in Java/C++ stack traces)
    - Multiple lines with file:line patterns

    Args:
        error_match: The error match to check
        catalog: The error catalog (unused but required by signature)

    Returns:
        True if error appears to have a stack trace, False otherwise

    Examples:
        >>> match = ErrorMatch(context_after=["Traceback (most recent call last):", ...], ...)
        >>> has_stack_trace(match, catalog)
        True
    """
    stack_indicators = ["traceback", "stack trace", "stacktrace"]

    # Check matched text
    text_lower = error_match.matched_text.lower()
    if any(indicator in text_lower for indicator in stack_indicators):
        return True

    # Check context
    all_context = error_match.context_before + error_match.context_after
    for line in all_context:
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in stack_indicators):
            return True

    # Check for multiple lines with "at " prefix (common in stack traces)
    at_count = sum(1 for line in all_context if line.strip().startswith("at "))
    if at_count >= 2:
        return True

    return False


def is_repeated_error(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Check if this error pattern repeats in context.

    Looks for the same error text appearing multiple times in context_before
    or context_after, which might indicate a loop or repeated failure.

    Args:
        error_match: The error match to check
        catalog: The error catalog (unused but required by signature)

    Returns:
        True if similar text appears multiple times in context, False otherwise

    Examples:
        >>> match = ErrorMatch(
        ...     matched_text="Connection failed",
        ...     context_before=["Connection failed", "Connection failed"],
        ...     ...
        ... )
        >>> is_repeated_error(match, catalog)
        True
    """
    # Get key phrase from matched text (first 50 chars)
    key_phrase = error_match.matched_text[:50].lower()

    # Count occurrences in context
    all_context = error_match.context_before + error_match.context_after
    occurrences = sum(1 for line in all_context if key_phrase in line.lower())

    # If found 2+ times in context (not counting the match itself), it's repeated
    return occurrences >= 2


def is_concurrent_error(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Check if error is related to concurrency issues.

    Looks for concurrency-related keywords:
    - "race condition"
    - "deadlock"
    - "thread"
    - "lock"
    - "semaphore"
    - "concurrent"

    Args:
        error_match: The error match to check
        catalog: The error catalog (unused but required by signature)

    Returns:
        True if error appears to be concurrency-related, False otherwise

    Examples:
        >>> match = ErrorMatch(matched_text="Deadlock detected", ...)
        >>> is_concurrent_error(match, catalog)
        True
    """
    concurrency_indicators = [
        "race condition",
        "deadlock",
        "thread",
        "lock",
        "semaphore",
        "concurrent",
        "mutex",
        "synchronization",
    ]

    text_lower = error_match.matched_text.lower()
    all_context = error_match.context_before + error_match.context_after

    # Check matched text
    for indicator in concurrency_indicators:
        if indicator in text_lower:
            return True

    # Check context
    for line in all_context:
        line_lower = line.lower()
        for indicator in concurrency_indicators:
            if indicator in line_lower:
                return True

    return False
