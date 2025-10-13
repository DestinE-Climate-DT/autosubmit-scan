"""Reporting module for error scan results.

This module provides:
- JSON-LD report generation following Schema.org
- Report aggregation and statistics
- Jinja2 template rendering
- Textual TUI for interactive viewing
"""

from src.reporting.aggregator import ReportAggregator
from src.reporting.jsonld import ReportGenerator
from src.reporting.templates import TemplateRenderer

__all__ = [
    "ReportGenerator",
    "ReportAggregator",
    "TemplateRenderer",
]
