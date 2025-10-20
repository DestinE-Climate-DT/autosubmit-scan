# Autosubmit-Scan Architecture Review

## Executive Summary

This review identifies critical architectural issues that must be addressed before v1.0 release. While the core layered architecture remains sound, recent additions (fsspec support, variable extraction, GitHub URIs) have introduced significant code duplication, configuration management problems, and separation of concerns violations.

**RECOMMENDATION**: Refactor identified issues before release. Current state: 6/10 for production readiness.

---

## 1. Architecture & Design Patterns

### 1.1 Layer Structure Assessment

**Current State**: GOOD with concerns

The five-layer architecture is conceptually sound:
- CLI Layer (Click-based)
- Domain Layer (Pydantic models)
- Matching Layer (Strategy pattern)
- Orchestration Layer (Snakemake + Railway pattern)
- Reporting Layer (JSON-LD, templates)

**Issues Identified**:

1. **CLI Layer Leaking Into Domain**: The completion.py module (650 lines) mixes filesystem operations with SSH config parsing - this belongs in infrastructure/utilities layer, not CLI.

2. **Domain Layer Impurity**: `catalog.py` and `templates.py` contain I/O operations and GitHub URI parsing logic. Domain should only contain pure business logic and models.

### 1.2 Railway Pattern Implementation

**Status**: COHERENT but underutilized

The Railway pattern is well-implemented:
- `RailwayExecutor` cleanly evaluates conditions
- `RailwayPlanner` builds DAG correctly
- `ConditionEvaluator` supports nested logic

**Strength**: Clean separation between planning (build DAG) and execution (evaluate conditions).

**No violations found** - this is one of the cleanest parts of the codebase.

### 1.3 Strategy Pattern for Matching

**Status**: EXCELLENT

Pattern matcher implementation is textbook:
- `BasePatternMatcher` abstract base class
- Three concrete implementations (Literal, Regex, Callable)
- Factory pattern for instantiation
- Clean abstraction over different matching strategies

**No issues** - this should serve as reference for other parts of the codebase.

### 1.4 Pydantic Model Validation

**Status**: GOOD with minor issues

Models are well-validated with:
- Field validators for all critical fields
- Model validators for cross-field validation
- Proper use of Pydantic v2 features

**Minor Issue**: Some validation logic in `validation.py` should be moved to separate utility module (see Section 5).

---

## 2. Code Quality Issues

### 2.1 CRITICAL: Code Duplication

#### Issue 1: GitHub URI Parsing (CRITICAL)

**Duplicated in 3 files**:

1. **catalog.py** (lines 65-108):
```python
if path.startswith("github://"):
    try:
        rest = path[len("github://"):]
        org_repo, ref_and_path = rest.split("@", 1)
        org, repo = org_repo.split(":", 1)

        # Find where the ref ends and path begins
        path_markers = ["templates/", "examples/", "src/", "config/", "catalogs/"]
        ref = None
        file_path = None

        for marker in path_markers:
            if marker in ref_and_path:
                ref, file_path = ref_and_path.split(f"/{marker}", 1)
                file_path = marker + file_path
                break
```

2. **templates.py** (lines 49-82):
```python
if uri.startswith("github://"):
    try:
        parts = uri.replace("github://", "").split("@", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid GitHub URI format: {uri}")

        org_repo = parts[0]
        ref_and_path = parts[1]

        # Split org:repo
        if ":" not in org_repo:
            raise ValueError(f"Invalid GitHub URI format (missing :): {uri}")
        org, repo = org_repo.split(":", 1)

        # Find where the path starts (after known path markers or first /)
        path_markers = ["templates/", "examples/", "src/", "docs/"]
        ref = None
        file_path = None

        for marker in path_markers:
            if marker in ref_and_path:
                ref, file_path = ref_and_path.split(marker, 1)
                file_path = marker + file_path
                ref = ref.rstrip("/")
                break
```

**BOTH implementations**:
- Parse the same GitHub URI format
- Have different path markers lists
- Have slightly different error handling
- Access GitHub credentials identically

**IMPACT**:
- Maintenance nightmare - bugs must be fixed in multiple places
- Inconsistent behavior between catalog and template loading
- Violates DRY principle

**SEVERITY**: CRITICAL - Must fix before v1.0

**Recommended Fix**:
Create `src/infrastructure/github.py`:

