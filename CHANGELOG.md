# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-13

### Added
- Complete CLI interface with commands: `scan`, `view`, `export`, `validate`, `init`, `add`, `dag`
- Expid shortcut: run `as-scan a23i` directly without specifying `scan` command
- Pattern matching system supporting literal, regex, and callable patterns
- Railway pattern for conditional error chaining and follow-up error detection
- Snakemake workflow orchestration with checkpoint-based execution
- Multi-protocol file support via fsspec (local, S3, SFTP, FTP, SSH)
- Context extraction around matched errors with configurable line counts
- JSON-LD report generation with Schema.org compliance
- Interactive TUI for viewing scan results (Textual-based)
- Template rendering system (Markdown, HTML, plain text)
- Error catalog validation with Pydantic v2 models
- File fingerprinting and caching to avoid re-scanning unchanged files
- CI/CD setup scripts for MinIO, SFTP, and FTP testing
- Comprehensive test suite (286 tests: unit, integration, e2e)
- Test fixtures for SLURM errors (OOM, timeout) and application errors
- Tab completion support for CLI

### Fixed
- Linting errors: unused loop variables in CI scripts (B007)
- Import ordering in CLI main (E402 with noqa comments for valid Click pattern)
- Deprecation warning: replaced `datetime.utcnow()` with `datetime.now(UTC)`
- Timezone-aware datetime handling in tests
- Empty files list validation errors in test catalogs
- Railway pattern attribute access (changed from dict to object attributes)
- File fingerprinting critical bug
- Git worktree configuration for cross-machine compatibility

### Changed
- Updated all tests to pass strict Pydantic validation
- Formatted entire codebase with ruff (30 files reformatted)
- Improved test readability by splitting complex assertions
- Strengthened validation: ErrorDefinition now requires non-empty files list

### Technical Details
- Python >= 3.12 required
- Pydantic v2 for all data models
- Click framework for CLI
- Snakemake for workflow orchestration
- Textual for TUI
- fsspec for multi-protocol file access
- Jinja2 for template rendering
- loguru for structured logging

### Testing
- 286 passing tests (0 failures, 0 errors)
- 40 remote integration tests (skipped without `--remote` flag)
- Test coverage across unit, integration, and e2e levels
- CI setup scripts for testing with MinIO, SFTP, and FTP services

### Documentation
- Comprehensive CLAUDE.md for development guidance
- Sample catalog examples
- CLI help documentation
- Architecture documentation in codebase

## [Unreleased]

### Planned
- Additional custom matcher examples
- More template options
- Performance optimizations for large file sets
- Enhanced error reporting and statistics

[0.1.0]: https://github.com/DestinE-Climate-DT/autosubmit-scan/releases/tag/v0.1.0
