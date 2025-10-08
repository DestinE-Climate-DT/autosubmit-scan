"""Context extraction for error matches.

Extracts lines before and after a matched line for better error understanding.
"""

from typing import List
from pydantic import BaseModel
from src.matching.stream_reader import FileStream


class ContextResult(BaseModel):
    """Result of context extraction.

    Contains the matched line plus surrounding context.
    """

    before: List[str]
    matched_line: str
    after: List[str]
    line_number: int

    def get_full_text(self) -> str:
        """Get all context lines as a single text block.

        Returns:
            Combined text of all context lines
        """
        all_lines = self.before + [self.matched_line] + self.after
        return "".join(all_lines)

    def total_lines(self) -> int:
        """Get total number of lines in context.

        Returns:
            Total number of lines (before + matched + after)
        """
        return len(self.before) + 1 + len(self.after)


class ContextExtractor:
    """Extract context around matched lines in files."""

    def extract_context(
        self,
        file_uri: str,
        line_number: int,
        context_lines: int
    ) -> ContextResult:
        """Extract context around a specific line.

        Args:
            file_uri: URI of the file
            line_number: Line number of the match (1-indexed)
            context_lines: Number of lines to include before and after

        Returns:
            ContextResult with before/after context

        Raises:
            ValueError: If line_number < 1 or context_lines < 0
            ValueError: If line_number is beyond file length
            FileNotFoundError: If file doesn't exist

        Examples:
            >>> extractor = ContextExtractor()
            >>> result = extractor.extract_context("app.log", line_number=100, context_lines=3)
            >>> print(result.matched_line)
            >>> print(result.before)  # Up to 3 lines before
            >>> print(result.after)   # Up to 3 lines after
        """
        if line_number < 1:
            raise ValueError(f"Line number must be >= 1, got {line_number}")

        if context_lines < 0:
            raise ValueError(f"Context lines must be >= 0, got {context_lines}")

        # Calculate the range of lines to read
        start_line = max(1, line_number - context_lines)
        # We'll read extra lines to get the after context
        # and to check if line_number exists

        before_lines = []
        matched_line = None
        after_lines = []

        with FileStream.open_file(file_uri) as stream:
            for current_line_num, line_text in stream.read_lines():
                # Collect lines before the match
                if current_line_num < line_number:
                    if current_line_num >= start_line:
                        before_lines.append(line_text)

                # The matched line
                elif current_line_num == line_number:
                    matched_line = line_text

                # Lines after the match
                elif current_line_num > line_number:
                    if len(after_lines) < context_lines:
                        after_lines.append(line_text)
                    else:
                        # We have all the after context we need
                        break

        # Check if we found the matched line
        if matched_line is None:
            raise ValueError(
                f"Line number {line_number} is beyond the file length"
            )

        # Trim before_lines to only keep the last context_lines entries
        if len(before_lines) > context_lines:
            before_lines = before_lines[-context_lines:]

        return ContextResult(
            before=before_lines,
            matched_line=matched_line,
            after=after_lines,
            line_number=line_number
        )