```python
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class GitHubURI:
    """Parsed GitHub URI components."""
    org: str
    repo: str
    ref: str
    path: str

class GitHubURIParser:
    """Parse and validate GitHub URIs.

    Format: github://org:repo@ref/path/to/file
    """

    # Canonical list of path markers for detecting ref boundaries
    PATH_MARKERS = [
        "templates/",
        "examples/",
        "src/",
        "docs/",
        "config/",
        "catalogs/",
    ]

    @classmethod
    def parse(cls, uri: str) -> GitHubURI:
        """Parse GitHub URI into components.

        Args:
            uri: GitHub URI string

        Returns:
            GitHubURI with parsed components

        Raises:
            ValueError: If URI format is invalid
        """
        if not uri.startswith("github://"):
            raise ValueError(f"Not a GitHub URI: {uri}")

        # Remove protocol
        rest = uri[len("github://"):]

        # Split org:repo and ref/path
        if "@" not in rest:
            raise ValueError(f"Invalid GitHub URI (missing @): {uri}")
        org_repo, ref_and_path = rest.split("@", 1)

        # Split org:repo
        if ":" not in org_repo:
            raise ValueError(f"Invalid GitHub URI (missing :): {uri}")
        org, repo = org_repo.split(":", 1)

        # Find where ref ends and path begins using path markers
        ref = None
        file_path = None

        for marker in cls.PATH_MARKERS:
            if f"/{marker}" in ref_and_path:
                ref, file_path = ref_and_path.split(f"/{marker}", 1)
                file_path = marker + file_path
                break

        if ref is None or file_path is None:
            raise ValueError(
                f"Cannot parse GitHub URI (missing known path marker): {uri}\n"
                f"Expected one of: {', '.join(cls.PATH_MARKERS)}"
            )

        return GitHubURI(org=org, repo=repo, ref=ref, path=file_path)

    @staticmethod
    def get_credentials() -> tuple[Optional[str], Optional[str]]:
        """Get GitHub credentials from environment.

        Returns:
            Tuple of (username, token) or (None, None)
        """
        username = os.environ.get("GITHUB_USERNAME") or os.environ.get("GH_USERNAME")
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

        return (username, token) if username and token else (None, None)
```

Then both `catalog.py` and `templates.py` use:
```python
from src.infrastructure.github import GitHubURIParser

parsed = GitHubURIParser.parse(uri)
username, token = GitHubURIParser.get_credentials()
# Use parsed.org, parsed.repo, parsed.ref, parsed.path
```

#### Issue 2: SSH Config Parsing (CRITICAL)

**Duplicated in 2 files**:

1. **completion.py** has `_parse_ssh_config()` method (lines 328-387)
2. **completion.py** also has standalone `_parse_ssh_config_standalone()` function (lines 65-124)

BOTH functions:
- Parse ~/.ssh/config identically
- Extract Host, HostName, User, Port, IdentityFile
- Have identical logic
- 60+ lines of duplication WITHIN THE SAME FILE

**SEVERITY**: CRITICAL - This is egregious

**Recommended Fix**:
Create `src/infrastructure/ssh_config.py`:

```python
from dataclasses import dataclass
from pathlib import Path
import os

@dataclass
class SSHConfig:
    """SSH configuration for a host."""
    hostname: str
    user: str
    port: int = 22
    identity_file: Optional[str] = None

class SSHConfigParser:
    """Parse OpenSSH configuration files."""

    @staticmethod
    def parse_host(alias: str, config_path: Optional[Path] = None) -> SSHConfig:
        """Parse SSH config to get connection details for an alias.

        Args:
            alias: SSH host alias (e.g., 'mn5', 'lumi')
            config_path: Path to SSH config file (defaults to ~/.ssh/config)

        Returns:
            SSHConfig with resolved connection details
        """
        if config_path is None:
            config_path = Path.home() / ".ssh" / "config"

        config = SSHConfig(
            hostname=alias,  # Default to alias if not found
            user=os.getenv("USER", ""),
            port=22,
        )

        if not config_path.exists():
            return config

        in_target_host = False

        with open(config_path) as f:
            for line in f:
                line = line.strip()

                # New Host section
                if line.startswith("Host "):
                    host_line = line[5:].strip()
                    hosts_in_line = host_line.split()
                    in_target_host = alias in hosts_in_line
                    continue

                # Parse config options for our target host
                if in_target_host and line:
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        key, value = parts
                        key_lower = key.lower()

                        if key_lower == "hostname":
                            config.hostname = value
                        elif key_lower == "user":
                            config.user = value
                        elif key_lower == "port":
                            try:
                                config.port = int(value)
                            except ValueError:
                                pass
                        elif key_lower == "identityfile":
                            config.identity_file = os.path.expanduser(value)

        return config
```

