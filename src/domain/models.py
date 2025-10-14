"""Domain models for error scanning system.

This module defines the core domain entities using Pydantic v2:
- PatternType: Enum for pattern matcher types
- ConditionType: Enum for condition types
- PatternMatcher: Pattern matching configuration
- ConditionSpec: Condition specification with nested logic
- ErrorCondition: Railway pattern for chaining errors
- CatalogMetadata: Catalog metadata
- ErrorDefinition: Error definition with patterns and actions
- ErrorMatch: Runtime error match instance
- ErrorCatalog: Complete error catalog
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from src.domain.validation import (
    validate_callable_string,
    validate_non_negative_int,
    validate_positive_int,
    validate_semver,
    validate_uri,
)


class PatternType(str, Enum):
    """Type of pattern matcher."""

    LITERAL = "literal"
    REGEX = "regex"
    CALLABLE = "callable"


class ConditionType(str, Enum):
    """Type of condition for railway pattern."""

    ALWAYS = "always"
    AND = "and"
    OR = "or"
    CUSTOM = "custom"
    FIELD_EQUALS = "field_equals"
    FIELD_CONTAINS = "field_contains"
    FIELD_REGEX = "field_regex"


class PatternMatcher(BaseModel):
    """Pattern matcher configuration.

    Supports three types of patterns:
    - literal: Exact string match
    - regex: Regular expression match
    - callable: Custom function (module:function format)
    """

    model_config = {"validate_assignment": True}

    type: PatternType = Field(..., description="Type of pattern matcher")
    pattern: str = Field(..., description="Pattern string or callable reference")
    flags: list[str] | None = Field(None, description="Regex flags (IGNORECASE, MULTILINE, etc.)")

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, v: str, info) -> str:
        """Validate pattern based on type."""
        # Get the type from the values being validated
        pattern_type = info.data.get("type")

        if pattern_type == PatternType.CALLABLE:
            return validate_callable_string(v)

        if not v:
            raise ValueError("Pattern cannot be empty")

        return v


class ConditionSpec(BaseModel):
    """Condition specification for railway pattern.

    Supports:
    - Simple conditions: ALWAYS, CUSTOM
    - Logical operators: AND, OR (with nested conditions)
    - Field operations: FIELD_EQUALS, FIELD_CONTAINS, FIELD_REGEX
    """

    model_config = {"validate_assignment": True}

    type: ConditionType = Field(..., description="Type of condition")
    conditions: list["ConditionSpec"] | None = Field(None, description="Nested conditions for AND/OR")
    callable: str | None = Field(None, description="Callable reference for CUSTOM (module:function)")
    field: str | None = Field(None, description="Field name for FIELD_* operations")
    operator: str | None = Field(None, description="Operator for FIELD_* operations")
    value: Any | None = Field(None, description="Value for FIELD_* operations")

    @field_validator("callable")
    @classmethod
    def validate_callable(cls, v: str | None) -> str | None:
        """Validate callable string format."""
        if v is not None:
            return validate_callable_string(v)
        return v

    @model_validator(mode="after")
    def validate_condition_requirements(self) -> "ConditionSpec":
        """Validate that required fields are present based on condition type."""
        if self.type in (ConditionType.AND, ConditionType.OR):
            if not self.conditions:
                raise ValueError(f"{self.type.value} condition requires 'conditions' list")

        if self.type == ConditionType.CUSTOM:
            if not self.callable:
                raise ValueError("CUSTOM condition requires 'callable' field")

        if self.type in (
            ConditionType.FIELD_EQUALS,
            ConditionType.FIELD_CONTAINS,
            ConditionType.FIELD_REGEX,
        ):
            if not self.field:
                raise ValueError(f"{self.type.value} condition requires 'field'")
            if self.value is None:
                raise ValueError(f"{self.type.value} condition requires 'value'")

        return self


class ErrorCondition(BaseModel):
    """Error condition for railway pattern.

    Links to the next error to check when a condition is met.
    """

    model_config = {"validate_assignment": True}

    error_id: str = Field(..., description="ID of the next error to check")
    when: ConditionSpec = Field(..., description="Condition for triggering next error")


class VariableExtractor(BaseModel):
    """Configuration for extracting a variable from a file.

    Supports extracting values from local files using various methods:
    - regex: Extract using regular expression pattern (group 1 or named 'value')
    - line: Extract specific line number
    - json_path: Extract from JSON file using JSONPath expression
    - yaml_path: Extract from YAML file using dot notation path (e.g., 'config.platforms.host')
    """

    model_config = {"validate_assignment": True}

    source: str = Field("file", description="Source type (currently only 'file' supported)")
    path: str = Field(..., description="Path to local file to read")
    method: str = Field("regex", description="Extraction method: 'regex', 'line', 'json_path', 'yaml_path'")
    pattern: str | None = Field(None, description="Pattern for regex extraction, JSONPath, or YAML path")
    line_number: int | None = Field(None, description="Line number for 'line' method (1-indexed)")
    default: str | None = Field(None, description="Default value if extraction fails")
    strip: bool = Field(True, description="Strip whitespace from extracted value")

    @model_validator(mode="after")
    def validate_method_parameters(self) -> "VariableExtractor":
        """Validate that required parameters are present for each method."""
        if self.method == "regex" and not self.pattern:
            raise ValueError("'pattern' is required when method is 'regex'")
        if self.method == "line" and self.line_number is None:
            raise ValueError("'line_number' is required when method is 'line'")
        if self.method == "json_path" and not self.pattern:
            raise ValueError("'pattern' (JSONPath) is required when method is 'json_path'")
        if self.method == "yaml_path" and not self.pattern:
            raise ValueError("'pattern' (YAML path) is required when method is 'yaml_path'")
        if self.method not in ["regex", "line", "json_path", "yaml_path"]:
            raise ValueError(f"Invalid method: {self.method}. Must be 'regex', 'line', 'json_path', or 'yaml_path'")
        return self


class CatalogMetadata(BaseModel):
    """Metadata for error catalog."""

    model_config = {"validate_assignment": True}

    name: str = Field(..., description="Catalog name")
    description: str = Field(..., description="Catalog description")
    author: str = Field(..., description="Catalog author")
    created: datetime = Field(..., description="Creation timestamp")
    updated: datetime = Field(..., description="Last update timestamp")
    variables: dict[str, VariableExtractor] | None = Field(
        None, description="Dynamic variable extractors for template rendering"
    )


class ErrorDefinition(BaseModel):
    """Error definition with pattern, files, and actions.

    Defines:
    - What to look for (pattern)
    - Where to look (files)
    - What it means (meaning)
    - How much context to capture (context_lines)
    - What to do about it (suggestion)
    - What to check next (next_errors - railway pattern)
    """

    model_config = {"validate_assignment": True}

    id: str = Field(..., description="Unique error identifier")
    pattern: PatternMatcher = Field(..., description="Pattern to match")
    files: list[str] = Field(..., description="File URIs or patterns (fsspec compatible)")
    meaning: str = Field(..., description="Human-readable error description")
    context_lines: int = Field(..., description="Number of context lines to capture")
    suggestion: str = Field(..., description="Suggested action")
    next_errors: list[ErrorCondition] = Field(default_factory=list, description="Next errors to check (railway pattern)")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata (tags, severity, etc.)")

    @field_validator("files")
    @classmethod
    def validate_files_not_empty(cls, v: list[str]) -> list[str]:
        """Validate that files list is not empty."""
        if not v:
            raise ValueError("Files list cannot be empty")
        return v

    @field_validator("files")
    @classmethod
    def validate_file_uris(cls, v: list[str]) -> list[str]:
        """Validate each file URI."""
        for uri in v:
            validate_uri(uri)
        return v

    @field_validator("context_lines")
    @classmethod
    def validate_context_lines(cls, v: int) -> int:
        """Validate that context_lines is non-negative."""
        return validate_non_negative_int(v)


class ErrorMatch(BaseModel):
    """Runtime error match instance.

    Created when a pattern matches in a file.
    """

    model_config = {"validate_assignment": True}

    error_id: str = Field(..., description="ID of the matched error definition")
    file_uri: str = Field(..., description="URI of the file where match occurred")
    line_number: int = Field(..., description="Line number of the match (1-indexed)")
    matched_text: str = Field(..., description="Text that matched the pattern")
    context_before: list[str] = Field(default_factory=list, description="Lines before the match")
    context_after: list[str] = Field(default_factory=list, description="Lines after the match")
    timestamp: datetime = Field(..., description="When the match was found")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional match metadata")

    @field_validator("file_uri")
    @classmethod
    def validate_file_uri(cls, v: str) -> str:
        """Validate file URI."""
        return validate_uri(v)

    @field_validator("line_number")
    @classmethod
    def validate_line_number(cls, v: int) -> int:
        """Validate that line_number is positive (>= 1)."""
        return validate_positive_int(v)


class ErrorCatalog(BaseModel):
    """Complete error catalog.

    Contains:
    - Version information (semver)
    - Metadata
    - Error definitions
    """

    model_config = {"validate_assignment": True}

    version: str = Field(..., description="Catalog content version (semver)")
    schema_version: str = Field(..., description="Catalog format version (semver)")
    metadata: CatalogMetadata = Field(..., description="Catalog metadata")
    errors: dict[str, ErrorDefinition] = Field(default_factory=dict, description="Error definitions (id -> definition)")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate catalog version is valid semver."""
        return validate_semver(v)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        """Validate schema version is valid semver."""
        return validate_semver(v)

    @model_validator(mode="after")
    def validate_error_ids_match(self) -> "ErrorCatalog":
        """Validate that error IDs in dict keys match error definition IDs."""
        for key, error_def in self.errors.items():
            if key != error_def.id:
                raise ValueError(f"Error key '{key}' does not match error definition ID '{error_def.id}'")
        return self
