# 🎯 Remote Monitoring Error System - Project Plan

## 📋 Project Overview

**Goal**: Build a remote error monitoring system with:
- YAML-based error catalogs with railway pattern
- Multi-protocol file streaming (S3, SSH, SFTP, FTP, Local)
- Snakemake orchestration with caching
- JSON-LD reports with Textual TUI
- Jinja2 export templates

---

## 🏗️ Architecture: 4+1 Views

### 1. **Logical View** - Domain Model
Domain entities, business logic, error definitions
- ErrorDefinition, PatternMatcher, ErrorMatch, ErrorCatalog, ConditionSpec classes
- Unit tests for domain logic, validation, serialization

### 2. **Process View** - Orchestration
Snakemake workflows, file discovery, pattern matching
- Snakemake rules, checkpoints, fsspec integration, fingerprinting
- Integration tests for workflows, rule execution, caching

### 3. **Development View** - Pattern Matching
Core scanning logic, regex/callable handling, context extraction
- Pattern matching strategies, context extraction, streaming file readers
- Unit tests for pattern matching, context extraction edge cases

### 4. **Physical View** - Report Generation
JSON-LD output, Textual TUI, Jinja2 templates
- JSON-LD formatting, Textual app, template rendering
- Integration tests for report generation, TUI rendering

### +1. **Scenarios View** - Integration
End-to-end workflows, ensuring all pieces integrate
- E2E tests, interface contracts, component integration
- Full pipeline tests with sample error catalogs

---

## 🔄 Implementation Iterations

### ✅ Iteration 0: CI/CD Infrastructure
**Agent**: github-actions-cicd-expert

**Tasks**:
- [ ] GitHub Actions workflow with pixi
- [ ] MinIO service (S3 protocol)
- [ ] OpenSSH server (SSH/SFTP protocols)
- [ ] FTP server (FTP protocol)
- [ ] Test fixtures upload scripts (all protocols)
- [ ] pytest fixtures for remote URIs
- [ ] CI test markers and configuration
- [ ] Coverage reporting setup

**Tests First**:
- `test_minio_s3_connection()`
- `test_ssh_connection_and_exec()`
- `test_sftp_file_operations()`
- `test_ftp_file_operations()`
- `test_fsspec_s3_uri_resolution()`
- `test_fsspec_ssh_uri_resolution()`
- `test_fsspec_sftp_uri_resolution()`
- `test_fsspec_ftp_uri_resolution()`

**Deliverable**: CI pipeline with S3/SSH/SFTP/FTP/Local testing

---

### ✅ Iteration 1: Domain Model Foundation
**Agent**: general-purpose

**Tasks**:
- [ ] Project structure (src/, tests/, schemas/)
- [ ] Pydantic models: ErrorDefinition, PatternMatcher, ErrorMatch, ErrorCatalog
- [ ] ConditionSpec with AND/OR/CUSTOM logic
- [ ] JSON Schema for ErrorCatalog validation
- [ ] YAML/JSON-LD serialization
- [ ] Semver validation
- [ ] Unit tests (100% coverage on models)
- [ ] Test with remote URIs from CI

**Tests First**:
- `test_error_definition_validation()`
- `test_pattern_matcher_types()`
- `test_error_catalog_yaml_loading()`
- `test_semver_validation()`
- `test_condition_spec_and_or_logic()`
- `test_jsonld_serialization()`

**Deliverable**: Core domain models with validation

---

### ✅ Iteration 2: Pattern Matching Engine
**Agent**: general-purpose

**Tasks**:
- [ ] PatternMatcher factory (literal/regex/callable)
- [ ] Callable loader (module:function resolution)
- [ ] Streaming file reader with fsspec (all protocols)
- [ ] Context extraction (before/after lines)
- [ ] Smart seeking for large files
- [ ] Unit tests for all pattern types
- [ ] Integration tests with MinIO/SFTP/FTP streams

**Tests First**:
- `test_literal_pattern_matching()`
- `test_regex_pattern_with_flags()`
- `test_callable_pattern_loading()`
- `test_context_extraction_boundaries()`
- `test_streaming_large_files()`
- `test_streaming_s3_protocol()`
- `test_streaming_sftp_protocol()`
- `test_streaming_ftp_protocol()`

**Deliverable**: Pattern matching with multi-protocol streaming

---

### ✅ Iteration 3: Snakemake Orchestration
**Agent**: general-purpose

**Tasks**:
- [ ] Checkpoint: file fingerprinting (mtime/checksum)
- [ ] Checkpoint: fsspec file discovery
- [ ] Rule: match_pattern (atomic)
- [ ] Rule: extract_context (atomic)
- [ ] Rule: aggregate_results
- [ ] Iterative funneling (checkpoint chains)
- [ ] Integration tests with Snakemake DAG
- [ ] Test with all remote protocols in CI

**Tests First**:
- `test_file_fingerprinting()`
- `test_checkpoint_file_discovery()`
- `test_match_pattern_rule_execution()`
- `test_context_extraction_rule()`
- `test_iterative_funneling()`
- `test_remote_file_caching()`

**Deliverable**: Working Snakemake pipeline

---

### ✅ Iteration 4: Railway Pattern & Conditions
**Agent**: general-purpose

**Tasks**:
- [ ] ConditionSpec evaluator (AND/OR/CUSTOM/FIELD_*)
- [ ] ErrorMatch context access in conditions
- [ ] Callable condition loader
- [ ] Snakemake checkpoint for next_errors
- [ ] DAG generation for error chains
- [ ] Integration tests for railway pattern
- [ ] Test conditional error chaining

**Tests First**:
- `test_condition_always()`
- `test_condition_and_or_logic()`
- `test_field_access_in_conditions()`
- `test_custom_callable_conditions()`
- `test_railway_pattern_dag_generation()`
- `test_error_chain_execution()`

