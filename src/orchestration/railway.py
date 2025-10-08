"""Railway pattern executor and planner.

This module provides the railway pattern execution logic:
- RailwayExecutor: Evaluates conditions and returns next errors to check
- RailwayPlanner: Builds DAG of potential error chains for Snakemake
"""

from typing import List, Dict, Set
from src.domain.models import ErrorMatch, ErrorDefinition, ErrorCatalog
from src.orchestration.conditions import ConditionEvaluator


class RailwayExecutor:
    """Executes railway pattern for error chaining.

    Evaluates conditions on ErrorMatch instances to determine which
    errors should be checked next.
    """

    def __init__(self):
        """Initialize RailwayExecutor with a ConditionEvaluator."""
        self.evaluator = ConditionEvaluator()

    def get_next_errors(
        self,
        error_match: ErrorMatch,
        error_def: ErrorDefinition,
        catalog: ErrorCatalog,
    ) -> List[str]:
        """Get list of next error IDs to check based on conditions.

        Evaluates all conditions in error_def.next_errors and returns
        the error IDs whose conditions are satisfied.

        Args:
            error_match: The error match to evaluate conditions against
            error_def: The error definition containing next_errors
            catalog: The error catalog (for custom callables)

        Returns:
            List of error IDs that should be checked next, in order

        Examples:
            >>> executor = RailwayExecutor()
            >>> next_errors = executor.get_next_errors(match, error_def, catalog)
            >>> print(next_errors)
            ['memory_leak_check', 'python_error']
        """
        next_error_ids = []

        for error_condition in error_def.next_errors:
            # Evaluate the condition
            if self.evaluator.evaluate(
                error_condition.when, error_match, catalog
            ):
                next_error_ids.append(error_condition.error_id)

        return next_error_ids


class RailwayPlanner:
    """Plans railway pattern execution by building DAG.

    Builds a directed acyclic graph (DAG) of potential error chains
    for Snakemake workflow generation.
    """

    def build_execution_plan(
        self, initial_error_id: str, catalog: ErrorCatalog
    ) -> Dict[str, List[str]]:
        """Build execution plan DAG for error chains.

        Traverses the error catalog starting from initial_error_id
        and builds a map of all reachable errors and their potential
        next errors.

        Args:
            initial_error_id: The starting error ID
            catalog: The error catalog

        Returns:
            Dictionary mapping error_id to list of potential next error IDs

        Examples:
            >>> planner = RailwayPlanner()
            >>> plan = planner.build_execution_plan("slurm_oom", catalog)
            >>> print(plan)
            {
                "slurm_oom": ["memory_leak_check", "python_error"],
                "memory_leak_check": [],
                "python_error": []
            }
        """
        # Check if initial error exists in catalog
        if initial_error_id not in catalog.errors:
            return {}

        plan: Dict[str, List[str]] = {}
        visited: Set[str] = set()
        to_visit: List[str] = [initial_error_id]

        while to_visit:
            current_error_id = to_visit.pop(0)

            # Skip if already visited (prevents infinite loops)
            if current_error_id in visited:
                continue

            visited.add(current_error_id)

            # Get error definition
            if current_error_id not in catalog.errors:
                # Referenced error doesn't exist in catalog
                # Add to plan with empty list and continue
                plan[current_error_id] = []
                continue

            error_def = catalog.errors[current_error_id]

            # Extract all potential next error IDs (regardless of conditions)
            next_error_ids = [
                error_condition.error_id for error_condition in error_def.next_errors
            ]

            # Add to plan
            plan[current_error_id] = next_error_ids

            # Add next errors to visit queue
            for next_error_id in next_error_ids:
                if next_error_id not in visited:
                    to_visit.append(next_error_id)

        return plan
