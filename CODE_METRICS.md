# Code Metrics and Technical Debt Assessment

This document provides quantitative analysis of the codebase to support the architectural review.

---

## Duplication Metrics

### GitHub URI Parsing

**Duplication**: 2 implementations across 2 files

| File | Lines | Function | Logic Similarity |
|------|-------|----------|------------------|
| `src/domain/catalog.py` | 65-108 (44 lines) | Inline in `load_catalog()` | 95% identical |
| `src/domain/templates.py` | 49-101 (53 lines) | Inline in `load_template()` | 95% identical |

**Total duplicated code**: ~97 lines
**Maintenance burden**: Every bug fix requires 2 changes
**Risk level**: CRITICAL

**Example difference**:
```python
# catalog.py uses:
path_markers = ["templates/", "examples/", "src/", "config/", "catalogs/"]

# templates.py uses:
path_markers = ["templates/", "examples/", "src/", "docs/"]
```

Different path marker lists could cause inconsistent behavior!

### SSH Config Parsing

**Duplication**: 2 implementations IN THE SAME FILE

| Location | Lines | Function | Logic Similarity |
|----------|-------|----------|------------------|
| `src/cli/completion.py` | 65-124 (60 lines) | `_parse_ssh_config_standalone()` | 100% identical |
| `src/cli/completion.py` | 328-387 (60 lines) | `FsspecPathCompleter._parse_ssh_config()` | 100% identical |

**Total duplicated code**: 120 lines IN ONE FILE
**Maintenance burden**: Catastrophic - same bugs in both implementations
**Risk level**: CRITICAL

This is a textbook violation of DRY principle.

### URI Detection

**Duplication**: 4 implementations across 4 files

| File | Lines | Function | Logic Similarity |
|------|-------|----------|------------------|
| `src/domain/catalog.py` | 24-35 | `is_fsspec_uri()` | 100% identical |
| `src/domain/templates.py` | 15-24 | `is_fsspec_uri()` | 100% identical |
| `src/domain/variable_extractor.py` | 35-44 | `_is_fsspec_uri()` | 100% identical |
| `src/cli/completion.py` | Various | Inline checks | 90% similar |

**Total duplicated code**: ~40 lines
**Risk level**: MODERATE

### Summary Statistics

| Metric | Value |
|--------|-------|
| Total duplicate lines | ~257 lines |
| Duplicate percentage | ~4.2% of src/ |
| Files affected | 4 |
| Critical duplications | 2 |
| Moderate duplications | 1 |

---

## Module Size Analysis

### Large Modules (>300 lines)

| File | Lines | Responsibilities | Assessment |
|------|-------|------------------|------------|
| `completion.py` | 650 | SSH, filesystem, URI, caching, completers | Split into 4 modules |
| `dag.py` | 398 | DAG visualization | Acceptable (single purpose) |
| `models.py` | 334 | Domain models | Acceptable (Pydantic models) |
| `helpers.py` | 327 | Orchestration helpers | Review for splitting |
| `catalog.py` | 318 | Catalog I/O + parsing | Split I/O from domain |

### Recommended Splits

**completion.py (650 lines) → 4 modules**:
- `infrastructure/ssh_config.py` (120 lines)
- `infrastructure/uri_utils.py` (80 lines)
- `infrastructure/filesystem.py` (200 lines)
- `cli/completers.py` (250 lines)

**catalog.py (318 lines) → 2 modules**:
- `domain/catalog.py` (50 lines) - pure domain logic
- `infrastructure/catalog_repository.py` (268 lines) - I/O operations

---

## Dependency Analysis

### Direct Dependencies

```
Core:
  - pydantic >= 2.0
  - pyyaml >= 6.0
  - jinja2 >= 3.1
  - loguru >= 0.7
  - click >= 8.0
  - snakemake >= 9.12

Remote Access:
  - fsspec >= 2024.9
  - s3fs >= 2024.9
  - sshfs >= 2024.9
  - paramiko >= 4.0    # UNUSED?
  - boto3 >= 1.35

Testing:
  - pytest >= 8.0
  - pytest-cov >= 6.0
```

