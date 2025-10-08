"""Condition evaluator for railway pattern.

This module provides condition evaluation for the railway pattern, supporting:
- ALWAYS: Always returns True
- AND: All nested conditions must be True
- OR: At least one nested condition must be True
- CUSTOM: Load and execute callable from "module:function"
- FIELD_EQUALS: error_match.field == value
- FIELD_CONTAINS: value in error_match.field
- FIELD_REGEX: re.match(value, error_match.field)

Field access supports:
- Dot notation: "metadata.hostname"
- Array indexing: "context_before[0]", "context_after[-1]"
- Nested access: "metadata.nested.key"
"""

import re
from typing import Any, Optional
from src.domain.models import ConditionSpec, ConditionType, ErrorMatch, ErrorCatalog
from src.matching.callable_loader import load_callable


def get_field_value(obj: Any, path: str) -> Optional[Any]:
    """Get field value from object using dot notation and array indexing.

    Supports:
    - Simple fields: "line_number"
    - Dot notation: "metadata.hostname"
    - Array indexing: "context_before[0]", "context_after[-1]"
    - Combined: "metadata.items[0].name"

    Args:
        obj: The object to extract field from
        path: The field path (e.g., "metadata.hostname" or "context_before[0]")

    Returns:
        The field value, or None if field doesn't exist or access fails

    Examples:
        >>> match = ErrorMatch(...)
        >>> get_field_value(match, "line_number")
        42
        >>> get_field_value(match, "metadata.hostname")
        "compute-node-01"
        >>> get_field_value(match, "context_before[0]")
        "Starting process..."
    """
    if not path:
        return None

    current = obj
    parts = []
    current_part = ""
    i = 0

    # Parse path into parts (handles both dot notation and array indexing)
    while i < len(path):
        char = path[i]

        if char == ".":
            if current_part:
                parts.append(("attr", current_part))
                current_part = ""
        elif char == "[":
            # Found array index
            if current_part:
                parts.append(("attr", current_part))
                current_part = ""

            # Find closing bracket
            j = i + 1
            while j < len(path) and path[j] != "]":
                j += 1

            if j < len(path):
                index_str = path[i + 1 : j]
                try:
                    index = int(index_str)
                    parts.append(("index", index))
                except ValueError:
                    # Invalid index, return None
                    return None
                i = j  # Skip to closing bracket
            else:
                # No closing bracket found
                return None
        else:
            current_part += char

        i += 1

    # Add final part if any
    if current_part:
        parts.append(("attr", current_part))

    # Navigate through parts
    for part_type, part_value in parts:
        try:
            if part_type == "attr":
                # Try attribute access first (for Pydantic models)
                if hasattr(current, part_value):
                    current = getattr(current, part_value)
                # Then try dictionary access
                elif isinstance(current, dict) and part_value in current:
                    current = current[part_value]
                else:
                    return None
            elif part_type == "index":
                # Array/list indexing
                if isinstance(current, (list, tuple)):
                    current = current[part_value]
                else:
                    return None
        except (AttributeError, KeyError, IndexError, TypeError):
            return None

    return current


class ConditionEvaluator:
    """Evaluates conditions for railway pattern.

    Supports all condition types defined in ConditionType enum:
    - ALWAYS: Always returns True
    - AND: All nested conditions must be True
    - OR: At least one nested condition must be True
    - CUSTOM: Load and execute callable
    - FIELD_EQUALS: Field equals value
    - FIELD_CONTAINS: Value is in field
    - FIELD_REGEX: Regex matches field
    """

    def evaluate(
        self, condition: ConditionSpec, error_match: ErrorMatch, catalog: ErrorCatalog
    ) -> bool:
        """Evaluate a condition against an error match.

        Args:
            condition: The condition to evaluate
            error_match: The error match to evaluate against
            catalog: The error catalog (for custom callables that might need it)

        Returns:
            True if condition is satisfied, False otherwise

        Examples:
            >>> evaluator = ConditionEvaluator()
            >>> condition = ConditionSpec(type=ConditionType.ALWAYS)
            >>> evaluator.evaluate(condition, error_match, catalog)
            True
        """
        if condition.type == ConditionType.ALWAYS:
            return True

        elif condition.type == ConditionType.AND:
            # Vacuous truth: empty AND is True
            if not condition.conditions:
                return True
            return all(
                self.evaluate(c, error_match, catalog) for c in condition.conditions
            )

        elif condition.type == ConditionType.OR:
            # Vacuous falsehood: empty OR is False
            if not condition.conditions:
                return False
            return any(
                self.evaluate(c, error_match, catalog) for c in condition.conditions
            )

        elif condition.type == ConditionType.CUSTOM:
            return self._evaluate_custom(condition, error_match, catalog)

        elif condition.type == ConditionType.FIELD_EQUALS:
            return self._evaluate_field_equals(condition, error_match)

        elif condition.type == ConditionType.FIELD_CONTAINS:
            return self._evaluate_field_contains(condition, error_match)

        elif condition.type == ConditionType.FIELD_REGEX:
            return self._evaluate_field_regex(condition, error_match)

        else:
            # Unknown condition type, return False
            return False

    def _evaluate_custom(
        self, condition: ConditionSpec, error_match: ErrorMatch, catalog: ErrorCatalog
    ) -> bool:
        """Evaluate CUSTOM condition by loading and executing callable.

        Args:
            condition: The CUSTOM condition with callable reference
            error_match: The error match to pass to callable
            catalog: The error catalog to pass to callable

        Returns:
            Result of callable execution, or False if loading fails
        """
        try:
            func = load_callable(condition.callable)
            result = func(error_match, catalog)
            return bool(result)
        except Exception:
            # If callable fails to load or execute, return False
            return False

    def _evaluate_field_equals(
        self, condition: ConditionSpec, error_match: ErrorMatch
    ) -> bool:
        """Evaluate FIELD_EQUALS condition.

        Args:
            condition: The FIELD_EQUALS condition
            error_match: The error match to check

        Returns:
            True if field equals value, False otherwise
        """
        field_value = get_field_value(error_match, condition.field)
        if field_value is None:
            return False
        return field_value == condition.value

    def _evaluate_field_contains(
        self, condition: ConditionSpec, error_match: ErrorMatch
    ) -> bool:
        """Evaluate FIELD_CONTAINS condition.

        Args:
            condition: The FIELD_CONTAINS condition
            error_match: The error match to check

        Returns:
            True if value is in field, False otherwise
        """
        field_value = get_field_value(error_match, condition.field)
        if field_value is None:
            return False

        try:
            return condition.value in field_value
        except TypeError:
            # Field doesn't support 'in' operator
            return False

    def _evaluate_field_regex(
        self, condition: ConditionSpec, error_match: ErrorMatch
    ) -> bool:
        """Evaluate FIELD_REGEX condition.

        Args:
            condition: The FIELD_REGEX condition
            error_match: The error match to check

        Returns:
            True if regex matches field, False otherwise
        """
        field_value = get_field_value(error_match, condition.field)
        if field_value is None:
            return False

        # Convert field value to string for regex matching
        field_str = str(field_value)

        try:
            pattern = re.compile(condition.value)
            return pattern.search(field_str) is not None
        except re.error:
            # Invalid regex pattern
            return False
