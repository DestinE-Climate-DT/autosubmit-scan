"""Unit tests for RailwayExecutor and RailwayPlanner.

Tests cover:
- RailwayExecutor: Getting next errors based on conditions
- RailwayPlanner: Building execution DAG for error chains
"""

from datetime import datetime

import pytest

from src.domain.models import (
    CatalogMetadata,
    ConditionSpec,
    ConditionType,
    ErrorCatalog,
    ErrorCondition,
    ErrorDefinition,
    ErrorMatch,
    PatternMatcher,
    PatternType,
)
from src.orchestration.railway import RailwayExecutor, RailwayPlanner


@pytest.fixture
def simple_catalog():
    """Create a simple catalog with railway patterns."""
    return ErrorCatalog(
        version="1.0.0",
        schema_version="1.0.0",
        metadata=CatalogMetadata(
            name="Test Catalog",
            description="Test catalog for railway pattern",
            author="Test Author",
            created=datetime(2025, 1, 1, 0, 0, 0),
            updated=datetime(2025, 1, 1, 0, 0, 0),
        ),
        errors={
            "slurm_oom": ErrorDefinition(
                id="slurm_oom",
                pattern=PatternMatcher(
                    type=PatternType.LITERAL, pattern="slurmstepd: error: Exceeded"
                ),
                files=["file:///var/log/slurm/*.log"],
                meaning="SLURM out of memory error",
                context_lines=2,
                suggestion="Increase memory allocation",
                next_errors=[
                    ErrorCondition(
                        error_id="memory_leak_check",
                        when=ConditionSpec(type=ConditionType.ALWAYS),
                    ),
                    ErrorCondition(
                        error_id="python_error",
                        when=ConditionSpec(
                            type=ConditionType.FIELD_CONTAINS,
                            field="matched_text",
                            value="python",
                        ),
                    ),
                ],
            ),
            "memory_leak_check": ErrorDefinition(
                id="memory_leak_check",
                pattern=PatternMatcher(
                    type=PatternType.REGEX, pattern=r"memory.*leak"
                ),
                files=["file:///var/log/*.log"],
                meaning="Potential memory leak",
                context_lines=3,
                suggestion="Review memory management",
                next_errors=[],
            ),
            "python_error": ErrorDefinition(
                id="python_error",
                pattern=PatternMatcher(
                    type=PatternType.REGEX, pattern=r"Traceback.*"
                ),
                files=["file:///var/log/*.log"],
                meaning="Python exception",
                context_lines=5,
                suggestion="Fix Python code",
                next_errors=[],
            ),
        },
    )


@pytest.fixture
def complex_catalog():
    """Create a complex catalog with nested railway patterns."""
    return ErrorCatalog(
        version="1.0.0",
        schema_version="1.0.0",
        metadata=CatalogMetadata(
            name="Complex Test Catalog",
            description="Complex catalog with nested railway patterns",
            author="Test Author",
            created=datetime(2025, 1, 1, 0, 0, 0),
            updated=datetime(2025, 1, 1, 0, 0, 0),
        ),
        errors={
            "error_a": ErrorDefinition(
                id="error_a",
                pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR A"),
                files=["file:///tmp/*.log"],
                meaning="Error A",
                context_lines=2,
                suggestion="Fix A",
                next_errors=[
                    ErrorCondition(
                        error_id="error_b",
                        when=ConditionSpec(type=ConditionType.ALWAYS),
                    ),
                    ErrorCondition(
                        error_id="error_c",
                        when=ConditionSpec(
                            type=ConditionType.FIELD_EQUALS,
                            field="line_number",
                            value=42,
                        ),
                    ),
                ],
            ),
            "error_b": ErrorDefinition(
                id="error_b",
                pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR B"),
                files=["file:///tmp/*.log"],
                meaning="Error B",
                context_lines=2,
                suggestion="Fix B",
                next_errors=[
                    ErrorCondition(
                        error_id="error_d",
                        when=ConditionSpec(type=ConditionType.ALWAYS),
                    ),
                ],
            ),
            "error_c": ErrorDefinition(
                id="error_c",
                pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR C"),
                files=["file:///tmp/*.log"],
                meaning="Error C",
                context_lines=2,
                suggestion="Fix C",
                next_errors=[
                    ErrorCondition(
                        error_id="error_d",
                        when=ConditionSpec(type=ConditionType.ALWAYS),
                    ),
                ],
            ),
            "error_d": ErrorDefinition(
                id="error_d",
                pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR D"),
                files=["file:///tmp/*.log"],
                meaning="Error D",
                context_lines=2,
                suggestion="Fix D",
                next_errors=[],
            ),
        },
    )


@pytest.fixture
def sample_oom_match():
    """Create a sample OOM error match."""
    return ErrorMatch(
        error_id="slurm_oom",
        file_uri="file:///var/log/slurm/node01.log",
        line_number=150,
        matched_text="slurmstepd: error: Exceeded job memory limit",
        context_before=["Job started", "Allocating resources"],
        context_after=["Job terminated", "Cleaning up"],
        timestamp=datetime(2025, 10, 8, 12, 0, 0),
        metadata={"hostname": "node01", "job_id": "12345"},
    )


