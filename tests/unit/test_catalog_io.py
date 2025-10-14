"""Unit tests for catalog I/O operations.

These tests define the expected behavior of catalog loading/saving
before implementation (TDD approach).
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml


class TestYAMLCatalogIO:
    """Test YAML catalog loading and saving."""

    def test_load_yaml_catalog(self, tmp_path):
        """Test loading a valid YAML catalog."""
        from src.domain.catalog import load_catalog

        # Create a simple YAML catalog
        catalog_yaml = """
version: "1.0.0"
schema_version: "1.0.0"
metadata:
  name: "Test Catalog"
  description: "A test catalog"
  author: "Test Author"
  created: "2024-01-01T00:00:00"
  updated: "2024-01-01T00:00:00"
errors:
  oom_error:
    id: "oom_error"
    pattern:
      type: "literal"
      pattern: "OOM killed"
    files:
      - "/var/log/*.log"
    meaning: "Out of memory error"
    context_lines: 5
    suggestion: "Increase memory allocation"
    next_errors: []
"""
        catalog_file = tmp_path / "catalog.yaml"
        catalog_file.write_text(catalog_yaml)

        catalog = load_catalog(str(catalog_file))
        assert catalog.version == "1.0.0"
        assert catalog.schema_version == "1.0.0"
        assert catalog.metadata.name == "Test Catalog"
        assert "oom_error" in catalog.errors
        assert catalog.errors["oom_error"].meaning == "Out of memory error"

    def test_save_yaml_catalog(self, tmp_path):
        """Test saving a catalog to YAML."""
        from src.domain.catalog import save_catalog
        from src.domain.models import CatalogMetadata, ErrorCatalog, ErrorDefinition, PatternMatcher, PatternType

        now = datetime(2024, 1, 1, 0, 0, 0)
        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata=CatalogMetadata(name="Test Catalog", description="Test", author="Author", created=now, updated=now),
            errors={
                "error1": ErrorDefinition(
                    id="error1",
                    pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
                    files=["/var/log/*.log"],
                    meaning="An error",
                    context_lines=3,
                    suggestion="Fix it",
                )
            },
        )

        catalog_file = tmp_path / "output.yaml"
        save_catalog(catalog, str(catalog_file))

        assert catalog_file.exists()
        content = catalog_file.read_text()
        assert "version: 1.0.0" in content
        assert "error1" in content

    def test_yaml_round_trip(self, tmp_path):
        """Test that save/load round-trip preserves data."""
        from src.domain.catalog import load_catalog, save_catalog
        from src.domain.models import (
            CatalogMetadata,
            ConditionSpec,
            ConditionType,
            ErrorCatalog,
            ErrorCondition,
            ErrorDefinition,
            PatternMatcher,
            PatternType,
        )

        now = datetime(2024, 1, 1, 12, 0, 0)
        original = ErrorCatalog(
            version="2.1.3",
            schema_version="1.0.0",
            metadata=CatalogMetadata(
                name="Round Trip Test", description="Testing round-trip", author="Test Author", created=now, updated=now
            ),
            errors={
                "error1": ErrorDefinition(
                    id="error1",
                    pattern=PatternMatcher(type=PatternType.REGEX, pattern=r"ERROR:\s+\w+", flags=["IGNORECASE"]),
                    files=["s3://bucket/logs/*.log"],
                    meaning="An error occurred",
                    context_lines=5,
                    suggestion="Check logs",
                    next_errors=[ErrorCondition(error_id="error2", when=ConditionSpec(type=ConditionType.ALWAYS))],
                    metadata={"severity": "high"},
                )
            },
        )

        catalog_file = tmp_path / "roundtrip.yaml"
        save_catalog(original, str(catalog_file))
        loaded = load_catalog(str(catalog_file))

        assert loaded.version == original.version
        assert loaded.schema_version == original.schema_version
        assert loaded.metadata.name == original.metadata.name
        assert loaded.metadata.author == original.metadata.author
        assert "error1" in loaded.errors
        assert loaded.errors["error1"].pattern.type == PatternType.REGEX
        assert loaded.errors["error1"].pattern.flags == ["IGNORECASE"]
        assert loaded.errors["error1"].files == ["s3://bucket/logs/*.log"]
        assert len(loaded.errors["error1"].next_errors) == 1

    def test_invalid_yaml_raises_error(self, tmp_path):
        """Test that invalid YAML raises an error."""
        from src.domain.catalog import load_catalog

        # Invalid YAML syntax
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):  # Should raise YAML parsing error
            load_catalog(str(invalid_file))

    def test_invalid_catalog_structure_raises_error(self, tmp_path):
        """Test that YAML with invalid catalog structure raises validation error."""
        from pydantic import ValidationError

        from src.domain.catalog import load_catalog

        # Valid YAML but invalid catalog structure
        invalid_catalog = """
