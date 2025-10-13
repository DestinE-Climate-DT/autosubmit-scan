"""Pattern matching engine for error detection.

Provides:
- BasePatternMatcher: Abstract base class for pattern matchers
- LiteralPatternMatcher: Simple string containment matching
- RegexPatternMatcher: Regular expression matching with flags
- CallablePatternMatcher: Custom callable function matching
- PatternMatcherFactory: Factory for creating appropriate matcher instances
"""

import re
from abc import ABC, abstractmethod
from re import Match as RegexMatch

from src.domain.models import PatternMatcher, PatternType
from src.matching.callable_loader import load_callable


class BasePatternMatcher(ABC):
    """Abstract base class for pattern matchers."""

    def __init__(self, pattern: PatternMatcher):
        """Initialize the matcher with a pattern configuration.

        Args:
            pattern: PatternMatcher configuration
        """
        self.pattern = pattern

    @abstractmethod
    def match(self, text: str) -> bool:
        """Check if pattern matches the text.

        Args:
            text: Text to match against

        Returns:
            True if pattern matches, False otherwise
        """
        pass

    @abstractmethod
    def find_all(self, text: str) -> list[RegexMatch]:
        """Find all occurrences of the pattern in text.

        Args:
            text: Text to search in

        Returns:
            List of Match objects with positions

        Raises:
            NotImplementedError: If matcher doesn't support find_all
        """
        pass


class LiteralPatternMatcher(BasePatternMatcher):
    """Literal string pattern matcher.

    Performs simple case-sensitive substring matching.
    """

    def match(self, text: str) -> bool:
        """Check if literal pattern is contained in text.

        Args:
            text: Text to match against

        Returns:
            True if pattern is found in text
        """
        return self.pattern.pattern in text

    def find_all(self, text: str) -> list[RegexMatch]:
        """Find all occurrences of the literal pattern.

        Args:
            text: Text to search in

        Returns:
            List of Match objects
        """
        # Use regex to find all occurrences and get Match objects
        pattern = re.escape(self.pattern.pattern)
        regex = re.compile(pattern)
        return list(regex.finditer(text))


class RegexPatternMatcher(BasePatternMatcher):
    """Regular expression pattern matcher.

    Supports regex flags like IGNORECASE, MULTILINE, DOTALL, etc.
    """

    # Map flag names to re module constants
    FLAG_MAP = {
        "IGNORECASE": re.IGNORECASE,
        "I": re.IGNORECASE,
        "MULTILINE": re.MULTILINE,
        "M": re.MULTILINE,
        "DOTALL": re.DOTALL,
        "S": re.DOTALL,
        "VERBOSE": re.VERBOSE,
        "X": re.VERBOSE,
        "ASCII": re.ASCII,
        "A": re.ASCII,
        "LOCALE": re.LOCALE,
        "L": re.LOCALE,
        "UNICODE": re.UNICODE,
        "U": re.UNICODE,
    }

    def __init__(self, pattern: PatternMatcher):
        """Initialize regex matcher and compile pattern.

        Args:
            pattern: PatternMatcher configuration

        Raises:
            re.error: If regex pattern is invalid
        """
        super().__init__(pattern)

        # Build flags from pattern configuration
        flags = 0
        if self.pattern.flags:
            for flag_name in self.pattern.flags:
                flag_value = self.FLAG_MAP.get(flag_name.upper())
                if flag_value:
                    flags |= flag_value

        # Compile regex pattern
        self.regex = re.compile(self.pattern.pattern, flags)

    def match(self, text: str) -> bool:
        """Check if regex pattern matches text.

        Args:
            text: Text to match against

        Returns:
            True if pattern matches anywhere in text
        """
        return self.regex.search(text) is not None

    def find_all(self, text: str) -> list[RegexMatch]:
        """Find all regex matches in text.

        Args:
            text: Text to search in

        Returns:
            List of Match objects with groups and positions
        """
        return list(self.regex.finditer(text))


class CallablePatternMatcher(BasePatternMatcher):
    """Callable pattern matcher.

    Loads and executes a custom Python function for pattern matching.
    Function must have signature: (text: str) -> bool
    """

    def __init__(self, pattern: PatternMatcher):
        """Initialize callable matcher and load function.

        Args:
            pattern: PatternMatcher configuration with callable reference

        Raises:
            ImportError: If module cannot be imported
            AttributeError: If function doesn't exist
        """
        super().__init__(pattern)

        # Load the callable function
        self.callable = load_callable(self.pattern.pattern)

    def match(self, text: str) -> bool:
        """Execute callable function to check if pattern matches.

        Args:
            text: Text to match against

        Returns:
            Result of callable function (must be bool)

        Raises:
            TypeError: If callable doesn't return bool
        """
        result = self.callable(text)

        if not isinstance(result, bool):
            raise TypeError(f"Callable {self.pattern.pattern} must return bool, " f"got {type(result).__name__}")

        return result

    def find_all(self, text: str) -> list[RegexMatch]:
        """Find all matches using callable.

        Note: Callables that return bool cannot provide match positions,
        so this method raises NotImplementedError.

        Args:
            text: Text to search in

        Raises:
            NotImplementedError: Callables don't support find_all
        """
        raise NotImplementedError("Callable pattern matchers cannot provide match positions. " "Use match() method instead.")


class PatternMatcherFactory:
    """Factory for creating appropriate pattern matcher instances."""

    @staticmethod
    def create_matcher(pattern: PatternMatcher) -> BasePatternMatcher:
        """Create appropriate matcher based on pattern type.

        Args:
            pattern: PatternMatcher configuration

        Returns:
            Concrete pattern matcher instance

        Raises:
            ValueError: If pattern type is not recognized
        """
        if pattern.type == PatternType.LITERAL:
            return LiteralPatternMatcher(pattern)
        elif pattern.type == PatternType.REGEX:
            return RegexPatternMatcher(pattern)
        elif pattern.type == PatternType.CALLABLE:
            return CallablePatternMatcher(pattern)
        else:
            raise ValueError(f"Unknown pattern type: {pattern.type}")