@pytest.fixture
def sample_python_oom_match():
    """Create a sample OOM error match with Python in text."""
    return ErrorMatch(
        error_id="slurm_oom",
        file_uri="file:///var/log/slurm/node01.log",
        line_number=150,
        matched_text="slurmstepd: error: Exceeded job memory limit at python script",
        context_before=["Job started", "Allocating resources"],
        context_after=["Job terminated", "Cleaning up"],
        timestamp=datetime(2025, 10, 8, 12, 0, 0),
        metadata={"hostname": "node01", "job_id": "12345"},
    )


@pytest.fixture
def sample_error_a_match():
    """Create a sample error A match."""
    return ErrorMatch(
        error_id="error_a",
        file_uri="file:///tmp/test.log",
        line_number=42,
        matched_text="ERROR A occurred",
        context_before=["Starting process"],
        context_after=["Process failed"],
        timestamp=datetime(2025, 10, 8, 12, 0, 0),
        metadata={},
    )


@pytest.fixture
def railway_executor():
    """Create a RailwayExecutor instance."""
    return RailwayExecutor()


@pytest.fixture
def railway_planner():
    """Create a RailwayPlanner instance."""
    return RailwayPlanner()


# Test RailwayExecutor.get_next_errors


def test_get_next_errors_always(
    railway_executor, simple_catalog, sample_oom_match
):
    """Test getting next errors with ALWAYS condition."""
    error_def = simple_catalog.errors["slurm_oom"]
    next_errors = railway_executor.get_next_errors(
        sample_oom_match, error_def, simple_catalog
    )

    # Should return memory_leak_check (ALWAYS) but not python_error (conditional false)
    assert "memory_leak_check" in next_errors
    assert "python_error" not in next_errors


def test_get_next_errors_conditional_true(
    railway_executor, simple_catalog, sample_python_oom_match
):
    """Test getting next errors with conditional that evaluates to True."""
    error_def = simple_catalog.errors["slurm_oom"]
    next_errors = railway_executor.get_next_errors(
        sample_python_oom_match, error_def, simple_catalog
    )

    # Should return both memory_leak_check (ALWAYS) and python_error (conditional true)
    assert "memory_leak_check" in next_errors
    assert "python_error" in next_errors


def test_get_next_errors_conditional_false(
    railway_executor, simple_catalog, sample_oom_match
):
    """Test getting next errors with conditional that evaluates to False."""
    error_def = simple_catalog.errors["slurm_oom"]
    next_errors = railway_executor.get_next_errors(
        sample_oom_match, error_def, simple_catalog
    )

    # Should only return memory_leak_check (ALWAYS), not python_error
    assert "memory_leak_check" in next_errors
    assert "python_error" not in next_errors


def test_get_next_errors_no_match(
    railway_executor, simple_catalog, sample_oom_match
):
    """Test getting next errors when no conditions match."""
    # Create error definition with only failing conditions
    error_def = ErrorDefinition(
        id="test_error",
        pattern=PatternMatcher(type=PatternType.LITERAL, pattern="test"),
        files=["file:///tmp/*.log"],
        meaning="Test",
        context_lines=2,
        suggestion="Test",
        next_errors=[
            ErrorCondition(
                error_id="never_error",
                when=ConditionSpec(
                    type=ConditionType.FIELD_EQUALS, field="line_number", value=999
                ),
            ),
        ],
    )

    next_errors = railway_executor.get_next_errors(
        sample_oom_match, error_def, simple_catalog
    )

    # Should return empty list
    assert next_errors == []


def test_get_next_errors_no_railway(
    railway_executor, simple_catalog, sample_oom_match
):
    """Test getting next errors when error has no next_errors."""
    error_def = simple_catalog.errors["memory_leak_check"]
    next_errors = railway_executor.get_next_errors(
        sample_oom_match, error_def, simple_catalog
    )

    # Should return empty list
    assert next_errors == []


def test_get_next_errors_multiple_conditions(
    railway_executor, complex_catalog, sample_error_a_match
):
    """Test getting next errors with multiple conditions."""
    error_def = complex_catalog.errors["error_a"]
    next_errors = railway_executor.get_next_errors(
        sample_error_a_match, error_def, complex_catalog
    )

    # Should return both error_b (ALWAYS) and error_c (line_number == 42)
    assert "error_b" in next_errors
    assert "error_c" in next_errors


def test_get_next_errors_preserves_order(
    railway_executor, simple_catalog, sample_python_oom_match
):
    """Test that get_next_errors preserves order of next_errors list."""
    error_def = simple_catalog.errors["slurm_oom"]
    next_errors = railway_executor.get_next_errors(
        sample_python_oom_match, error_def, simple_catalog
    )

    # Should preserve order: memory_leak_check, then python_error
    assert next_errors == ["memory_leak_check", "python_error"]


