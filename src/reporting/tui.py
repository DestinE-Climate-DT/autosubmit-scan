"""Textual TUI for interactive error report viewing.

Provides a terminal user interface for browsing error matches
with hierarchical tree view and detailed information panels.
"""

import json
from pathlib import Path
from typing import Dict, Any

from textual.app import App, ComposeResult
from textual.widgets import Tree, Static, Footer, Header
from textual.containers import Container, Horizontal
from textual.binding import Binding


class ErrorReportApp(App):
    """TUI application for viewing error reports.

    Features:
    - Hierarchical tree view of errors (by type and file)
    - Detail panel showing match information
    - Keyboard navigation
    """

    CSS_PATH = "tui.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("/", "search", "Search"),
        Binding("f", "filter", "Filter"),
        Binding("e", "export", "Export"),
    ]

    def __init__(self, report_path: str):
        """Initialize the TUI app.

        Args:
            report_path: Path to JSON-LD report file
        """
        super().__init__()
        self.report_path = report_path
        self.report_data: Dict[str, Any] = {}

    def on_mount(self) -> None:
        """Load report data when app mounts."""
        with open(self.report_path, "r", encoding="utf-8") as f:
            self.report_data = json.load(f)

        # Populate tree with report data
        tree = self.query_one(Tree)
        self._populate_tree(tree)

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()

        with Horizontal():
            # Left side: Tree view of errors
            tree = Tree("Error Report")
            tree.root.expand()
            yield tree

            # Right side: Detail panel
            yield Container(
                Static("Select an error to view details", id="detail"),
                id="detail-panel"
            )

        yield Footer()

    def _populate_tree(self, tree: Tree) -> None:
        """Populate tree with error report data.

        Args:
            tree: Tree widget to populate
        """
        if "hasPart" not in self.report_data:
            return

        # Group matches by error type
        errors_by_type: Dict[str, list] = {}
        for match in self.report_data["hasPart"]:
            error_id = match.get("errorDefinition", "unknown")
            if error_id not in errors_by_type:
                errors_by_type[error_id] = []
            errors_by_type[error_id].append(match)

        # Add error types to tree
        for error_type, matches in errors_by_type.items():
            type_node = tree.root.add(f"{error_type} ({len(matches)} matches)")

            # Group matches by file
            files: Dict[str, list] = {}
            for match in matches:
                file_uri = match.get("url", "unknown")
                if file_uri not in files:
                    files[file_uri] = []
                files[file_uri].append(match)

            # Add files to tree
            for file_uri, file_matches in files.items():
                file_node = type_node.add(f"{Path(file_uri).name} ({len(file_matches)} matches)")

                # Add individual matches
                for match in file_matches:
                    line = match.get("position", "?")
                    text = match.get("text", "")[:50]  # Truncate long text
                    match_node = file_node.add(f"Line {line}: {text}")
                    match_node.data = match  # Store match data for detail view

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection.

        Args:
            event: Tree selection event
        """
        node = event.node

        # Get match data if available
        if hasattr(node, "data") and node.data:
            match = node.data
            detail_text = self._format_match_details(match)
        else:
            detail_text = f"Selected: {node.label}"

        # Update detail panel
        detail_panel = self.query_one("#detail", Static)
        detail_panel.update(detail_text)

    def _format_match_details(self, match: Dict[str, Any]) -> str:
        """Format match details for display.

        Args:
            match: Match dictionary from JSON-LD

        Returns:
            Formatted string for detail panel
        """
        lines = []
        lines.append(f"[bold]Error:[/bold] {match.get('errorDefinition', 'unknown')}")
        lines.append(f"[bold]File:[/bold] {match.get('url', 'unknown')}")
        lines.append(f"[bold]Line:[/bold] {match.get('position', '?')}")
        lines.append(f"[bold]Date:[/bold] {match.get('dateFound', 'unknown')}")
        lines.append("")
        lines.append("[bold]Matched Text:[/bold]")
        lines.append(match.get("text", ""))
        lines.append("")

        if "about" in match:
            about = match["about"]
            lines.append("[bold]Meaning:[/bold]")
            lines.append(about.get("headline", ""))
            lines.append("")
            lines.append("[bold]Suggestion:[/bold]")
            lines.append(about.get("description", ""))
            lines.append("")

        if "context" in match:
            context = match["context"]
            if context.get("before"):
                lines.append("[bold]Context Before:[/bold]")
                for line in context["before"]:
                    lines.append(f"  {line}")
                lines.append("")

            if context.get("after"):
                lines.append("[bold]Context After:[/bold]")
                for line in context["after"]:
                    lines.append(f"  {line}")

        return "\n".join(lines)

    def action_search(self) -> None:
        """Handle search action."""
        self.bell()  # Placeholder - would implement search in full version

    def action_filter(self) -> None:
        """Handle filter action."""
        self.bell()  # Placeholder - would implement filtering in full version

    def action_export(self) -> None:
        """Handle export action."""
        self.bell()  # Placeholder - would implement export in full version
