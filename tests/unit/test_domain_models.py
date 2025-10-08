"""Unit tests for domain models.

These tests define the expected behavior of the domain models
before implementation (TDD approach).
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestPatternType:
    """Test PatternType enum."""

    def test_pattern_type_values(self):
        """Test that PatternType has correct enum values."""
        from src.domain.models import PatternType

        assert PatternType.LITERAL.value == "literal"
        assert PatternType.REGEX.value == "regex"
        assert PatternType.CALLABLE.value == "callable"


class TestConditionType:
    """Test ConditionType enum."""

    def test_condition_type_values(self):
        """Test that ConditionType has all required values."""
        from src.domain.models import ConditionType

        assert ConditionType.ALWAYS.value == "always"
        assert ConditionType.AND.value == "and"
        assert ConditionType.OR.value == "or"
        assert ConditionType.CUSTOM.value == "custom"
        assert ConditionType.FIELD_EQUALS.value == "field_equals"
        assert ConditionType.FIELD_CONTAINS.value == "field_contains"
        assert ConditionType.FIELD_REGEX.value == "field_regex"


class TestPatternMatcher:
    """Test PatternMatcher model."""

    def test_literal_pattern_matcher(self):
        """Test creation of literal pattern matcher."""
        from src.domain.models import PatternMatcher, PatternType

        matcher = PatternMatcher(
            type=PatternType.LITERAL,
            pattern="OOM killed"
        )
        assert matcher.type == PatternType.LITERAL
        assert matcher.pattern == "OOM killed"
        assert matcher.flags is None

    def test_regex_pattern_matcher(self):
        """Test creation of regex pattern matcher with flags."""
        from src.domain.models import PatternMatcher, PatternType

        matcher = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"ERROR:\s+\w+",
            flags=["IGNORECASE", "MULTILINE"]
        )
        assert matcher.type == PatternType.REGEX
        assert matcher.pattern == r"ERROR:\s+\w+"
        assert matcher.flags == ["IGNORECASE", "MULTILINE"]

    def test_callable_pattern_matcher(self):
        """Test creation of callable pattern matcher."""
        from src.domain.models import PatternMatcher, PatternType

        matcher = PatternMatcher(
            type=PatternType.CALLABLE,
            pattern="mymodule:check_error"
        )
        assert matcher.type == PatternType.CALLABLE
        assert matcher.pattern == "mymodule:check_error"

    def test_callable_pattern_validation(self):
        """Test that callable pattern requires module:function format."""
        from src.domain.models import PatternMatcher, PatternType

        # Valid formats
        PatternMatcher(type=PatternType.CALLABLE, pattern="module:function")
        PatternMatcher(type=PatternType.CALLABLE, pattern="package.module:function")
        PatternMatcher(type=PatternType.CALLABLE, pattern="package.subpackage.module:function_name")

        # Invalid formats should raise ValidationError
        with pytest.raises(ValidationError):
            PatternMatcher(type=PatternType.CALLABLE, pattern="invalid")
        with pytest.raises(ValidationError):
            PatternMatcher(type=PatternType.CALLABLE, pattern="module:")
        with pytest.raises(ValidationError):
            PatternMatcher(type=PatternType.CALLABLE, pattern=":function")


class TestConditionSpec:
    """Test ConditionSpec model."""

    def test_always_condition(self):
        """Test ALWAYS condition."""
        from src.domain.models import ConditionSpec, ConditionType

        condition = ConditionSpec(type=ConditionType.ALWAYS)
        assert condition.type == ConditionType.ALWAYS

    def test_field_equals_condition(self):
        """Test FIELD_EQUALS condition."""
        from src.domain.models import ConditionSpec, ConditionType

        condition = ConditionSpec(
            type=ConditionType.FIELD_EQUALS,
            field="exit_code",
            operator="==",
            value=137
        )
        assert condition.type == ConditionType.FIELD_EQUALS
        assert condition.field == "exit_code"
        assert condition.operator == "=="
        assert condition.value == 137

    def test_field_contains_condition(self):
        """Test FIELD_CONTAINS condition."""
        from src.domain.models import ConditionSpec, ConditionType

        condition = ConditionSpec(
            type=ConditionType.FIELD_CONTAINS,
            field="matched_text",
            operator="contains",
            value="timeout"
        )
        assert condition.type == ConditionType.FIELD_CONTAINS
        assert condition.field == "matched_text"
        assert condition.value == "timeout"

    def test_field_regex_condition(self):
        """Test FIELD_REGEX condition."""
        from src.domain.models import ConditionSpec, ConditionType

        condition = ConditionSpec(
            type=ConditionType.FIELD_REGEX,
            field="matched_text",
            operator="regex",
            value=r"\d{3,4}"
        )
        assert condition.type == ConditionType.FIELD_REGEX
        assert condition.field == "matched_text"
        assert condition.value == r"\d{3,4}"

    def test_and_condition(self):
        """Test AND condition with nested conditions."""
        from src.domain.models import ConditionSpec, ConditionType

        condition = ConditionSpec(
            type=ConditionType.AND,
            conditions=[
                ConditionSpec(
                    type=ConditionType.FIELD_EQUALS,
                    field="exit_code",
                    operator="==",
                    value=1
                ),
                ConditionSpec(
                    type=ConditionType.FIELD_CONTAINS,
                    field="matched_text",
                    operator="contains",
                    value="error"
                )
            ]
        )
        assert condition.type == ConditionType.AND
        assert len(condition.conditions) == 2

    def test_or_condition(self):
        """Test OR condition with nested conditions."""
        from src.domain.models import ConditionSpec, ConditionType

        condition = ConditionSpec(
            type=ConditionType.OR,
            conditions=[
                ConditionSpec(type=ConditionType.ALWAYS),
                ConditionSpec(
                    type=ConditionType.FIELD_EQUALS,
                    field="retry_count",
                    operator=">",
                    value=3
                )
            ]
        )
        assert condition.type == ConditionType.OR
        assert len(condition.conditions) == 2

    def test_custom_condition(self):
        """Test CUSTOM condition with callable."""
        from src.domain.models import ConditionSpec, ConditionType

        condition = ConditionSpec(
            type=ConditionType.CUSTOM,
            callable="mymodule:should_trigger"
        )
        assert condition.type == ConditionType.CUSTOM
        assert condition.callable == "mymodule:should_trigger"

    def test_nested_and_or_logic(self):
        """Test deeply nested AND/OR logic."""
        from src.domain.models import ConditionSpec, ConditionType

        # (field1 == value1 AND field2 == value2) OR field3 == value3
        condition = ConditionSpec(
            type=ConditionType.OR,
            conditions=[
                ConditionSpec(
                    type=ConditionType.AND,
                    conditions=[
                        ConditionSpec(
                            type=ConditionType.FIELD_EQUALS,
                            field="field1",
                            operator="==",
                            value="value1"
                        ),
                        ConditionSpec(
                            type=ConditionType.FIELD_EQUALS,
                            field="field2",
                            operator="==",
                            value="value2"
                        )
                    ]
                ),
                ConditionSpec(
                    type=ConditionType.FIELD_EQUALS,
                    field="field3",
                    operator="==",
                    value="value3"
                )
            ]
        )
        assert condition.type == ConditionType.OR
        assert len(condition.conditions) == 2
        assert condition.conditions[0].type == ConditionType.AND


class TestErrorCondition:
    """Test ErrorCondition model."""

    def test_error_condition_creation(self):
        """Test creation of error condition."""
        from src.domain.models import ErrorCondition, ConditionSpec, ConditionType

        error_condition = ErrorCondition(
            error_id="next_error",
            when=ConditionSpec(type=ConditionType.ALWAYS)
        )
        assert error_condition.error_id == "next_error"
        assert error_condition.when.type == ConditionType.ALWAYS


class TestCatalogMetadata:
    """Test CatalogMetadata model."""

    def test_catalog_metadata_creation(self):
        """Test creation of catalog metadata."""
        from src.domain.models import CatalogMetadata

        now = datetime.now()
        metadata = CatalogMetadata(
            name="Test Catalog",
            description="A test error catalog",
            author="Test Author",
            created=now,
            updated=now
        )
        assert metadata.name == "Test Catalog"
        assert metadata.description == "A test error catalog"
        assert metadata.author == "Test Author"
        assert metadata.created == now
        assert metadata.updated == now


class TestErrorDefinition:
    """Test ErrorDefinition model."""

    def test_error_definition_minimal(self):
        """Test minimal error definition."""
        from src.domain.models import ErrorDefinition, PatternMatcher, PatternType

        error = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=["/var/log/*.log"],
            meaning="An error occurred",
            context_lines=3,
            suggestion="Check the logs"
        )
        assert error.id == "test_error"
        assert error.pattern.type == PatternType.LITERAL
        assert error.files == ["/var/log/*.log"]
        assert error.meaning == "An error occurred"
        assert error.context_lines == 3
        assert error.suggestion == "Check the logs"
        assert error.next_errors == []
        assert error.metadata is None

    def test_error_definition_with_next_errors(self):
        """Test error definition with railway pattern."""
        from src.domain.models import (
            ErrorDefinition,
            PatternMatcher,
            PatternType,
            ErrorCondition,
            ConditionSpec,
            ConditionType
        )

        error = ErrorDefinition(
            id="oom_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="OOM killed"),
            files=["s3://bucket/logs/*.log"],
            meaning="Out of memory error",
            context_lines=5,
            suggestion="Increase memory allocation",
            next_errors=[
                ErrorCondition(
                    error_id="allocation_error",
                    when=ConditionSpec(type=ConditionType.ALWAYS)
                )
            ]
        )
        assert len(error.next_errors) == 1
        assert error.next_errors[0].error_id == "allocation_error"

    def test_error_definition_with_metadata(self):
        """Test error definition with metadata."""
        from src.domain.models import ErrorDefinition, PatternMatcher, PatternType

        error = ErrorDefinition(
            id="critical_error",
            pattern=PatternMatcher(type=PatternType.REGEX, pattern=r"CRITICAL:\s+.*"),
            files=["ssh://user@host:22/var/log/**/*.log"],
            meaning="Critical system error",
            context_lines=10,
            suggestion="Immediate action required",
            metadata={
                "severity": "critical",
                "tags": ["system", "urgent"],
                "notify": ["ops@example.com"]
            }
        )
        assert error.metadata["severity"] == "critical"
        assert "system" in error.metadata["tags"]

    def test_error_definition_validation(self):
        """Test error definition validation."""
        from src.domain.models import ErrorDefinition, PatternMatcher, PatternType

        # Valid definition
        ErrorDefinition(
            id="valid_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["/path/to/file.log"],
            meaning="An error",
            context_lines=1,
            suggestion="Fix it"
        )

        # Invalid: negative context_lines
        with pytest.raises(ValidationError):
            ErrorDefinition(
                id="invalid_error",
                pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
                files=["/path/to/file.log"],
                meaning="An error",
                context_lines=-1,
                suggestion="Fix it"
            )

        # Invalid: empty files list
        with pytest.raises(ValidationError):
            ErrorDefinition(
                id="invalid_error",
                pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
                files=[],
                meaning="An error",
                context_lines=1,
                suggestion="Fix it"
            )


class TestErrorCatalog:
    """Test ErrorCatalog model."""

    def test_error_catalog_creation(self):
        """Test creation of error catalog."""
        from src.domain.models import (
            ErrorCatalog,
            CatalogMetadata,
            ErrorDefinition,
            PatternMatcher,
            PatternType
        )

        now = datetime.now()
        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata=CatalogMetadata(
                name="Test Catalog",
                description="Test",
                author="Author",
                created=now,
                updated=now
            ),
            errors={
                "error1": ErrorDefinition(
                    id="error1",
                    pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
                    files=["/var/log/*.log"],
                    meaning="Error",
                    context_lines=3,
                    suggestion="Fix"
                )
            }
        )
        assert catalog.version == "1.0.0"
        assert catalog.schema_version == "1.0.0"
        assert "error1" in catalog.errors

    def test_semver_validation(self):
        """Test semver validation for catalog versions."""
        from src.domain.models import ErrorCatalog, CatalogMetadata

        now = datetime.now()
        metadata = CatalogMetadata(
            name="Test", description="Test", author="Author",
            created=now, updated=now
        )

        # Valid semver
        ErrorCatalog(version="1.0.0", schema_version="1.0.0", metadata=metadata, errors={})
        ErrorCatalog(version="2.1.3", schema_version="1.0.0", metadata=metadata, errors={})
        ErrorCatalog(version="0.0.1", schema_version="1.2.3", metadata=metadata, errors={})
        ErrorCatalog(version="1.0.0-alpha", schema_version="1.0.0", metadata=metadata, errors={})
        ErrorCatalog(version="1.0.0+build.123", schema_version="1.0.0", metadata=metadata, errors={})

        # Invalid semver
        with pytest.raises(ValidationError):
            ErrorCatalog(version="1.0", schema_version="1.0.0", metadata=metadata, errors={})
        with pytest.raises(ValidationError):
            ErrorCatalog(version="1", schema_version="1.0.0", metadata=metadata, errors={})
        with pytest.raises(ValidationError):
            ErrorCatalog(version="invalid", schema_version="1.0.0", metadata=metadata, errors={})


class TestErrorMatch:
    """Test ErrorMatch model."""

    def test_error_match_creation(self):
        """Test creation of runtime error match."""
        from src.domain.models import ErrorMatch

        now = datetime.now()
        match = ErrorMatch(
            error_id="oom_error",
            file_uri="s3://bucket/logs/job123.log",
            line_number=456,
            matched_text="OOM killed process",
            context_before=["line 1", "line 2"],
            context_after=["line 3", "line 4"],
            timestamp=now,
            metadata={"job_id": "123", "severity": "high"}
        )
        assert match.error_id == "oom_error"
        assert match.file_uri == "s3://bucket/logs/job123.log"
        assert match.line_number == 456
        assert match.matched_text == "OOM killed process"
        assert len(match.context_before) == 2
        assert len(match.context_after) == 2
        assert match.timestamp == now
        assert match.metadata["job_id"] == "123"

    def test_error_match_validation(self):
        """Test error match validation."""
        from src.domain.models import ErrorMatch

        now = datetime.now()

        # Valid match
        ErrorMatch(
            error_id="error1",
            file_uri="/path/to/file.log",
            line_number=1,
            matched_text="error text",
            context_before=[],
            context_after=[],
            timestamp=now,
            metadata={}
        )

        # Invalid: negative line number
        with pytest.raises(ValidationError):
            ErrorMatch(
                error_id="error1",
                file_uri="/path/to/file.log",
                line_number=-1,
                matched_text="error text",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={}
            )

        # Invalid: line number = 0
        with pytest.raises(ValidationError):
            ErrorMatch(
                error_id="error1",
                file_uri="/path/to/file.log",
                line_number=0,
                matched_text="error text",
                context_before=[],
                context_after=[],
                timestamp=now,
                metadata={}
            )


class TestURIValidation:
    """Test URI validation for various fsspec protocols."""

    def test_s3_uri_validation(self):
        """Test S3 URI validation."""
        from src.domain.models import ErrorDefinition, PatternMatcher, PatternType

        # Valid S3 URIs
        ErrorDefinition(
            id="test",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["s3://bucket/path/file.log"],
            meaning="test",
            context_lines=1,
            suggestion="test"
        )
        ErrorDefinition(
            id="test",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["s3://bucket/path/*.log"],
            meaning="test",
            context_lines=1,
            suggestion="test"
        )
        ErrorDefinition(
            id="test",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["s3://bucket/path/**/*.log"],
            meaning="test",
            context_lines=1,
            suggestion="test"
        )

    def test_ssh_uri_validation(self):
        """Test SSH URI validation."""
        from src.domain.models import ErrorDefinition, PatternMatcher, PatternType

        # Valid SSH URIs
        ErrorDefinition(
            id="test",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["ssh://user@host/path/file.log"],
            meaning="test",
            context_lines=1,
            suggestion="test"
        )
        ErrorDefinition(
            id="test",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["ssh://user@host:22/path/*.log"],
            meaning="test",
            context_lines=1,
            suggestion="test"
        )
        ErrorDefinition(
            id="test",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["ssh://user@192.168.1.1:2222/path/**/*.log"],
            meaning="test",
            context_lines=1,
            suggestion="test"
        )

    def test_sftp_uri_validation(self):
        """Test SFTP URI validation."""
        from src.domain.models import ErrorDefinition, PatternMatcher, PatternType

        ErrorDefinition(
            id="test",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["sftp://user:pass@host/path/file.log"],
            meaning="test",
            context_lines=1,
            suggestion="test"
        )

    def test_ftp_uri_validation(self):
        """Test FTP URI validation."""
        from src.domain.models import ErrorDefinition, PatternMatcher, PatternType

        ErrorDefinition(
            id="test",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["ftp://user:pass@host/path/file.log"],
            meaning="test",
            context_lines=1,
            suggestion="test"
        )

    def test_local_path_validation(self):
        """Test local path validation."""
        from src.domain.models import ErrorDefinition, PatternMatcher, PatternType

        # Valid local paths
        ErrorDefinition(
            id="test",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["/absolute/path/file.log"],
            meaning="test",
            context_lines=1,
            suggestion="test"
        )
        ErrorDefinition(
            id="test",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["file:///absolute/path/file.log"],
            meaning="test",
            context_lines=1,
            suggestion="test"
        )
        ErrorDefinition(
            id="test",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="error"),
            files=["/var/log/**/*.log"],
            meaning="test",
            context_lines=1,
            suggestion="test"
        )


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_pattern_matcher_dict(self):
        """Test PatternMatcher serialization to dict."""
        from src.domain.models import PatternMatcher, PatternType

        matcher = PatternMatcher(
            type=PatternType.REGEX,
            pattern=r"\w+",
            flags=["IGNORECASE"]
        )
        data = matcher.model_dump()
        assert data["type"] == "regex"
        assert data["pattern"] == r"\w+"
        assert data["flags"] == ["IGNORECASE"]

    def test_error_definition_dict(self):
        """Test ErrorDefinition serialization to dict."""
        from src.domain.models import ErrorDefinition, PatternMatcher, PatternType

        error = ErrorDefinition(
            id="test_error",
            pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
            files=["/var/log/*.log"],
            meaning="An error",
            context_lines=3,
            suggestion="Fix it",
            metadata={"severity": "high"}
        )
        data = error.model_dump()
        assert data["id"] == "test_error"
        assert data["pattern"]["type"] == "literal"
        assert data["metadata"]["severity"] == "high"

    def test_error_catalog_dict(self):
        """Test ErrorCatalog serialization to dict."""
        from src.domain.models import (
            ErrorCatalog,
            CatalogMetadata,
            ErrorDefinition,
            PatternMatcher,
            PatternType
        )

        now = datetime.now()
        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata=CatalogMetadata(
                name="Test",
                description="Test",
                author="Author",
                created=now,
                updated=now
            ),
            errors={
                "error1": ErrorDefinition(
                    id="error1",
                    pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
                    files=["/var/log/*.log"],
                    meaning="Error",
                    context_lines=3,
                    suggestion="Fix"
                )
            }
        )
        data = catalog.model_dump()
        assert data["version"] == "1.0.0"
        assert "error1" in data["errors"]