**Deliverable**: Full railway pattern with conditions

---

### ✅ Iteration 5: Report Generation
**Agent**: general-purpose

**Tasks**:
- [ ] JSON-LD aggregator from ErrorMatches
- [ ] Schema.org compliance
- [ ] Textual TUI app
- [ ] Tree navigation widget
- [ ] Context viewer panel
- [ ] Jinja2 template engine
- [ ] Markdown export template
- [ ] HTML export template (optional)
- [ ] Integration tests for reporting

**Tests First**:
- `test_jsonld_report_structure()`
- `test_schema_org_compliance()`
- `test_textual_tree_rendering()`
- `test_jinja2_markdown_export()`
- `test_hierarchical_grouping()`
- `test_tui_navigation()`

**Deliverable**: Interactive TUI with export

---

### ✅ Iteration 6: E2E Integration & CLI
**Agent**: integration-supervisor

**Tasks**:
- [ ] Sample error catalog (YAML)
- [ ] Test remote files (all protocols)
- [ ] E2E test: simple error detection
- [ ] E2E test: railway pattern chaining
- [ ] E2E test: remote streaming
- [ ] E2E test: report generation
- [ ] Click CLI with loguru integration
- [ ] CLI commands: scan, view, export
- [ ] Documentation and examples
- [ ] README with quickstart

**Tests First**:
- `test_e2e_simple_error_detection()`
- `test_e2e_railway_pattern_chaining()`
- `test_e2e_remote_file_streaming()`
- `test_e2e_report_generation()`
- `test_cli_interface()`
- `test_cli_scan_command()`
- `test_cli_view_command()`
- `test_cli_export_command()`

**Deliverable**: Production-ready CLI tool

---

## 📂 Project Structure

```
autosubmit-scan/
├── src/
│   ├── domain/              # Iteration 1
│   │   ├── models.py
│   │   ├── catalog.py
│   │   └── validation.py
│   ├── matching/            # Iteration 2
│   │   ├── pattern_matcher.py
│   │   ├── context_extractor.py
│   │   └── stream_reader.py
│   ├── orchestration/       # Iteration 3-4
│   │   ├── Snakefile
│   │   ├── rules/
│   │   └── conditions.py
│   └── reporting/           # Iteration 5
│       ├── jsonld.py
│       ├── tui.py
│       └── templates/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/
│   └── ci/
│       ├── setup_minio.py
│       ├── setup_sftp.py
│       └── setup_ftp.py
├── schemas/
│   └── error_catalog.schema.json
├── examples/
│   └── sample_catalog.yaml
├── .github/
│   └── workflows/
│       └── test.yml
├── pixi.toml
└── PROJECT_PLAN.md
```

---

## 🎯 Success Criteria

- [ ] All tests pass (unit + integration + E2E)
- [ ] Test coverage > 90%
- [ ] CI green with all protocols tested
- [ ] Sample catalog runs end-to-end
- [ ] TUI displays hierarchical errors
- [ ] Markdown/HTML export works
- [ ] Railway pattern chains correctly
- [ ] No file downloads (streaming only)
- [ ] Documentation complete

---

## 📦 Key Technologies

**Core Stack**:
- loguru (logging)
- click + click-loguru (CLI)
- questionary (interactive prompts)
- snakemake (workflow orchestration)
- returns (functional error handling)
- semver (version management)

**File & Remote Access**:
- fsspec (filesystem abstraction)
- paramiko (SSH/SFTP)
- boto3 + s3fs (S3/MinIO)
- sshfs (SFTP backend)

**Reporting & UI**:
- textual (TUI)
- jinja2 (templates)
- pydantic (data validation)
- check-jsonschema (schema validation)

**Testing & CI**:
- pytest + pytest-cov
- GitHub Actions
- MinIO (S3 mock)
- OpenSSH server (SSH/SFTP mock)
- FTP server (FTP mock)

---

## 🔄 Agent Coordination

**Supervisor Agent** (`integration-supervisor`) will:
- Review each iteration's output
- Ensure interface contracts between components
- Run integration tests after each iteration
- Flag issues before moving to next iteration

**Communication Pattern**:
1. Agent completes iteration → Tests pass
2. Supervisor reviews interfaces
3. Supervisor approves OR requests changes
4. Move to next iteration

---

## 📝 Design Decisions

### Domain Model
- **JSON-LD for reports**: Semantic web ready, Schema.org compatible
- **YAML for catalogs**: Human-readable error definitions
- **Semver versioning**: Both catalog content and schema version
- **Railway pattern**: Conditional error chaining via `next_errors`

### Orchestration
- **Streaming-first**: No file downloads, fsspec streaming only
- **Fingerprint caching**: mtime/checksum, manual clear option
- **Atomic Snakemake rules**: Composable, reusable building blocks
- **Checkpoint funneling**: Iterative filtering for efficiency

### Pattern Matching
- **Configurable types**: literal, regex, callable (Python functions)
- **Context extraction**: Configurable lines before/after match
- **Smart seeking**: Optimize for large files

### Reporting
- **Textual TUI**: Interactive tree navigation, context viewer
- **Jinja2 export**: User-customizable templates (Markdown/HTML)
- **Hierarchical structure**: By error type, host, file

---

## 🚀 Getting Started (Post-Implementation)

```bash
# Install dependencies
pixi install

# Run tests
pixi run pytest

# Scan for errors
pixi run scan --catalog examples/sample_catalog.yaml

# View results in TUI
pixi run view report.jsonld

# Export to markdown
pixi run export report.jsonld --template markdown --output report.md
```

---

**Status**: Ready to begin Iteration 0 - CI/CD Infrastructure Setup