version: "invalid_version"
schema_version: "1.0.0"
metadata:
  name: "Test"
errors: {}
"""
        catalog_file = tmp_path / "invalid_catalog.yaml"
        catalog_file.write_text(invalid_catalog)

        with pytest.raises(ValidationError):
            load_catalog(str(catalog_file))

    def test_load_nonexistent_file(self):
        """Test that loading nonexistent file raises error."""
        from src.domain.catalog import load_catalog

        with pytest.raises(FileNotFoundError):
            load_catalog("/nonexistent/path/catalog.yaml")

    def test_load_catalog_with_complex_conditions(self, tmp_path):
        """Test loading catalog with complex nested conditions."""
        from src.domain.catalog import load_catalog

        catalog_yaml = """
version: "1.0.0"
schema_version: "1.0.0"
metadata:
  name: "Complex Catalog"
  description: "Catalog with complex conditions"
  author: "Test"
  created: "2024-01-01T00:00:00"
  updated: "2024-01-01T00:00:00"
errors:
  error1:
    id: "error1"
    pattern:
      type: "literal"
      pattern: "ERROR"
    files:
      - "/var/log/*.log"
    meaning: "Error"
    context_lines: 3
    suggestion: "Fix"
    next_errors:
      - error_id: "error2"
        when:
          type: "and"
          conditions:
            - type: "field_equals"
              field: "exit_code"
              operator: "=="
              value: 1
            - type: "field_contains"
              field: "matched_text"
              operator: "contains"
              value: "timeout"
