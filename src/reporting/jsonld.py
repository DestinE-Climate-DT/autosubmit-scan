"""JSON-LD report generator following Schema.org vocabulary.

This module provides functionality to convert error matches into
JSON-LD format following Schema.org conventions with custom extensions.
"""

import uuid
from datetime import datetime
from typing import Any

from src.domain.models import ErrorCatalog, ErrorMatch


class ReportGenerator:
    """Generates JSON-LD reports from error matches.

    Creates reports following Schema.org vocabulary with custom
    error_scan extensions.
    """

    def generate_report(self, matches: list[ErrorMatch], catalog: ErrorCatalog, metadata: dict[str, Any]) -> dict[str, Any]:
        """Generate a JSON-LD report from error matches.

        Args:
            matches: List of ErrorMatch instances
            catalog: ErrorCatalog containing error definitions
            metadata: Additional metadata (author, description, catalog_uri, catalog_retrieved_date, etc.)

        Returns:
            JSON-LD report as a dictionary
        """
        report_id = f"urn:uuid:{uuid.uuid4()}"
        now = datetime.now().isoformat() + "Z"

        # Calculate summary statistics
        summary = self._calculate_summary(matches)

        # Build error definitions array for embedding
        error_definitions = self._build_error_definitions(matches, catalog)

        # Convert matches to JSON-LD
        jsonld_matches = []
        for match in matches:
            jsonld_match = self._match_to_jsonld(match, catalog)
            jsonld_matches.append(jsonld_match)

        # Build author information
        author_info = metadata.get("author", {})
        author = {"@type": "Person", "name": author_info.get("name", "Unknown"), "email": author_info.get("email", "")}

        # Build catalog reference
        catalog_ref = {
            "@id": metadata.get("catalog_uri", "unknown"),
            "@type": "ErrorCatalog",
            "version": catalog.version,
            "dateRetrieved": metadata.get("catalog_retrieved_date", now),
        }

        # Build complete report
        report = {
            "@context": {
                "@vocab": "https://schema.org/",
                "as": "https://destine-climate-dt.github.io/autosubmit-scan/schema#",
                "ErrorReport": "as:ErrorReport",
                "ErrorMatch": "as:ErrorMatch",
                "ErrorDefinition": "as:ErrorDefinition",
                "ErrorCatalog": "as:ErrorCatalog",
            },
            "@type": "ErrorReport",
            "@id": report_id,
            "version": "1.0.0",
            "dateCreated": now,
            "author": author,
            "catalog": catalog_ref,
            "summary": summary,
            "defines": error_definitions,
            "hasPart": jsonld_matches,
        }

        return report

    def _calculate_summary(self, matches: list[ErrorMatch]) -> dict[str, Any]:
        """Calculate summary statistics from matches.

        Args:
            matches: List of ErrorMatch instances

        Returns:
            Dictionary with summary statistics
        """
        if not matches:
            return {"totalMatches": 0, "errorTypes": 0, "filesScanned": 0, "hostsScanned": []}

        # Count unique error types
        error_types = set(m.error_id for m in matches)

        # Count unique files
        files = set(m.file_uri for m in matches)

        # Extract unique hosts from metadata
        hosts = set()
        for match in matches:
            if "host" in match.metadata:
                hosts.add(match.metadata["host"])

        return {
            "totalMatches": len(matches),
            "errorTypes": len(error_types),
            "filesScanned": len(files),
            "hostsScanned": sorted(list(hosts)),
        }

    def _build_error_definitions(self, matches: list[ErrorMatch], catalog: ErrorCatalog) -> list[dict[str, Any]]:
        """Build error definitions array for embedding in report.

        Args:
            matches: List of ErrorMatch instances
            catalog: ErrorCatalog containing error definitions

        Returns:
            List of ErrorDefinition objects referenced by matches
        """
        # Get unique error IDs from matches
        error_ids = set(m.error_id for m in matches)

        definitions = []
        for error_id in sorted(error_ids):
            error_def = catalog.errors.get(error_id)
            if error_def:
                definitions.append(
                    {
                        "@type": "ErrorDefinition",
                        "@id": f"#{error_id}",
                        "identifier": error_id,
                        "meaning": error_def.meaning,
                        "suggestion": error_def.suggestion,
                    }
                )
            else:
                # Fallback for missing definitions
                definitions.append(
                    {
                        "@type": "ErrorDefinition",
                        "@id": f"#{error_id}",
                        "identifier": error_id,
                        "meaning": f"Error {error_id}",
                        "suggestion": "No suggestion available",
                    }
                )

        return definitions

    def _match_to_jsonld(self, match: ErrorMatch, catalog: ErrorCatalog) -> dict[str, Any]:
        """Convert an ErrorMatch to JSON-LD format.

        Args:
            match: ErrorMatch instance
            catalog: ErrorCatalog for looking up error definitions

        Returns:
            JSON-LD representation of the match
        """
        match_id = f"urn:uuid:{uuid.uuid4()}"

        # Build context
        context = {"before": match.context_before, "after": match.context_after}

        # Convert timestamp to ISO format
        timestamp_iso = match.timestamp.isoformat() + "Z"

        # Build metadata object
        metadata_obj = {
            "host": match.metadata.get("host", "unknown"),
            "experiment_id": match.metadata.get("experiment_id", "unknown"),
        }

        jsonld_match = {
            "@type": "ErrorMatch",
            "@id": match_id,
            "errorDefinition": {"@id": f"#{match.error_id}"},
            "url": match.file_uri,
            "lineNumber": match.line_number,
            "text": match.matched_text,
            "dateFound": timestamp_iso,
            "context": context,
            "metadata": metadata_obj,
        }

        return jsonld_match

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
