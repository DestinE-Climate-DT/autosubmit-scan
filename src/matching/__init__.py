"""Pattern matching and file streaming for error detection.

This module provides:
- Pattern matchers (literal, regex, callable)
- File streaming with fsspec
- Context extraction
- Error match building
"""

from src.matching.callable_loader import load_callable, validate_callable_signature
from src.matching.context_extractor import ContextExtractor, ContextResult
from src.matching.match_builder import ErrorMatchBuilder
from src.matching.pattern_matcher import (
    BasePatternMatcher,
    CallablePatternMatcher,
    LiteralPatternMatcher,
    PatternMatcherFactory,
    RegexPatternMatcher,
)
from src.matching.stream_reader import FileStream

__all__ = [
    "BasePatternMatcher",
    "LiteralPatternMatcher",
    "RegexPatternMatcher",
    "CallablePatternMatcher",
    "PatternMatcherFactory",
    "load_callable",
    "validate_callable_signature",
    "FileStream",
    "ContextExtractor",
    "ContextResult",
    "ErrorMatchBuilder",
]
