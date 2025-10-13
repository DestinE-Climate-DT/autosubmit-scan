"""Report aggregator for loading and organizing error matches.

This module provides functionality to:
- Load error matches from JSON files
- Group matches by error type or file
- Calculate summary statistics
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.domain.models import ErrorMatch


class ReportAggregator:
    """Aggregates and organizes error matches for reporting.

    Provides methods to load matches from files, group them by various
    criteria, and calculate statistics.
    """

    def load_matches_from_files(self, file_paths: list[str]) -> list[ErrorMatch]:
        """Load error matches from JSON files.

        Args:
            file_paths: List of file paths to load matches from

        Returns:
            List of ErrorMatch instances

        Raises:
            FileNotFoundError: If a file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        matches = []

        for file_path in file_paths:
            path = Path(file_path)

            if not path.exists():
                raise FileNotFoundError(f"Match file not found: {file_path}")

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            # Convert timestamp string to datetime if needed
            if "timestamp" in data and isinstance(data["timestamp"], str):
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])

            match = ErrorMatch(**data)
            matches.append(match)

        return matches

    def group_by_error(self, matches: list[ErrorMatch]) -> dict[str, list[ErrorMatch]]:
        """Group matches by error_id.

        Args:
            matches: List of ErrorMatch instances

        Returns:
            Dictionary mapping error_id to list of matches
        """
        grouped: dict[str, list[ErrorMatch]] = {}

        for match in matches:
            if match.error_id not in grouped:
                grouped[match.error_id] = []
            grouped[match.error_id].append(match)

        return grouped

    def group_by_file(self, matches: list[ErrorMatch]) -> dict[str, list[ErrorMatch]]:
        """Group matches by file_uri, sorted by line_number.

        Args:
            matches: List of ErrorMatch instances

        Returns:
            Dictionary mapping file_uri to sorted list of matches
        """
        grouped: dict[str, list[ErrorMatch]] = {}

        for match in matches:
            if match.file_uri not in grouped:
                grouped[match.file_uri] = []
            grouped[match.file_uri].append(match)

        # Sort matches within each file by line number
        for file_uri in grouped:
            grouped[file_uri].sort(key=lambda m: m.line_number)

        return grouped

    def calculate_statistics(self, matches: list[ErrorMatch]) -> dict[str, Any]:
        """Calculate summary statistics from matches.

        Args:
            matches: List of ErrorMatch instances

        Returns:
            Dictionary with statistics including:
            - total_matches: Total number of matches
            - unique_errors: Number of unique error types
            - unique_files: Number of unique files
            - unique_hosts: Number of unique hosts
            - errors_by_type: Count of matches per error type
            - files_by_error: List of files affected by each error
        """
        if not matches:
            return {
                "total_matches": 0,
                "unique_errors": 0,
                "unique_files": 0,
                "unique_hosts": 0,
                "errors_by_type": {},
                "files_by_error": {},
            }

        # Collect unique values
        error_ids = set()
        file_uris = set()
        hosts = set()

        # Count errors by type
        errors_by_type: dict[str, int] = {}

        # Track files by error
        files_by_error: dict[str, set] = {}

        for match in matches:
            error_ids.add(match.error_id)
            file_uris.add(match.file_uri)

            # Extract host from metadata if available
            if "host" in match.metadata:
                hosts.add(match.metadata["host"])

            # Count errors by type
            if match.error_id not in errors_by_type:
                errors_by_type[match.error_id] = 0
            errors_by_type[match.error_id] += 1

            # Track files by error
            if match.error_id not in files_by_error:
                files_by_error[match.error_id] = set()
            files_by_error[match.error_id].add(match.file_uri)

        # Convert sets to lists for JSON serialization
        files_by_error_list = {error_id: list(files) for error_id, files in files_by_error.items()}

        return {
            "total_matches": len(matches),
            "unique_errors": len(error_ids),
            "unique_files": len(file_uris),
            "unique_hosts": len(hosts),
            "errors_by_type": errors_by_type,
            "files_by_error": files_by_error_list,
        }