### Dependency Issues

1. **paramiko not used?**
   ```bash
   $ grep -r "import paramiko" src/
   # No results
   ```
   Recommendation: Remove if truly unused

2. **Two SSH implementations**
   - `paramiko` (if used)
   - `asyncssh` (via sshfs)

   Recommendation: Use only asyncssh via sshfs

---

## Configuration Analysis

### Environment Variables

Current environment variables used throughout codebase:

| Variable | Used In | Purpose | Centralized? |
|----------|---------|---------|--------------|
| `AUTOSUBMIT_SCAN_DEFAULT_TEMPLATE` | default.py | Template URI | No |
| `AUTOSUBMIT_HOST` | default.py | SSH host | No |
| `AUTOSUBMIT_BASE_PATH` | default.py | Base path | No |
| `GITHUB_TOKEN` | catalog.py, templates.py | Auth | No |
| `GITHUB_USERNAME` | catalog.py, templates.py | Auth | No |
| `GH_TOKEN` | catalog.py, templates.py | Auth alt | No |
| `GH_USERNAME` | catalog.py, templates.py | Auth alt | No |
| `USER` | Multiple | Default user | System |

**Total**: 7 custom environment variables
**Centralized**: 0 (0%)
**Risk**: HIGH - scattered configuration

### After Refactoring

All configuration in `src/config.py`:
- Single source of truth
- Type-safe access
- Testable
- Documented

---

## Cyclomatic Complexity

### Complex Functions (>10)

```python
# src/orchestration/conditions.py::get_field_value()
Complexity: 15
Reason: Nested conditionals for field path parsing
Recommendation: Acceptable (domain complexity)

# src/cli/completion.py::_complete_path()
Complexity: 18
Reason: Multiple protocol handling
Recommendation: Split by protocol type

# src/cli/completion.py::_complete_from_fsspec()
Complexity: 12
Reason: Caching + error handling
Recommendation: Extract caching logic
```

Most functions are reasonably simple (<10 complexity).

---

## Test Coverage

### Current Coverage (Estimated)

| Layer | Files | Test Files | Coverage Estimate |
|-------|-------|------------|-------------------|
| Domain | 6 | 5 | ~85% |
| Matching | 5 | 4 | ~80% |
| Orchestration | 4 | 3 | ~70% |
| CLI | 9 | 2 | ~30% |
| Reporting | 4 | 3 | ~75% |

**Overall estimated coverage**: ~65%

### Coverage Gaps

1. **CLI commands**: Low coverage (30%)
   - completion.py barely tested
   - default.py not fully tested

2. **Error paths**: Under-tested
   - GitHub rate limiting
   - SSH connection failures
   - Network timeouts

3. **Duplicated code**: No tests for consistency
   - GitHub parsing has 2 impls, which is tested?
   - SSH config parsing has 2 impls, neither tested

---

## Type Hint Coverage

### Analysis

```bash
$ mypy src/ --strict
# Would reveal gaps
```

**Estimated coverage**: ~85%

**Gaps**:
- Some callback functions lack hints
- Helper functions in completion.py
- Some exception handlers

---

## Code Smells Summary

### Critical Smells (Must Fix)

1. **Duplicated Code** (4 instances)
   - Severity: CRITICAL
   - Effort: 2 days
   - Impact: High maintainability improvement

2. **Scattered Configuration** (7 env vars)
   - Severity: HIGH
   - Effort: 0.5 days
   - Impact: Medium maintainability improvement

3. **Domain Layer Impurity** (I/O in domain)
   - Severity: HIGH
   - Effort: 1 day
   - Impact: High architectural improvement

### Moderate Smells (Should Fix)

1. **Large Modules** (completion.py: 650 lines)
   - Severity: MODERATE
   - Effort: 1 day
   - Impact: Medium readability improvement