#### Issue 3: fsspec URI Detection (MODERATE)

**Duplicated in 4 files**:

1. `catalog.py`: `is_fsspec_uri()` (lines 24-35)
2. `templates.py`: `is_fsspec_uri()` (lines 15-24)
3. `variable_extractor.py`: `_is_fsspec_uri()` (lines 35-44)
4. `completion.py`: Uses inline checks

All have identical logic:
```python
def is_fsspec_uri(path: str) -> bool:
    return "://" in path and not path.startswith("file://")
```

**Recommended Fix**:
Create `src/infrastructure/uri_utils.py`:

```python
def is_remote_uri(uri: str) -> bool:
    """Check if URI is a remote fsspec URI (not local file).

    Args:
        uri: Path or URI string

    Returns:
        True if URI has a protocol and is not file://
    """
    return "://" in uri and not uri.startswith("file://")

def is_github_uri(uri: str) -> bool:
    """Check if URI is a GitHub URI."""
    return uri.startswith("github://")

def is_ssh_uri(uri: str) -> bool:
    """Check if URI is SSH/SFTP URI."""
    return uri.startswith(("ssh://", "sftp://"))
```

### 2.2 Configuration Management (CRITICAL)

#### Issue 1: Hardcoded DEFAULT_TEMPLATE_URI

**Location**: `src/cli/commands/default.py` (line 20-23)

```python
DEFAULT_TEMPLATE_URI = os.getenv(
    "AUTOSUBMIT_SCAN_DEFAULT_TEMPLATE",
    "github://DestinE-Climate-DT:autosubmit-scan-error-catalogs@test/dynamic-variables/templates/default_autosubmit.yaml",
)
```

**Problems**:
1. Only ONE place reads this environment variable
2. Branch name `test/dynamic-variables` is hardcoded in default value
3. No centralized configuration
4. Other modules might need default templates but have no access

**Recommended Fix**:
Create `src/config.py`:

```python
import os
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class AutosubmitScanConfig:
    """Centralized configuration for autosubmit-scan.

    All configuration should be accessed through this class.
    Environment variables are read once at startup.
    """

    # GitHub repository for default templates
    default_template_repo_org: str = "DestinE-Climate-DT"
    default_template_repo_name: str = "autosubmit-scan-error-catalogs"
    default_template_branch: str = "main"  # Use main, not test branch
    default_template_path: str = "templates/default_autosubmit.yaml"

    # Autosubmit defaults
    autosubmit_default_host: str = "mn5"
    autosubmit_default_base_path: str = "/gpfs/scratch/ehpc01/awi478153"

    # Override from environment
    github_username: Optional[str] = None
    github_token: Optional[str] = None

    @classmethod
    def from_env(cls) -> "AutosubmitScanConfig":
        """Create configuration from environment variables."""
        return cls(
            default_template_repo_org=os.getenv(
                "AUTOSUBMIT_SCAN_TEMPLATE_ORG",
                cls.default_template_repo_org
            ),
            default_template_repo_name=os.getenv(
                "AUTOSUBMIT_SCAN_TEMPLATE_REPO",
                cls.default_template_repo_name
            ),
            default_template_branch=os.getenv(
                "AUTOSUBMIT_SCAN_TEMPLATE_BRANCH",
                cls.default_template_branch
            ),
            default_template_path=os.getenv(
                "AUTOSUBMIT_SCAN_TEMPLATE_PATH",
                cls.default_template_path
            ),
            autosubmit_default_host=os.getenv(
                "AUTOSUBMIT_HOST",
                cls.autosubmit_default_host
            ),
            autosubmit_default_base_path=os.getenv(
                "AUTOSUBMIT_BASE_PATH",
                cls.autosubmit_default_base_path
            ),
            github_username=os.getenv("GITHUB_USERNAME") or os.getenv("GH_USERNAME"),
            github_token=os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN"),
        )

    @property
    def default_template_uri(self) -> str:
        """Get complete URI for default template."""
        return (
            f"github://{self.default_template_repo_org}:"
            f"{self.default_template_repo_name}@{self.default_template_branch}/"
            f"{self.default_template_path}"
        )

# Global config instance
_config: Optional[AutosubmitScanConfig] = None

def get_config() -> AutosubmitScanConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = AutosubmitScanConfig.from_env()
    return _config
```

