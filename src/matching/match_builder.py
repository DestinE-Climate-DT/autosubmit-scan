"""Error match builder for creating ErrorMatch instances.

Builds ErrorMatch objects from error definitions and context results.
"""

from datetime import UTC, datetime
from typing import Any

from src.domain.models import ErrorDefinition, ErrorMatch
from src.matching.context_extractor import ContextResult


class ErrorMatchBuilder:
    """Builder for creating ErrorMatch instances."""

    @staticmethod
    def build_match(
        error_def: ErrorDefinition,
        file_uri: str,
        line_number: int,
        matched_text: str,
        context: ContextResult,
        metadata: dict[str, Any] = None,
    ) -> ErrorMatch:
        """Build an ErrorMatch from error definition and context.

        Args:
            error_def: The error definition that was matched
            file_uri: URI of the file where match occurred
            line_number: Line number of the match (1-indexed)
            matched_text: The specific text that matched the pattern
            context: Context extracted around the match
            metadata: Additional metadata to attach to the match

        Returns:
            ErrorMatch instance

        Examples:
            >>> builder = ErrorMatchBuilder()
            >>> match = builder.build_match(
            ...     error_def=my_error_def,
            ...     file_uri="s3://bucket/log.txt",
            ...     line_number=42,
            ...     matched_text="ERROR: Out of memory",
            ...     context=context_result,
            ...     metadata={"severity": "high"}
            ... )
        """
        if metadata is None:
            metadata = {}

        # Add error definition metadata to match metadata
        if error_def.metadata:
            metadata.update(error_def.metadata)

        return ErrorMatch(
            error_id=error_def.id,
            file_uri=file_uri,
            line_number=line_number,
            matched_text=matched_text,
            context_before=context.before,
            context_after=context.after,
            timestamp=datetime.now(UTC),
            metadata=metadata,
        )