# Test RailwayPlanner.build_execution_plan


def test_build_execution_plan_simple(railway_planner, simple_catalog):
    """Test building execution plan for simple catalog."""
    plan = railway_planner.build_execution_plan("slurm_oom", simple_catalog)

    # Should include all potential paths
    assert "slurm_oom" in plan
    assert set(plan["slurm_oom"]) == {"memory_leak_check", "python_error"}

    # Leaf nodes should be in plan with empty lists
    assert "memory_leak_check" in plan
    assert plan["memory_leak_check"] == []

    assert "python_error" in plan
    assert plan["python_error"] == []


def test_build_execution_plan_complex(railway_planner, complex_catalog):
    """Test building execution plan for complex catalog with nested chains."""
    plan = railway_planner.build_execution_plan("error_a", complex_catalog)

    # Should include full DAG
    assert "error_a" in plan
    assert set(plan["error_a"]) == {"error_b", "error_c"}

    assert "error_b" in plan
    assert plan["error_b"] == ["error_d"]

    assert "error_c" in plan
    assert plan["error_c"] == ["error_d"]

    assert "error_d" in plan
    assert plan["error_d"] == []


def test_build_execution_plan_single_node(railway_planner, simple_catalog):
    """Test building execution plan for error with no next_errors."""
    plan = railway_planner.build_execution_plan("memory_leak_check", simple_catalog)

    # Should only contain the starting node
    assert plan == {"memory_leak_check": []}


def test_build_execution_plan_prevents_infinite_loop(railway_planner):
    """Test that build_execution_plan handles circular dependencies."""
    # Create catalog with circular dependency
    circular_catalog = ErrorCatalog(
        version="1.0.0",
        schema_version="1.0.0",
        metadata=CatalogMetadata(
            name="Circular Test Catalog",
            description="Catalog with circular dependencies",
            author="Test Author",
            created=datetime(2025, 1, 1, 0, 0, 0),
            updated=datetime(2025, 1, 1, 0, 0, 0),
        ),
        errors={
            "error_x": ErrorDefinition(
                id="error_x",
                pattern=PatternMatcher(type=PatternType.LITERAL, pattern="X"),
                files=["file:///tmp/*.log"],
                meaning="Error X",
                context_lines=2,
                suggestion="Fix X",
                next_errors=[
                    ErrorCondition(
                        error_id="error_y",
                        when=ConditionSpec(type=ConditionType.ALWAYS),
                    ),
                ],
            ),
            "error_y": ErrorDefinition(
                id="error_y",
                pattern=PatternMatcher(type=PatternType.LITERAL, pattern="Y"),
                files=["file:///tmp/*.log"],
                meaning="Error Y",
                context_lines=2,
                suggestion="Fix Y",
                next_errors=[
                    ErrorCondition(
                        error_id="error_x",
                        when=ConditionSpec(type=ConditionType.ALWAYS),
                    ),
                ],
            ),
        },
    )

    plan = railway_planner.build_execution_plan("error_x", circular_catalog)

    # Should handle circular dependency gracefully
    assert "error_x" in plan
    assert "error_y" in plan
    # Should not infinite loop


def test_railway_chain_depth(railway_planner, complex_catalog):
    """Test that railway planner handles multi-level chains correctly."""
    plan = railway_planner.build_execution_plan("error_a", complex_catalog)

    # Verify the depth of the chain
    # error_a -> error_b -> error_d
    # error_a -> error_c -> error_d
    assert len(plan) == 4  # error_a, error_b, error_c, error_d

    # Verify all nodes are reachable
    visited = set()
    to_visit = ["error_a"]

    while to_visit:
        current = to_visit.pop(0)
        if current in visited:
            continue
        visited.add(current)
        to_visit.extend(plan[current])

    assert visited == {"error_a", "error_b", "error_c", "error_d"}


def test_build_execution_plan_nonexistent_error(railway_planner, simple_catalog):
    """Test building execution plan for non-existent error ID."""
    plan = railway_planner.build_execution_plan("nonexistent_error", simple_catalog)

    # Should return empty plan
    assert plan == {}


def test_get_next_errors_invalid_error_id_in_condition(
    railway_executor, simple_catalog, sample_oom_match
):
    """Test get_next_errors when condition references non-existent error."""
    # Create error definition with invalid next error ID
    error_def = ErrorDefinition(
        id="test_error",
        pattern=PatternMatcher(type=PatternType.LITERAL, pattern="test"),
        files=["file:///tmp/*.log"],
        meaning="Test",
        context_lines=2,
        suggestion="Test",
        next_errors=[
            ErrorCondition(
                error_id="nonexistent_error",
                when=ConditionSpec(type=ConditionType.ALWAYS),
            ),
        ],
    )

    next_errors = railway_executor.get_next_errors(
        sample_oom_match, error_def, simple_catalog
    )

    # Should still return the error_id (validation is done elsewhere)
    assert "nonexistent_error" in next_errors