2. **Generic Exceptions** (no custom hierarchy)
   - Severity: MODERATE
   - Effort: 0.5 days
   - Impact: Medium error handling improvement

### Minor Smells (Nice to Have)

1. **Missing Type Hints** (~15% of code)
   - Severity: LOW
   - Effort: 0.5 days
   - Impact: Low type safety improvement

2. **Test Coverage Gaps** (CLI at 30%)
   - Severity: LOW
   - Effort: 1 day
   - Impact: Medium test reliability improvement

---

## Refactoring Impact Analysis

### Lines of Code Changes

| Change Type | Lines Added | Lines Removed | Net Change |
|-------------|-------------|---------------|------------|
| New infrastructure modules | +800 | 0 | +800 |
| Remove duplicate code | 0 | -257 | -257 |
| Update imports | +50 | -50 | 0 |
| New tests | +400 | 0 | +400 |
| **Total** | **+1250** | **-307** | **+943** |

### Module Changes

| Module | Current Lines | After Refactoring | Change |
|--------|---------------|-------------------|--------|
| `completion.py` | 650 | ~250 | -400 |
| `catalog.py` | 318 | ~100 | -218 |
| `templates.py` | 162 | ~80 | -82 |
| `variable_extractor.py` | 271 | ~260 | -11 |
| **New modules** | 0 | ~800 | +800 |

**Net result**: More files, better organization, less duplication

---

## Risk Assessment

### Refactoring Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing code | Medium | High | Comprehensive tests, gradual rollout |
| Import cycles | Low | Medium | Proper layer separation |
| Performance regression | Low | Low | Benchmarking before/after |
| Incomplete migration | Medium | High | Checklist, PR reviews |

### Risk Score

**Overall risk**: MEDIUM-LOW

The refactoring is primarily extracting existing code into new modules with minimal logic changes. Risk is controlled through:
- Comprehensive test suite
- Gradual migration
- Clear documentation
- Code review process

---

## Technical Debt Quantification

### Debt Categories

| Category | Instances | Severity | Effort (days) | Impact |
|----------|-----------|----------|---------------|--------|
| Code duplication | 4 | Critical | 2 | High |
| Architecture violations | 2 | High | 1 | High |
| Missing tests | ~15 | Moderate | 1 | Medium |
| Missing type hints | ~50 | Low | 0.5 | Low |
| Large modules | 2 | Moderate | 1 | Medium |
| Generic exceptions | All | Moderate | 0.5 | Medium |

**Total technical debt**: ~6 days effort

### Debt Payoff

Fixing critical and high-severity issues:
- **Time investment**: 3 days
- **Maintenance time saved**: ~2 days per release
- **ROI**: Positive after 2 releases
- **Code quality improvement**: Significant

---

## Pre-Release Checklist

### Code Quality

- [ ] Duplicate code eliminated
- [ ] Configuration centralized
- [ ] Domain layer pure (no I/O)
- [ ] Custom exceptions defined
- [ ] Type hints > 90% coverage
- [ ] No modules > 400 lines (without good reason)

### Testing

- [ ] Unit test coverage > 80%
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] New infrastructure modules tested
- [ ] Error paths tested

### Documentation

- [ ] ARCHITECTURE_REVIEW.md reviewed
- [ ] REFACTORING_PLAN.md followed
- [ ] CHANGELOG.md updated
- [ ] CLAUDE.md updated
- [ ] API documentation complete

### Release

- [ ] Version bumped to 1.0.0
- [ ] Git tags created
- [ ] Release notes written
- [ ] Migration guide (if needed)

---

## Conclusion

The codebase has solid foundations but accumulated technical debt that must be addressed before v1.0:

**Current state**: 257 lines of duplicate code, scattered configuration, architectural violations

**After refactoring**: Clean architecture, centralized config, testable infrastructure layer

**Effort required**: 4-6 days focused work

**Benefit**: Maintainable, extensible, production-ready codebase

**Recommendation**: Complete refactoring before v1.0 release. Current state is "beta quality" not "production quality".