Then `default.py` becomes:
```python
from src.config import get_config

config = get_config()
DEFAULT_TEMPLATE_URI = config.default_template_uri
```

### 2.3 God Classes and Large Modules

#### Issue 1: completion.py (650 lines) - MODERATE

**Problems**:
- Mixes SSH config parsing, filesystem operations, URI normalization
- Has both a class and standalone functions doing similar things
- Should be split into smaller, focused modules

**Recommended Split**:
1. `src/infrastructure/ssh_config.py` - SSH config parsing
2. `src/infrastructure/uri_utils.py` - URI normalization and detection
3. `src/infrastructure/filesystem.py` - Filesystem operations with caching
4. `src/cli/completers.py` - Just the completer classes

#### Issue 2: default.py Hardcoded Fallback Template (133 lines) - MODERATE

Lines 29-132 contain a massive YAML string as fallback template.

**Better approach**:
1. Move fallback template to `src/templates/fallback_catalog.yaml`
2. Use `importlib.resources` to load it
3. Makes it easier to maintain and test

```python
from importlib import resources

def load_fallback_template() -> str:
    """Load fallback catalog template from package resources."""
    return resources.read_text("src.templates", "fallback_catalog.yaml")
```

### 2.4 Error Handling and Exception Types

**Status**: NEEDS IMPROVEMENT

**Issues**:
1. No custom exception hierarchy defined
2. Generic exceptions (ValueError, RuntimeError, FileNotFoundError) used everywhere
3. Difficult to handle specific error cases in calling code

**Recommended Fix**:
Create `src/exceptions.py`:

```python
class AutosubmitScanError(Exception):
    """Base exception for all autosubmit-scan errors."""
    pass

class ConfigurationError(AutosubmitScanError):
    """Configuration or setup error."""
    pass

class CatalogError(AutosubmitScanError):
    """Error related to catalog loading or validation."""
    pass

class CatalogLoadError(CatalogError):
    """Failed to load catalog from URI."""
    pass

class CatalogValidationError(CatalogError):
    """Catalog validation failed."""
    pass

class TemplateError(AutosubmitScanError):
    """Template rendering error."""
    pass

class VariableExtractionError(AutosubmitScanError):
    """Failed to extract variable from source."""
    pass

class URIError(AutosubmitScanError):
    """Invalid or unsupported URI."""
    pass

class GitHubURIError(URIError):
    """Invalid GitHub URI format."""
    pass

class RemoteAccessError(AutosubmitScanError):
    """Failed to access remote resource."""
    pass

class SSHError(RemoteAccessError):
    """SSH connection or operation failed."""
    pass
```

Then update all raise statements to use specific exceptions:

```python
# Before
raise ValueError(f"Invalid GitHub URI: {uri}")

# After
raise GitHubURIError(f"Invalid GitHub URI: {uri}")
```

### 2.5 Type Hints

**Status**: GOOD with gaps

**Good**:
- All Pydantic models have full type hints
- Most functions have return type hints
- Modern syntax (e.g., `list[str]` not `List[str]`)

**Missing**:
- Some helper functions lack hints
- Callback functions in completion.py

---

## 3. Dependency Management

### 3.1 Current Dependencies

**From pixi.toml**:
```toml
fsspec = ">=2024.9.0"
paramiko = ">=4.0.0,<5"
boto3 = ">=1.35.0,<2"
s3fs = ">=2024.9.0"
sshfs = ">=2024.9.0"
```

**Analysis**: GOOD

- No obvious conflicts
- Version constraints are reasonable
- Uses conda-forge channel appropriately

**Minor Issue**: Both `paramiko` and `sshfs` (which uses `asyncssh`) are present. This could lead to confusion about which SSH implementation to use.

**Recommendation**: Document which module should use which:
- `sshfs` (asyncssh) for file operations via fsspec
- `paramiko` only if you need direct SSH operations (currently not used?)

Check if `paramiko` is actually needed:

```bash
git grep -n "import paramiko" src/
```

If not used, remove from dependencies.

### 3.2 Missing Dependencies

None identified. All imports have corresponding dependencies.

---

## 4. Separation of Concerns Violations

### 4.1 Domain Layer Impurity (CRITICAL)

**Problem**: Domain modules (`catalog.py`, `templates.py`) perform I/O operations

**Violation**:
```python
# src/domain/catalog.py (line 38)
def load_catalog(path: str) -> ErrorCatalog:
    """Load error catalog from YAML file or fsspec URI."""
    # ... 100+ lines of fsspec, GitHub, file I/O
```

**Domain layer should**:
- Define models (ErrorCatalog, ErrorDefinition, etc.)
- Define validation rules
- Define domain logic (pure functions)

**Domain layer should NOT**:
- Read from filesystem
- Make network requests
- Parse URIs

**Recommended Fix**:

Create proper repository pattern:

```
src/
  domain/
    models.py           # Pydantic models (current)
    validation.py       # Validation functions (current)
  infrastructure/
    catalog_repository.py     # NEW: Catalog loading/saving
    template_repository.py    # NEW: Template loading
    github.py                 # NEW: GitHub URI parsing
    ssh_config.py             # NEW: SSH config parsing
    uri_utils.py              # NEW: URI utilities
    filesystem.py             # NEW: Filesystem operations
```

**catalog_repository.py**:
```python
from abc import ABC, abstractmethod
from src.domain.models import ErrorCatalog

class CatalogRepository(ABC):
    """Abstract repository for loading/saving catalogs."""

    @abstractmethod
    def load(self, uri: str) -> ErrorCatalog:
        """Load catalog from URI."""
        pass

    @abstractmethod
    def save(self, catalog: ErrorCatalog, uri: str) -> None:
        """Save catalog to URI."""
        pass

class FsspecCatalogRepository(CatalogRepository):
    """Catalog repository using fsspec for storage."""

    def load(self, uri: str) -> ErrorCatalog:
        """Load catalog from any fsspec-compatible URI."""
        # Current catalog.py logic goes here
        pass

    def save(self, catalog: ErrorCatalog, uri: str) -> None:
        """Save catalog to any fsspec-compatible URI."""
        # Current save_catalog logic goes here
        pass
```

Then CLI commands use:
```python
from src.infrastructure.catalog_repository import FsspecCatalogRepository

repo = FsspecCatalogRepository()
catalog = repo.load("github://...")
```

### 4.2 CLI Module Doing Infrastructure Work (MODERATE)

**Problem**: `completion.py` handles SSH connections, filesystem caching

**Fix**: Move filesystem operations to `src/infrastructure/filesystem.py`

---

## 5. Technical Debt Summary

### 5.1 Must Fix Before v1.0 (CRITICAL)

1. Deduplicate GitHub URI parsing (catalog.py, templates.py)
2. Deduplicate SSH config parsing (completion.py - 2 functions!)
3. Centralize configuration (create config.py)
4. Move I/O out of domain layer (repository pattern)
5. Define custom exception hierarchy

**Estimated effort**: 2-3 days

### 5.2 Should Fix Before v1.0 (HIGH)

1. Split completion.py into focused modules
2. Move fallback template to resource file
3. Remove paramiko if unused
4. Add type hints to remaining functions

**Estimated effort**: 1 day

### 5.3 Nice to Have (MODERATE)

1. Add more comprehensive tests for duplicated code paths
2. Create architecture decision records (ADRs)
3. Document which SSH library is used where

**Estimated effort**: 1 day

---

## 6. What's Working Well (Keep This)

### 6.1 Excellent Patterns

1. **Railway Pattern**: Clean, testable, well-separated
2. **Strategy Pattern for Matching**: Textbook implementation
3. **Pydantic Models**: Comprehensive validation
4. **Layer Structure**: Conceptually sound

### 6.2 Good Code Quality

1. **Type hints**: Generally good coverage
2. **Docstrings**: Well-documented
3. **Test organization**: Clear markers for unit/integration/e2e
4. **CLI UX**: Nice shortcuts (expid detection)

---

## 7. Breaking Changes Risk Assessment

### 7.1 Proposed Refactoring Impact

**Low Risk** (backward compatible):
- Create config.py (add new module)
- Create infrastructure/ modules (new modules)
- Add custom exceptions (catch more specific, fall back to base)

