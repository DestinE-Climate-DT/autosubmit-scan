"""Unit tests for ConditionEvaluator.

Tests cover:
- All condition types (ALWAYS, AND, OR, CUSTOM, FIELD_*)
- Nested conditions
- Field access with dot notation and array indexing
- Error handling for missing fields
"""

from datetime import datetime

import pytest

from src.domain.models import (
    CatalogMetadata,
    ConditionSpec,
    ConditionType,
    ErrorCatalog,
    ErrorDefinition,
    ErrorMatch,
    PatternMatcher,
    PatternType,
)
from src.orchestration.conditions import ConditionEvaluator, get_field_value


@pytest.fixture
def sample_error_match():
    """Create a sample ErrorMatch for testing."""
    return ErrorMatch(
        error_id="test_error",
        file_uri="file:///tmp/test.log",
        line_number=42,
        matched_text="OutOfMemoryError: Java heap space",
        context_before=["Starting process...", "Allocating memory..."],
        context_after=["Process crashed", "Cleaning up..."],
        timestamp=datetime(2025, 10, 8, 12, 0, 0),
        metadata={
            "hostname": "compute-node-01",
            "severity": "critical",
            "user": "testuser",
            "nested": {"key": "value", "count": 42},
        },
    )


@pytest.fixture
def sample_catalog():
    """Create a sample ErrorCatalog for testing."""
    return ErrorCatalog(
        version="1.0.0",
        schema_version="1.0.0",
        metadata=CatalogMetadata(
            name="Test Catalog",
            description="Test catalog for condition evaluation",
            author="Test Author",
            created=datetime(2025, 1, 1, 0, 0, 0),
            updated=datetime(2025, 1, 1, 0, 0, 0),
        ),
        errors={
            "test_error": ErrorDefinition(
                id="test_error",
                pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
                files=["file:///tmp/*.log"],
                meaning="Test error",
                context_lines=2,
                suggestion="Fix it",
            )
        },
    )


@pytest.fixture
def evaluator():
    """Create a ConditionEvaluator instance."""
    return ConditionEvaluator()


# Test ALWAYS condition
def test_evaluate_always(evaluator, sample_error_match, sample_catalog):
    """ALWAYS condition should always return True."""
    condition = ConditionSpec(type=ConditionType.ALWAYS)
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


