"""Pattern scanning wrappers for Snakemake workflow.

Provides high-level functions that wrap the pattern matching components
from Iteration 2 for use in Snakemake rules:

- scan_file_for_pattern: Scan a file and return line numbers of matches (single pattern)
- scan_file_for_all_patterns: Scan a file for ALL patterns in one pass (multi-pattern)
- extract_matches_with_context: Extract full ErrorMatch objects with context
"""

from src.domain.models import ErrorCatalog, ErrorDefinition, ErrorMatch, PatternMatcher
from src.matching.context_extractor import ContextExtractor
from src.matching.match_builder import ErrorMatchBuilder
from src.matching.pattern_matcher import PatternMatcherFactory
from src.matching.stream_reader import FileStream


def scan_file_for_pattern(file_uri: str, pattern: PatternMatcher) -> list[int]:
    """Scan a file and return line numbers where pattern matches.

    This is an atomic operation used in the pattern matching rule.
    It only identifies WHERE matches occur, not the full context.

    Args:
        file_uri: URI of file to scan (supports all fsspec protocols)
        pattern: PatternMatcher configuration

    Returns:
        List of line numbers (1-indexed) where pattern matches

    Examples:
        >>> pattern = PatternMatcher(type=PatternType.LITERAL, pattern="ERROR")
        >>> line_numbers = scan_file_for_pattern("s3://bucket/log.txt", pattern)
        >>> line_numbers
        [42, 108, 256]
    """
    # Create the appropriate pattern matcher
    matcher = PatternMatcherFactory.create_matcher(pattern)

    matched_lines = []

    # Stream through file line by line
    with FileStream.open_file(file_uri, strip_newlines=False) as stream:
        for line_number, line_text in stream.read_lines():
            # Check if pattern matches this line
            if matcher.match(line_text):
                # Only record each line once (even if multiple matches on same line)
                if line_number not in matched_lines:
                    matched_lines.append(line_number)

    return matched_lines


def extract_matches_with_context(
    file_uri: str,
    line_numbers: list[int],
    error_def: ErrorDefinition,
) -> list[ErrorMatch]:
    """Extract full ErrorMatch objects with context for matched lines.

    This is an atomic operation used in the context extraction rule.
    It takes the line numbers from pattern matching and extracts
    full context around each match.

    Args:
        file_uri: URI of file containing matches
        line_numbers: List of line numbers to extract (from scan_file_for_pattern)
        error_def: ErrorDefinition with context_lines setting

    Returns:
        List of ErrorMatch objects with full context

    Examples:
        >>> error_def = get_error_definition(catalog, "slurm_oom")
        >>> line_numbers = [42, 108]
        >>> matches = extract_matches_with_context(
        ...     "s3://bucket/log.txt",
        ...     line_numbers,
        ...     error_def
        ... )
        >>> len(matches)
        2
    """
    extractor = ContextExtractor()
    builder = ErrorMatchBuilder()

    matches = []

    # For each matched line number, extract context and build ErrorMatch
    for line_number in line_numbers:
        # Extract context around this line
        context = extractor.extract_context(
            file_uri=file_uri,
            line_number=line_number,
            context_lines=error_def.context_lines,
        )

        # Build the ErrorMatch object
        match = builder.build_match(
            error_def=error_def,
            file_uri=file_uri,
            line_number=line_number,
            matched_text=context.matched_line,
            context=context,
        )

        matches.append(match)

    return matches


def scan_file_for_all_patterns(file_uri: str, catalog: ErrorCatalog) -> dict[str, list[ErrorMatch]]:
    """Scan a file for ALL error patterns in one pass.

    This is the key function for file-centric scanning. It opens the file ONCE,
    reads it into memory, and scans for ALL error patterns. This dramatically
    reduces I/O operations and SSH connections for remote files.

    Args:
        file_uri: URI of file to scan (supports all fsspec protocols)
        catalog: ErrorCatalog containing all error definitions

    Returns:
        Dictionary mapping error_id -> list of ErrorMatch objects
        Only includes error IDs that had at least one match.

    Examples:
        >>> catalog = load_catalog("errors.yaml")
        >>> results = scan_file_for_all_patterns("sftp://host/log.txt", catalog)
        >>> results.keys()
        dict_keys(['slurm_oom', 'python_traceback'])
        >>> len(results['slurm_oom'])
        3
    """
    # Results dictionary: error_id -> list of ErrorMatch objects
    results = {}

    # Read the entire file content into memory ONCE
    # We use FileStream to support all fsspec protocols
    file_lines = []
    with FileStream.open_file(file_uri, strip_newlines=False) as stream:
        for line_number, line_text in stream.read_lines():
            file_lines.append((line_number, line_text))

    # For each error definition, scan the in-memory file
    for error_id, error_def in catalog.errors.items():
        # Create pattern matcher for this error
        matcher = PatternMatcherFactory.create_matcher(error_def.pattern)

        # Find all matching line numbers
        matched_line_numbers = []
        for line_number, line_text in file_lines:
            if matcher.match(line_text):
                if line_number not in matched_line_numbers:
                    matched_line_numbers.append(line_number)

        # If we found matches, extract context for each one
        if matched_line_numbers:
            extractor = ContextExtractor()
            builder = ErrorMatchBuilder()
            matches = []

            for line_number in matched_line_numbers:
                # Extract context around this line
                context = extractor.extract_context(
                    file_uri=file_uri,
                    line_number=line_number,
                    context_lines=error_def.context_lines,
                )

                # Build the ErrorMatch object
                match = builder.build_match(
                    error_def=error_def,
                    file_uri=file_uri,
                    line_number=line_number,
                    matched_text=context.matched_line,
                    context=context,
                )

                matches.append(match)

            # Store results for this error
            results[error_id] = matches

    return results