**Medium Risk** (internal API change):
- Repository pattern requires CLI changes
- Functions move between modules (imports change)

**High Risk** (breaking):
- None - all proposed changes are internal refactoring

### 7.2 Migration Path

1. Create new modules alongside existing code
2. Add deprecation warnings to old functions
3. Update CLI commands to use new APIs
4. Remove old code in subsequent commit
5. Release as v1.0

---

## 8. Specific Code Examples to Fix

### Example 1: Deduplicate GitHub Parsing

**File**: `src/infrastructure/github.py` (NEW)

See Section 2.1, Issue 1 for complete implementation.

**Changes needed**:
- Update `src/domain/catalog.py` line 65-108
- Update `src/domain/templates.py` line 49-82

**Testing**:
```python
def test_github_uri_parser():
    uri = "github://DestinE-Climate-DT:autosubmit-scan@main/templates/default.yaml"
    parsed = GitHubURIParser.parse(uri)

    assert parsed.org == "DestinE-Climate-DT"
    assert parsed.repo == "autosubmit-scan"
    assert parsed.ref == "main"
    assert parsed.path == "templates/default.yaml"
```

### Example 2: Centralize Configuration

**File**: `src/config.py` (NEW)

See Section 2.2 for complete implementation.

**Changes needed**:
- Update `src/cli/commands/default.py` line 20-23

### Example 3: Repository Pattern

**File**: `src/infrastructure/catalog_repository.py` (NEW)

```python
from pathlib import Path
from typing import Any
import yaml
import fsspec
from src.domain.models import ErrorCatalog
from src.infrastructure.github import GitHubURIParser
from src.infrastructure.uri_utils import is_remote_uri, is_github_uri

class CatalogRepository:
    """Repository for loading and saving error catalogs."""

    def load(self, uri: str) -> ErrorCatalog:
        """Load catalog from URI.

        Supports:
        - GitHub URIs: github://org:repo@ref/path
        - Remote URIs: s3://, ssh://, sftp://
        - Local files: /path/to/catalog.yaml

        Args:
            uri: Catalog location

        Returns:
            Loaded ErrorCatalog instance

        Raises:
            CatalogLoadError: If catalog cannot be loaded
            CatalogValidationError: If catalog structure is invalid
        """
        try:
            if is_github_uri(uri):
                data = self._load_from_github(uri)
            elif is_remote_uri(uri):
                data = self._load_from_fsspec(uri)
            else:
                data = self._load_from_local(uri)

            # Parse and validate
            return ErrorCatalog(**data)

        except Exception as e:
            from src.exceptions import CatalogLoadError
            raise CatalogLoadError(f"Failed to load catalog from {uri}: {e}") from e

    def _load_from_github(self, uri: str) -> dict[str, Any]:
        """Load catalog from GitHub."""
        from src.config import get_config

        parsed = GitHubURIParser.parse(uri)
        config = get_config()

        # Create GitHub filesystem
        fs_kwargs = {"org": parsed.org, "repo": parsed.repo, "sha": parsed.ref}

        if config.github_username and config.github_token:
            fs_kwargs["username"] = config.github_username
            fs_kwargs["token"] = config.github_token

        fs = fsspec.filesystem("github", **fs_kwargs)

        with fs.open(parsed.path, "r") as f:
            return yaml.safe_load(f)

    def _load_from_fsspec(self, uri: str) -> dict[str, Any]:
        """Load catalog from fsspec URI."""
        with fsspec.open(uri, "r") as f:
            return yaml.safe_load(f)

    def _load_from_local(self, path: str) -> dict[str, Any]:
        """Load catalog from local file."""
        file_path = Path(path)

        if not file_path.exists():
            from src.exceptions import CatalogLoadError
            raise CatalogLoadError(f"Catalog file not found: {path}")

        with open(file_path) as f:
            return yaml.safe_load(f)
```

**Usage in CLI**:
```python
from src.infrastructure.catalog_repository import CatalogRepository

repo = CatalogRepository()
catalog = repo.load("github://...")  # Works
catalog = repo.load("/local/path")   # Works
catalog = repo.load("s3://bucket")   # Works
```

---

## 9. Testing Gaps

### Current Coverage

Based on 26 test files and project structure:
- Unit tests exist for core patterns (matching, railway)
- Integration tests for remote access
- E2E tests for workflows

