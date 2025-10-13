"""Snakemake workflow orchestration for error scanning.

This module provides the workflow orchestration layer that coordinates:
- File discovery via fsspec glob patterns
- File fingerprinting for caching and change detection
- Pattern matching across files
- Context extraction for matches
- Result aggregation

Main components:
- helpers: Utility functions for file operations and catalog access
- scanners: Pattern scanning wrappers for workflow rules
- Snakefile: Main workflow definition with checkpoints and rules
"""

from src.orchestration.helpers import (
    expand_fsspec_patterns,
    get_error_definition,
    get_file_hash,
    get_fingerprint,
    read_manifest,
    write_manifest,
)
from src.orchestration.scanners import (
    extract_matches_with_context,
    scan_file_for_pattern,
)

__all__ = [
    "get_file_hash",
    "expand_fsspec_patterns",
    "get_fingerprint",
    "read_manifest",
    "write_manifest",
    "get_error_definition",
    "scan_file_for_pattern",
    "extract_matches_with_context",
]
