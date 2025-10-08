"""JSON-LD report generator following Schema.org vocabulary.

This module provides functionality to convert error matches into
JSON-LD format following Schema.org conventions with custom extensions.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any

from src.domain.models import ErrorMatch, ErrorCatalog


class ReportGenerator:
    """Generates JSON-LD reports from error matches.

    Creates reports following Schema.org vocabulary with custom
    error_scan extensions.
    """

    def generate_report(
        self,
        matches: List[ErrorMatch],
        catalog: ErrorCatalog,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a JSON-LD report from error matches.

        Args:
            matches: List of ErrorMatch instances
            catalog: ErrorCatalog containing error definitions
            metadata: Additional metadata (author, description, etc.)

        Returns:
            JSON-LD report as a dictionary
        """
        report_id = f"urn:uuid:{uuid.uuid4()}"
        now = datetime.now().isoformat() + "Z"

        # Calculate summary statistics
        summary = self._calculate_summary(matches)

        # Convert matches to JSON-LD
        jsonld_matches = []
        for match in matches:
            jsonld_match = self._match_to_jsonld(match, catalog)
            jsonld_matches.append(jsonld_match)

        # Build author information
        author_info = metadata.get("author", {})
        author = {
            "@type": "Person",
            "name": author_info.get("name", "Unknown"),
            "email": author_info.get("email", "")
        }

        # Build complete report
        report = {
            "@context": {
                "@vocab": "https://schema.org/",
                "error_scan": "https://destine.example/error-scan/schema#"
            },
            "@type": "ErrorReport",
            "@id": report_id,
            "version": "1.0.0",
            "dateCreated": now,
            "author": author,
            "summary": summary,
            "hasPart": jsonld_matches
        }

        return report

    def _calculate_summary(self, matches: List[ErrorMatch]) -> Dict[str, Any]:
        """Calculate summary statistics from matches.

        Args:
            matches: List of ErrorMatch instances

        Returns:
            Dictionary with summary statistics
        """
        if not matches:
            return {
                "totalMatches": 0,
                "errorTypes": 0,
                "filesScanned": 0,
                "hostsScanned": []
            }

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
            "hostsScanned": sorted(list(hosts))
        }

    def _match_to_jsonld(
        self,
        match: ErrorMatch,
        catalog: ErrorCatalog
    ) -> Dict[str, Any]:
        """Convert an ErrorMatch to JSON-LD format.

        Args:
            match: ErrorMatch instance
            catalog: ErrorCatalog for looking up error definitions

        Returns:
            JSON-LD representation of the match
        """
        match_id = f"urn:uuid:{uuid.uuid4()}"

        # Get error definition from catalog
        error_def = catalog.errors.get(match.error_id)

        # Build about section with error definition details
        if error_def:
            about = {
                "@type": "CreativeWork",
                "headline": error_def.meaning,
                "description": error_def.suggestion
            }
        else:
            # Fallback for missing error definitions
            about = {
                "@type": "CreativeWork",
                "headline": f"Error {match.error_id}",
                "description": "No description available"
            }

        # Build context
        context = {
            "before": match.context_before,
            "after": match.context_after
        }

        # Convert timestamp to ISO format
        timestamp_iso = match.timestamp.isoformat() + "Z"

        jsonld_match = {
            "@type": "ErrorMatch",
            "@id": match_id,
            "errorDefinition": match.error_id,
            "url": match.file_uri,
            "position": match.line_number,
            "text": match.matched_text,
            "dateFound": timestamp_iso,
            "about": about,
            "context": context
        }

        return jsonld_match

    def group_by_error(self, matches: List[ErrorMatch]) -> Dict[str, List[ErrorMatch]]:
        """Group matches by error_id.

        Args:
            matches: List of ErrorMatch instances

        Returns:
            Dictionary mapping error_id to list of matches
        """
        grouped: Dict[str, List[ErrorMatch]] = {}

        for match in matches:
            if match.error_id not in grouped:
                grouped[match.error_id] = []
            grouped[match.error_id].append(match)

        return grouped

    def group_by_file(self, matches: List[ErrorMatch]) -> Dict[str, List[ErrorMatch]]:
        """Group matches by file_uri, sorted by line_number.

        Args:
            matches: List of ErrorMatch instances

        Returns:
            Dictionary mapping file_uri to sorted list of matches
        """
        grouped: Dict[str, List[ErrorMatch]] = {}

        for match in matches:
            if match.file_uri not in grouped:
                grouped[match.file_uri] = []
            grouped[match.file_uri].append(match)

        # Sort matches within each file by line number
        for file_uri in grouped:
            grouped[file_uri].sort(key=lambda m: m.line_number)

        return grouped