### Identified Gaps

1. **No tests for duplicated code paths**
   - GitHub URI parsing has 2 implementations, need tests for both
   - SSH config parsing has 2 implementations, need tests for both

2. **No tests for configuration**
   - Environment variable handling not tested
   - Default values not tested

3. **Error handling paths undertested**
   - What happens when GitHub API rate limits?
   - What happens when SSH connection fails?
   - What happens when template rendering fails?

### Recommended New Tests

```python
# tests/infrastructure/test_github_uri_parser.py
class TestGitHubURIParser:
    def test_parse_valid_uri(self):
        uri = "github://org:repo@main/templates/file.yaml"
        parsed = GitHubURIParser.parse(uri)
        assert parsed.org == "org"
        assert parsed.repo == "repo"
        assert parsed.ref == "main"
        assert parsed.path == "templates/file.yaml"

    def test_parse_branch_with_slash(self):
        uri = "github://org:repo@feature/my-branch/templates/file.yaml"
        parsed = GitHubURIParser.parse(uri)
        assert parsed.ref == "feature/my-branch"

    def test_parse_invalid_format(self):
        with pytest.raises(GitHubURIError):
            GitHubURIParser.parse("github://invalid")

# tests/infrastructure/test_ssh_config_parser.py
class TestSSHConfigParser:
    def test_parse_host_with_config(self, tmp_path):
        config_file = tmp_path / "config"
        config_file.write_text("""
Host myhost
    HostName example.com
    User testuser
    Port 2222
    IdentityFile ~/.ssh/mykey
""")
        config = SSHConfigParser.parse_host("myhost", config_file)
        assert config.hostname == "example.com"
        assert config.user == "testuser"
        assert config.port == 2222
```

---

## 10. Recommendations Summary

### Priority 1: MUST FIX (Before v1.0)

1. Create `src/infrastructure/github.py` - deduplicate GitHub URI parsing
2. Create `src/infrastructure/ssh_config.py` - deduplicate SSH config parsing
3. Create `src/infrastructure/uri_utils.py` - deduplicate URI detection
4. Create `src/config.py` - centralize configuration
5. Create `src/exceptions.py` - proper exception hierarchy
6. Create `src/infrastructure/catalog_repository.py` - move I/O out of domain

**Timeline**: 3-4 days
**Risk**: Low (internal refactoring)

### Priority 2: SHOULD FIX (Before v1.0)

1. Split `completion.py` into focused modules
2. Move fallback template to resource file
3. Verify and remove unused `paramiko` dependency
4. Add comprehensive tests for new infrastructure modules

**Timeline**: 1-2 days
**Risk**: Low

### Priority 3: NICE TO HAVE (After v1.0)

1. Create architecture decision records
2. Add more error handling tests
3. Document SSH library usage patterns
4. Consider adding observability (metrics, tracing)

**Timeline**: 1 day
**Risk**: None

### Total Effort Estimate

**Critical + High priority**: 4-6 days of focused work
**All recommendations**: 5-7 days total

---

## 11. Release Readiness Checklist

Before releasing v1.0, ensure:

- [ ] All CRITICAL issues resolved (Section 5.1)
- [ ] All HIGH issues resolved (Section 5.2)
- [ ] Test coverage > 80% for new infrastructure code
- [ ] All duplicated code removed
- [ ] Configuration centralized
- [ ] Custom exceptions implemented
- [ ] Repository pattern implemented
- [ ] Documentation updated
- [ ] CHANGELOG.md created
- [ ] Migration guide written (if API changed)

---

## 12. Final Verdict

**Current State**: 6/10 for production readiness

**Strengths**:
- Core architecture (Railway, Strategy patterns) is excellent
- Pydantic validation is comprehensive
- Test structure is good
- CLI UX is thoughtful

**Critical Issues**:
- Severe code duplication (GitHub URI, SSH config)
- Configuration management is scattered
- Domain layer has I/O violations
- No custom exception hierarchy

**Recommendation**:

Do NOT release as v1.0 without addressing critical issues. The technical debt is manageable but must be fixed to avoid maintenance nightmares. The proposed refactoring is low-risk and will significantly improve code quality.

With 4-6 days of focused refactoring, this project can reach production quality for v1.0 release.

---

## Contact

For questions about this review, contact the architecture team or open a discussion issue in the repository.
