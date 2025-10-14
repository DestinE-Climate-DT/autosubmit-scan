"""Integration tests for catalog variable extraction and rendering."""

from datetime import datetime

import pytest
import yaml

from src.domain.catalog import load_catalog


class TestCatalogVariableExtraction:
    """Test loading catalogs with variable extraction."""

    def test_load_catalog_with_regex_variable(self, tmp_path):
        """Test loading catalog that extracts variable using regex."""
        # Create a config file with host information
        config_file = tmp_path / "platform_config.txt"
        config_file.write_text("PLATFORM_HOST=lumi\nPLATFORM_USER=testuser\n")

        # Create catalog with variable extraction
        catalog_file = tmp_path / "catalog.yaml"
        catalog_data = {
            "version": "1.0.0",
            "schema_version": "1.0.0",
            "metadata": {
                "name": "Test Catalog",
                "description": "Test",
                "author": "Test",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "variables": {
                    "host": {"source": "file", "path": str(config_file), "method": "regex", "pattern": r"PLATFORM_HOST=(\S+)"}
                },
            },
            "errors": {
                "test_error": {
                    "id": "test_error",
                    "pattern": {"type": "literal", "pattern": "ERROR"},
                    "files": ["ssh://user@{{ host }}/logs/*.log", "/local/{{ host }}/data/*.txt"],
                    "meaning": "Test error",
                    "suggestion": "Fix it",
                    "context_lines": 2,
                }
            },
        }

        with open(catalog_file, "w") as f:
            yaml.dump(catalog_data, f)

        # Load catalog
        catalog = load_catalog(str(catalog_file))

        # Verify variable was extracted and templates were rendered
        assert catalog.errors["test_error"].files == ["ssh://user@lumi/logs/*.log", "/local/lumi/data/*.txt"]

    def test_load_catalog_with_yaml_path_variable(self, tmp_path):
        """Test loading catalog that extracts variable from YAML."""
        # Create a YAML config file
        config_file = tmp_path / "platform_config.yaml"
        config_data = {"config": {"platforms": {"default": "mn5", "hpc": {"name": "lumi", "partition": "standard"}}}}
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Create catalog with YAML path extraction
        catalog_file = tmp_path / "catalog.yaml"
        catalog_data = {
            "version": "1.0.0",
            "schema_version": "1.0.0",
            "metadata": {
                "name": "Test Catalog",
                "description": "Test",
                "author": "Test",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "variables": {
                    "host": {
                        "source": "file",
                        "path": str(config_file),
                        "method": "yaml_path",
                        "pattern": "config.platforms.hpc.name",
                    }
                },
            },
            "errors": {
                "test_error": {
                    "id": "test_error",
                    "pattern": {"type": "literal", "pattern": "ERROR"},
                    "files": ["sftp://user@{{ host }}/scratch/logs/**/*.log"],
                    "meaning": "Test error",
                    "suggestion": "Fix it",
                    "context_lines": 2,
                }
            },
        }

        with open(catalog_file, "w") as f:
            yaml.dump(catalog_data, f)

        # Load catalog
        catalog = load_catalog(str(catalog_file))

        # Verify variable was extracted and template was rendered
        assert catalog.errors["test_error"].files == ["sftp://user@lumi/scratch/logs/**/*.log"]

    def test_load_catalog_with_line_extraction(self, tmp_path):
        """Test loading catalog that extracts variable from specific line."""
        # Create a simple text file with hostname on second line
        config_file = tmp_path / "hostname.txt"
        config_file.write_text("# Hostname file\nlumi\n# End\n")

        # Create catalog with line extraction
        catalog_file = tmp_path / "catalog.yaml"
        catalog_data = {
            "version": "1.0.0",
            "schema_version": "1.0.0",
            "metadata": {
                "name": "Test Catalog",
                "description": "Test",
                "author": "Test",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "variables": {"host": {"source": "file", "path": str(config_file), "method": "line", "line_number": 2}},
            },
            "errors": {
                "test_error": {
                    "id": "test_error",
                    "pattern": {"type": "literal", "pattern": "ERROR"},
                    "files": ["ftp://{{ host }}/logs/*.log"],
                    "meaning": "Test error",
                    "suggestion": "Fix it",
                    "context_lines": 2,
                }
            },
        }

        with open(catalog_file, "w") as f:
            yaml.dump(catalog_data, f)

        # Load catalog
        catalog = load_catalog(str(catalog_file))

        # Verify variable was extracted and template was rendered
        assert catalog.errors["test_error"].files == ["ftp://lumi/logs/*.log"]

    def test_load_catalog_with_multiple_variables(self, tmp_path):
        """Test loading catalog with multiple variable extractions."""
        # Create config files
        host_file = tmp_path / "host.txt"
        host_file.write_text("lumi\n")

        user_file = tmp_path / "user.txt"
        user_file.write_text("testuser\n")

        base_path_file = tmp_path / "paths.yaml"
        with open(base_path_file, "w") as f:
            yaml.dump({"paths": {"scratch": "/scratch/project"}}, f)

        # Create catalog with multiple variables
        catalog_file = tmp_path / "catalog.yaml"
        catalog_data = {
            "version": "1.0.0",
            "schema_version": "1.0.0",
            "metadata": {
                "name": "Test Catalog",
                "description": "Test",
                "author": "Test",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "variables": {
                    "host": {"source": "file", "path": str(host_file), "method": "line", "line_number": 1},
                    "user": {"source": "file", "path": str(user_file), "method": "line", "line_number": 1},
                    "base_path": {
                        "source": "file",
                        "path": str(base_path_file),
                        "method": "yaml_path",
                        "pattern": "paths.scratch",
                    },
                },
            },
            "errors": {
                "test_error": {
                    "id": "test_error",
                    "pattern": {"type": "literal", "pattern": "ERROR"},
                    "files": ["ssh://{{ user }}@{{ host }}{{ base_path }}/logs/*.log"],
                    "meaning": "Test error",
                    "suggestion": "Fix it",
                    "context_lines": 2,
                }
            },
        }

        with open(catalog_file, "w") as f:
            yaml.dump(catalog_data, f)

        # Load catalog
        catalog = load_catalog(str(catalog_file))

        # Verify all variables were extracted and template was rendered
        assert catalog.errors["test_error"].files == ["ssh://testuser@lumi/scratch/project/logs/*.log"]

    def test_load_catalog_with_missing_file_uses_default(self, tmp_path):
        """Test that default value is used when extraction file is missing."""
        # Don't create the config file - it's missing

        # Create catalog with default value
        catalog_file = tmp_path / "catalog.yaml"
        catalog_data = {
            "version": "1.0.0",
            "schema_version": "1.0.0",
            "metadata": {
                "name": "Test Catalog",
                "description": "Test",
                "author": "Test",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "variables": {
                    "host": {
                        "source": "file",
                        "path": str(tmp_path / "nonexistent.txt"),
                        "method": "regex",
                        "pattern": r"host=(\S+)",
                        "default": "localhost",
                    }
                },
            },
            "errors": {
                "test_error": {
                    "id": "test_error",
                    "pattern": {"type": "literal", "pattern": "ERROR"},
                    "files": ["ssh://user@{{ host }}/logs/*.log"],
                    "meaning": "Test error",
                    "suggestion": "Fix it",
                    "context_lines": 2,
                }
            },
        }

        with open(catalog_file, "w") as f:
            yaml.dump(catalog_data, f)

        # Load catalog
        catalog = load_catalog(str(catalog_file))

        # Verify default value was used
        assert catalog.errors["test_error"].files == ["ssh://user@localhost/logs/*.log"]

    def test_load_catalog_without_variables_unchanged(self, tmp_path):
        """Test that catalogs without variables work as before."""
        # Create catalog without variables
        catalog_file = tmp_path / "catalog.yaml"
        catalog_data = {
            "version": "1.0.0",
            "schema_version": "1.0.0",
            "metadata": {
                "name": "Test Catalog",
                "description": "Test",
                "author": "Test",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
            },
            "errors": {
                "test_error": {
                    "id": "test_error",
                    "pattern": {"type": "literal", "pattern": "ERROR"},
                    "files": ["/logs/*.log"],
                    "meaning": "Test error",
                    "suggestion": "Fix it",
                    "context_lines": 2,
                }
            },
        }

        with open(catalog_file, "w") as f:
            yaml.dump(catalog_data, f)

        # Load catalog
        catalog = load_catalog(str(catalog_file))

        # Verify files are unchanged (no template rendering)
        assert catalog.errors["test_error"].files == ["/logs/*.log"]