# Test AND conditions
def test_evaluate_and_all_true(evaluator, sample_error_match, sample_catalog):
    """AND condition with all true nested conditions should return True."""
    condition = ConditionSpec(
        type=ConditionType.AND,
        conditions=[
            ConditionSpec(type=ConditionType.ALWAYS),
            ConditionSpec(type=ConditionType.ALWAYS),
            ConditionSpec(type=ConditionType.ALWAYS),
        ],
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


def test_evaluate_and_one_false(evaluator, sample_error_match, sample_catalog):
    """AND condition with one false nested condition should return False."""
    condition = ConditionSpec(
        type=ConditionType.AND,
        conditions=[
            ConditionSpec(type=ConditionType.ALWAYS),
            ConditionSpec(
                type=ConditionType.FIELD_EQUALS,
                field="line_number",
                value=999,  # This will be false
            ),
            ConditionSpec(type=ConditionType.ALWAYS),
        ],
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is False


def test_evaluate_and_single_true(evaluator, sample_error_match, sample_catalog):
    """AND condition with single true condition should return True."""
    condition = ConditionSpec(
        type=ConditionType.AND, conditions=[ConditionSpec(type=ConditionType.ALWAYS)]
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


# Test OR conditions
def test_evaluate_or_one_true(evaluator, sample_error_match, sample_catalog):
    """OR condition with one true nested condition should return True."""
    condition = ConditionSpec(
        type=ConditionType.OR,
        conditions=[
            ConditionSpec(
                type=ConditionType.FIELD_EQUALS, field="line_number", value=999
            ),
            ConditionSpec(type=ConditionType.ALWAYS),  # This is true
            ConditionSpec(
                type=ConditionType.FIELD_EQUALS, field="line_number", value=888
            ),
        ],
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


def test_evaluate_or_all_false(evaluator, sample_error_match, sample_catalog):
    """OR condition with all false nested conditions should return False."""
    condition = ConditionSpec(
        type=ConditionType.OR,
        conditions=[
            ConditionSpec(
                type=ConditionType.FIELD_EQUALS, field="line_number", value=999
            ),
            ConditionSpec(
                type=ConditionType.FIELD_EQUALS, field="line_number", value=888
            ),
            ConditionSpec(
                type=ConditionType.FIELD_EQUALS, field="line_number", value=777
            ),
        ],
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is False


def test_evaluate_or_single_false(evaluator, sample_error_match, sample_catalog):
    """OR condition with single false condition should return False."""
    condition = ConditionSpec(
        type=ConditionType.OR,
        conditions=[
            ConditionSpec(
                type=ConditionType.FIELD_EQUALS, field="line_number", value=999
            )
        ],
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is False


# Test FIELD_EQUALS
def test_evaluate_field_equals_true(evaluator, sample_error_match, sample_catalog):
    """FIELD_EQUALS should return True when field equals value."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS, field="line_number", value=42
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


def test_evaluate_field_equals_false(evaluator, sample_error_match, sample_catalog):
    """FIELD_EQUALS should return False when field does not equal value."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS, field="line_number", value=999
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is False


def test_evaluate_field_equals_string(evaluator, sample_error_match, sample_catalog):
    """FIELD_EQUALS should work with string fields."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS,
        field="matched_text",
        value="OutOfMemoryError: Java heap space",
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


# Test FIELD_CONTAINS
def test_evaluate_field_contains_true(evaluator, sample_error_match, sample_catalog):
    """FIELD_CONTAINS should return True when value is in field."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_CONTAINS, field="matched_text", value="OutOfMemory"
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


def test_evaluate_field_contains_false(evaluator, sample_error_match, sample_catalog):
    """FIELD_CONTAINS should return False when value is not in field."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_CONTAINS, field="matched_text", value="NonExistent"
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is False


def test_evaluate_field_contains_list(evaluator, sample_error_match, sample_catalog):
    """FIELD_CONTAINS should work with list fields."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_CONTAINS,
        field="context_before",
        value="Starting process...",
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


# Test FIELD_REGEX
def test_evaluate_field_regex_match(evaluator, sample_error_match, sample_catalog):
    """FIELD_REGEX should return True when regex matches."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_REGEX, field="matched_text", value=r"OutOf.*Error"
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


def test_evaluate_field_regex_no_match(evaluator, sample_error_match, sample_catalog):
    """FIELD_REGEX should return False when regex does not match."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_REGEX, field="matched_text", value=r"^Success"
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is False


def test_evaluate_field_regex_case_sensitive(
    evaluator, sample_error_match, sample_catalog
):
    """FIELD_REGEX should be case-sensitive by default."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_REGEX, field="matched_text", value=r"outofmemory"
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is False


# Test CUSTOM callable
def test_evaluate_custom_callable(evaluator, sample_error_match, sample_catalog):
    """CUSTOM condition should load and execute callable."""
    condition = ConditionSpec(
        type=ConditionType.CUSTOM,
        callable="tests.unit.test_conditions:always_true_condition",
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


def test_evaluate_custom_callable_false(evaluator, sample_error_match, sample_catalog):
    """CUSTOM condition should return False when callable returns False."""
    condition = ConditionSpec(
        type=ConditionType.CUSTOM,
        callable="tests.unit.test_conditions:always_false_condition",
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is False


def test_evaluate_custom_callable_with_logic(
    evaluator, sample_error_match, sample_catalog
):
    """CUSTOM condition should execute callable logic."""
    condition = ConditionSpec(
        type=ConditionType.CUSTOM,
        callable="tests.unit.test_conditions:check_line_number_even",
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True  # 42 is even


# Test nested conditions
def test_nested_conditions_and_or(evaluator, sample_error_match, sample_catalog):
    """Test nested AND(OR(...), OR(...)) conditions."""
    condition = ConditionSpec(
        type=ConditionType.AND,
        conditions=[
            ConditionSpec(
                type=ConditionType.OR,
                conditions=[
                    ConditionSpec(
                        type=ConditionType.FIELD_EQUALS, field="line_number", value=42
                    ),
                    ConditionSpec(
                        type=ConditionType.FIELD_EQUALS, field="line_number", value=43
                    ),
                ],
            ),
            ConditionSpec(
                type=ConditionType.OR,
                conditions=[
                    ConditionSpec(
                        type=ConditionType.FIELD_CONTAINS,
                        field="matched_text",
                        value="OutOfMemory",
                    ),
                    ConditionSpec(
                        type=ConditionType.FIELD_CONTAINS,
                        field="matched_text",
                        value="NullPointer",
                    ),
                ],
            ),
        ],
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True  # Both OR conditions are true


def test_nested_conditions_complex(evaluator, sample_error_match, sample_catalog):
    """Test complex nested conditions with multiple levels."""
    condition = ConditionSpec(
        type=ConditionType.AND,
        conditions=[
            ConditionSpec(
                type=ConditionType.OR,
                conditions=[
                    ConditionSpec(
                        type=ConditionType.AND,
                        conditions=[
                            ConditionSpec(
                                type=ConditionType.FIELD_EQUALS,
                                field="line_number",
                                value=42,
                            ),
                            ConditionSpec(
                                type=ConditionType.FIELD_REGEX,
                                field="matched_text",
                                value=r"OutOf.*Error",
                            ),
                        ],
                    ),
                    ConditionSpec(type=ConditionType.FIELD_EQUALS, field="line_number", value=999),
                ],
            ),
            ConditionSpec(type=ConditionType.ALWAYS),
        ],
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


# Test field access with dot notation
def test_field_access_dot_notation(evaluator, sample_error_match, sample_catalog):
    """Field access should support dot notation for nested metadata."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS, field="metadata.hostname", value="compute-node-01"
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


def test_field_access_nested_dot_notation(
    evaluator, sample_error_match, sample_catalog
):
    """Field access should support multiple levels of dot notation."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS, field="metadata.nested.key", value="value"
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


def test_field_access_nested_int(evaluator, sample_error_match, sample_catalog):
    """Field access should work with nested integer values."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS, field="metadata.nested.count", value=42
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


# Test field access with array indexing
def test_field_access_array_index_positive(
    evaluator, sample_error_match, sample_catalog
):
    """Field access should support positive array indexing."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS,
        field="context_before[0]",
        value="Starting process...",
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


def test_field_access_array_index_negative(
    evaluator, sample_error_match, sample_catalog
):
    """Field access should support negative array indexing."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS,
        field="context_after[-1]",
        value="Cleaning up...",
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


def test_field_access_array_index_middle(
    evaluator, sample_error_match, sample_catalog
):
    """Field access should support middle array indices."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS,
        field="context_before[1]",
        value="Allocating memory...",
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is True


# Test missing field handling
def test_missing_field_returns_false(evaluator, sample_error_match, sample_catalog):
    """Missing field should return False gracefully."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS, field="nonexistent_field", value="anything"
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is False


def test_missing_nested_field_returns_false(
    evaluator, sample_error_match, sample_catalog
):
    """Missing nested field should return False gracefully."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS,
        field="metadata.nonexistent.field",
        value="anything",
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is False


def test_array_index_out_of_bounds_returns_false(
    evaluator, sample_error_match, sample_catalog
):
    """Array index out of bounds should return False gracefully."""
    condition = ConditionSpec(
        type=ConditionType.FIELD_EQUALS, field="context_before[999]", value="anything"
    )
    result = evaluator.evaluate(condition, sample_error_match, sample_catalog)
    assert result is False


# Test get_field_value helper
def test_get_field_value_simple(sample_error_match):
    """get_field_value should retrieve simple fields."""
    value = get_field_value(sample_error_match, "line_number")
    assert value == 42


def test_get_field_value_dot_notation(sample_error_match):
    """get_field_value should handle dot notation."""
    value = get_field_value(sample_error_match, "metadata.hostname")
    assert value == "compute-node-01"


def test_get_field_value_array_index(sample_error_match):
    """get_field_value should handle array indexing."""
    value = get_field_value(sample_error_match, "context_before[0]")
    assert value == "Starting process..."


def test_get_field_value_missing_returns_none(sample_error_match):
    """get_field_value should return None for missing fields."""
    value = get_field_value(sample_error_match, "nonexistent")
    assert value is None


def test_get_field_value_nested_missing_returns_none(sample_error_match):
    """get_field_value should return None for missing nested fields."""
    value = get_field_value(sample_error_match, "metadata.nonexistent")
    assert value is None


# Custom condition callables for testing
def always_true_condition(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Always returns True."""
    return True


def always_false_condition(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Always returns False."""
    return False


def check_line_number_even(error_match: ErrorMatch, catalog: ErrorCatalog) -> bool:
    """Check if line number is even."""
    return error_match.line_number % 2 == 0