"""
        catalog_file = tmp_path / "complex.yaml"
        catalog_file.write_text(catalog_yaml)

        catalog = load_catalog(str(catalog_file))
        assert "error1" in catalog.errors
        assert len(catalog.errors["error1"].next_errors) == 1
        assert catalog.errors["error1"].next_errors[0].when.type.value == "and"
        assert len(catalog.errors["error1"].next_errors[0].when.conditions) == 2


class TestJSONLDSerialization:
    """Test JSON-LD serialization."""

    def test_catalog_to_jsonld(self):
        """Test converting catalog to JSON-LD format."""
        from src.domain.catalog import catalog_to_jsonld
        from src.domain.models import CatalogMetadata, ErrorCatalog, ErrorDefinition, PatternMatcher, PatternType

        now = datetime(2024, 1, 1, 0, 0, 0)
        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata=CatalogMetadata(name="Test Catalog", description="Test", author="Author", created=now, updated=now),
            errors={
                "error1": ErrorDefinition(
                    id="error1",
                    pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
                    files=["/var/log/*.log"],
                    meaning="An error",
                    context_lines=3,
                    suggestion="Fix it",
                )
            },
        )

        jsonld = catalog_to_jsonld(catalog)

        # Check JSON-LD structure
        assert "@context" in jsonld
        assert "@type" in jsonld
        assert "@id" in jsonld
        assert jsonld["@type"] == "ErrorCatalog"
        assert "@vocab" in jsonld["@context"]
        assert "https://schema.org/" in jsonld["@context"]["@vocab"]
        assert "version" in jsonld
        assert jsonld["version"] == "1.0.0"

    def test_jsonld_to_catalog(self):
        """Test converting JSON-LD back to catalog."""
        from src.domain.catalog import jsonld_to_catalog
        from src.domain.models import PatternType

        jsonld_data = {
            "@context": {"@vocab": "https://schema.org/", "error_scan": "https://destine.example/error-scan/schema#"},
            "@type": "ErrorCatalog",
            "@id": "urn:uuid:12345",
            "version": "1.0.0",
            "schema_version": "1.0.0",
            "metadata": {
                "name": "Test Catalog",
                "description": "Test",
                "author": "Author",
                "created": "2024-01-01T00:00:00",
                "updated": "2024-01-01T00:00:00",
            },
            "errors": {
                "error1": {
                    "id": "error1",
                    "pattern": {"type": "literal", "pattern": "ERROR"},
                    "files": ["/var/log/*.log"],
                    "meaning": "An error",
                    "context_lines": 3,
                    "suggestion": "Fix it",
                    "next_errors": [],
                }
            },
        }

        catalog = jsonld_to_catalog(jsonld_data)
        assert catalog.version == "1.0.0"
        assert catalog.metadata.name == "Test Catalog"
        assert "error1" in catalog.errors
        assert catalog.errors["error1"].pattern.type == PatternType.LITERAL

    def test_jsonld_round_trip(self):
        """Test JSON-LD round-trip conversion."""
        from src.domain.catalog import catalog_to_jsonld, jsonld_to_catalog
        from src.domain.models import CatalogMetadata, ErrorCatalog, ErrorDefinition, PatternMatcher, PatternType

        now = datetime(2024, 1, 1, 0, 0, 0)
        original = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata=CatalogMetadata(name="Round Trip", description="Test", author="Author", created=now, updated=now),
            errors={
                "error1": ErrorDefinition(
                    id="error1",
                    pattern=PatternMatcher(type=PatternType.REGEX, pattern=r"\w+"),
                    files=["s3://bucket/*.log"],
                    meaning="Error",
                    context_lines=5,
                    suggestion="Fix",
                )
            },
        )

        jsonld = catalog_to_jsonld(original)
        loaded = jsonld_to_catalog(jsonld)

        assert loaded.version == original.version
        assert loaded.metadata.name == original.metadata.name
        assert "error1" in loaded.errors


class TestSchemaValidation:
    """Test JSON Schema validation."""

    def test_validate_catalog_against_schema(self, tmp_path):
        """Test that a valid catalog passes JSON Schema validation."""
        import json
        import subprocess

        from src.domain.catalog import save_catalog
        from src.domain.models import CatalogMetadata, ErrorCatalog, ErrorDefinition, PatternMatcher, PatternType

        now = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata=CatalogMetadata(name="Schema Test", description="Test", author="Author", created=now, updated=now),
            errors={
                "error1": ErrorDefinition(
                    id="error1",
                    pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
                    files=["/var/log/*.log"],
                    meaning="An error",
                    context_lines=3,
                    suggestion="Fix it",
                )
            },
        )

        # Save as YAML
        yaml_file = tmp_path / "catalog.yaml"
        save_catalog(catalog, str(yaml_file))

        # Convert to JSON for schema validation
        json_file = tmp_path / "catalog.json"
        catalog_dict = catalog.model_dump(mode="json", exclude_none=True)

        # Convert datetime objects to ISO format strings with timezone
        if isinstance(catalog_dict["metadata"]["created"], datetime):
            catalog_dict["metadata"]["created"] = catalog_dict["metadata"]["created"].isoformat()
        if isinstance(catalog_dict["metadata"]["updated"], datetime):
            catalog_dict["metadata"]["updated"] = catalog_dict["metadata"]["updated"].isoformat()

        json_file.write_text(json.dumps(catalog_dict, indent=2, default=str))

        # Validate against schema
        schema_path = Path(__file__).parent.parent.parent / "schemas" / "error_catalog.schema.json"

        # Only run if schema exists (will be created later)
        if schema_path.exists():
            result = subprocess.run(
                ["check-jsonschema", "--schemafile", str(schema_path), str(json_file)], capture_output=True, text=True
            )
            assert result.returncode == 0, f"Schema validation failed: {result.stderr}"

    def test_invalid_catalog_fails_schema_validation(self, tmp_path):
        """Test that an invalid catalog fails JSON Schema validation."""
        import json
        import subprocess

        # Create an invalid catalog JSON
        invalid_catalog = {
            "version": "invalid",  # Invalid semver
            "schema_version": "1.0.0",
            "metadata": {
                "name": "Test"
                # Missing required fields
            },
            "errors": {},
        }

        json_file = tmp_path / "invalid.json"
        json_file.write_text(json.dumps(invalid_catalog, indent=2))

        schema_path = Path(__file__).parent.parent.parent / "schemas" / "error_catalog.schema.json"

        # Only run if schema exists (will be created later)
        if schema_path.exists():
            result = subprocess.run(
                ["check-jsonschema", "--schemafile", str(schema_path), str(json_file)], capture_output=True, text=True
            )
            assert result.returncode != 0, "Invalid catalog should fail validation"


class TestCatalogHelpers:
    """Test catalog helper functions."""

    def test_catalog_get_error_by_id(self):
        """Test retrieving error by ID from catalog."""
        from src.domain.models import CatalogMetadata, ErrorCatalog, ErrorDefinition, PatternMatcher, PatternType

        now = datetime.now()
        catalog = ErrorCatalog(
            version="1.0.0",
            schema_version="1.0.0",
            metadata=CatalogMetadata(name="Test", description="Test", author="Author", created=now, updated=now),
            errors={
                "error1": ErrorDefinition(
                    id="error1",
                    pattern=PatternMatcher(type=PatternType.LITERAL, pattern="ERROR"),
                    files=["/var/log/*.log"],
                    meaning="An error",
                    context_lines=3,
                    suggestion="Fix it",
                ),
                "error2": ErrorDefinition(
                    id="error2",
                    pattern=PatternMatcher(type=PatternType.LITERAL, pattern="WARN"),
                    files=["/var/log/*.log"],
                    meaning="A warning",
                    context_lines=2,
                    suggestion="Check it",
                ),
            },
        )

        # Access errors by ID
        assert catalog.errors["error1"].meaning == "An error"
        assert catalog.errors["error2"].meaning == "A warning"
        assert "error3" not in catalog.errors
