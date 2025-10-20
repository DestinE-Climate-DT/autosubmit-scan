# Railway Pattern Deep Dive

**For unfamiliar terms, see the [Glossary](../GLOSSARY.md).**

The [Railway Pattern](../GLOSSARY.md#railway-pattern) is an automatic error flowchart system. When the tool finds one error, it can automatically check for related errors based on [conditions](../GLOSSARY.md#condition) you define.

## Concept

The Railway Pattern mimics how human operators troubleshoot systems. When an error is detected, the tool automatically checks for related errors based on runtime [conditions](../GLOSSARY.md#condition).

### Real-World Analogy

Imagine troubleshooting a failed batch job:

1. **Primary error**: "Job killed"
2. **Question**: "Why was it killed?"
3. **Check memory logs** → If OOM error found: "Memory issue"
4. **Question**: "Is this a known issue?"
5. **Check configuration** → If memory < recommended: "Increase memory"
6. **Action**: Create ticket with specific recommendation

The Railway pattern automates this decision tree.

## Basic Flow

```{mermaid}
flowchart LR
    Scan[Scan Logs] --> E1{Error 1<br/>Found?}
    E1 -->|Yes| M1[ErrorMatch 1]
    E1 -->|No| End1([End])

    M1 --> C1{Condition<br/>Met?}
    C1 -->|Yes| E2[Scan for Error 2]
    C1 -->|No| End2([End])

    E2 --> M2{Error 2<br/>Found?}
    M2 -->|Yes| Match2[ErrorMatch 2]
    M2 -->|No| End3([End])

    Match2 --> Report[Add to Report]
    Report --> End4([End])

    classDef errorClass fill:#E74C3C,stroke:#C0392B,color:#fff
    classDef condClass fill:#F39C12,stroke:#E67E22,color:#fff
    classDef successClass fill:#27AE60,stroke:#229954,color:#fff
    classDef endClass fill:#95A5A6,stroke:#7F8C8D,color:#fff

    class E1,E2,M2 errorClass
    class C1 condClass
    class M1,Match2,Report successClass
    class End1,End2,End3,End4 endClass
```

## Catalog Syntax

### Simple Chain (Always)

```yaml
errors:
  primary_error:
    id: "primary_error"
    pattern:
      type: "literal"
      pattern: "ERROR: System failure"
    next_errors:
      - error_id: "secondary_error"
        when:
          type: "always"

  secondary_error:
    id: "secondary_error"
    pattern:
      type: "regex"
      pattern: "Root cause: (.*)"
```

**Behavior:** Always scan for `secondary_error` when `primary_error` is found.

### Conditional Chain (Field Equals)

```yaml
errors:
  oom_error:
    id: "oom_error"
    pattern:
      type: "literal"
      pattern: "OOM killed"
    next_errors:
      - error_id: "memory_check"
        when:
          type: "field_equals"
          field: "metadata.severity"
          value: "critical"
    metadata:
      severity: "critical"

  memory_check:
    id: "memory_check"
    pattern:
      type: "callable"
      pattern: "checks:verify_memory"
```

**Behavior:** Only scan for `memory_check` if `severity` is `"critical"`.

## Condition Types

### 1. Always

```yaml
when:
  type: "always"
```

Always execute the next error check.

**Use case:** Mandatory follow-up checks.

### 2. Field Equals

```yaml
when:
  type: "field_equals"
  field: "metadata.priority"
  operator: "=="
  value: "high"
```

**Operators:** `==`, `!=`, `>`, `<`, `>=`, `<=`

**Use case:** Numeric or string comparisons.

### 3. Field Contains

```yaml
when:
  type: "field_contains"
  field: "matched_text"
  operator: "contains"
  value: "timeout"
```

**Operators:** `contains`, `not_contains`, `startswith`, `endswith`

**Use case:** Substring matching in error text.

### 4. Field Regex

```yaml
when:
  type: "field_regex"
  field: "file_uri"
  operator: "regex"
  value: ".*production.*"
```

**Use case:** Pattern matching in any field.

### 5. Logical AND

```yaml
when:
  type: "and"
  conditions:
    - type: "field_equals"
      field: "severity"
      value: "critical"
    - type: "field_contains"
      field: "matched_text"
      value: "production"
```

**Behavior:** All conditions must be true.

### 6. Logical OR

```yaml
when:
  type: "or"
  conditions:
    - type: "field_contains"
      field: "matched_text"
      value: "urgent"
    - type: "field_equals"
      field: "priority"
      value: "high"
```

**Behavior:** At least one condition must be true.

### 7. Custom Callable

```yaml
when:
  type: "custom"
  callable: "my_module.conditions:is_business_hours"
```

**Function signature:**

```python
from src.domain.models import ErrorMatch, ErrorDefinition, ErrorCatalog

def is_business_hours(
    match: ErrorMatch,
    error_def: ErrorDefinition,
    catalog: ErrorCatalog
) -> bool:
    """Check if error occurred during business hours."""
    from datetime import datetime
    hour = datetime.now().hour
    return 9 <= hour <= 17
```

**Use case:** Complex logic that can't be expressed with built-in conditions.

## Complex Chaining Example

### Scenario: HPC Job Failure Troubleshooting

```{mermaid}
flowchart TB
    Start([Scan Job Logs]) --> JobFail{Job Failed?}
    JobFail -->|Yes| CheckOOM{OOM Error?}
    JobFail -->|No| End1([No Issues])

    CheckOOM -->|Yes| MemMatch[ErrorMatch: OOM]
    CheckOOM -->|No| CheckTimeout{Timeout?}

    MemMatch --> MemSeverity{Severity<br/>Critical?}
    MemSeverity -->|Yes| MemAlloc[Check Memory<br/>Allocation]
    MemSeverity -->|No| End2([Log Only])

    MemAlloc --> MemConfig{Configured<br/>< 100GB?}
    MemConfig -->|Yes| Recommend[Recommend<br/>Memory Increase]
    MemConfig -->|No| Escalate[Escalate to<br/>Ops Team]

    CheckTimeout -->|Yes| TimeMatch[ErrorMatch: Timeout]
    CheckTimeout -->|No| CheckDisk{Disk Full?}

    TimeMatch --> TimeSeverity{Production<br/>Environment?}
    TimeSeverity -->|Yes| NotifyOps[Notify Ops]
    TimeSeverity -->|No| End3([Log Only])

    CheckDisk -->|Yes| DiskMatch[ErrorMatch: Disk Full]
    CheckDisk -->|No| End4([Unknown Error])

    DiskMatch --> DiskCheck{Free Space<br/>< 10%?}
    DiskCheck -->|Yes| Cleanup[Trigger Cleanup]
    DiskCheck -->|No| End5([Monitor])

    Recommend --> Ticket1[Create Ticket]
    Escalate --> Alert1[Send Alert]
    NotifyOps --> Alert2[Send Alert]
    Cleanup --> Ticket2[Create Ticket]

    Ticket1 --> End6([Complete])
    Alert1 --> End6
    Alert2 --> End6
    Ticket2 --> End6

    classDef errorClass fill:#E74C3C,stroke:#C0392B,color:#fff
    classDef checkClass fill:#F39C12,stroke:#E67E22,color:#fff
    classDef actionClass fill:#3498DB,stroke:#2980B9,color:#fff
    classDef endClass fill:#95A5A6,stroke:#7F8C8D,color:#fff

    class JobFail,CheckOOM,CheckTimeout,CheckDisk,MemSeverity,MemConfig,TimeSeverity,DiskCheck checkClass
    class MemMatch,TimeMatch,DiskMatch errorClass
    class MemAlloc,Recommend,Escalate,NotifyOps,Cleanup,Ticket1,Alert1,Alert2,Ticket2 actionClass
    class Start,End1,End2,End3,End4,End5,End6 endClass
```

### Catalog Implementation

```yaml
version: "1.0.0"
schema_version: "1.0.0"

errors:
  # Primary error: Job failure
  job_failure:
    id: "job_failure"
    pattern:
      type: "regex"
      pattern: "Job.*failed|SLURM.*error"
      flags: ["IGNORECASE"]
    files:
      - "ssh://hpc:/logs/**/*.out"
    next_errors:
      - error_id: "oom_error"
        when:
          type: "always"
      - error_id: "timeout_error"
        when:
          type: "always"
      - error_id: "disk_full_error"
        when:
          type: "always"
    metadata:
      severity: "high"

  # Branch 1: OOM handling
  oom_error:
    id: "oom_error"
    pattern:
      type: "literal"
      pattern: "OOM killed"
    next_errors:
      - error_id: "memory_allocation_check"
        when:
          type: "field_equals"
          field: "metadata.severity"
          value: "critical"
    metadata:
      severity: "critical"

  memory_allocation_check:
    id: "memory_allocation_check"
    pattern:
      type: "callable"
      pattern: "checks:check_memory_config"
    next_errors:
      - error_id: "recommend_memory_increase"
        when:
          type: "custom"
          callable: "checks:memory_below_threshold"
      - error_id: "escalate_to_ops"
        when:
          type: "custom"
          callable: "checks:memory_above_threshold_still_failing"

  recommend_memory_increase:
    id: "recommend_memory_increase"
    pattern:
      type: "literal"
      pattern: "MEMORY_RECOMMENDATION"
    next_errors:
      - error_id: "create_ticket"
        when:
          type: "always"
    metadata:
      action: "recommend_increase"

  # Branch 2: Timeout handling
  timeout_error:
    id: "timeout_error"
    pattern:
      type: "regex"
      pattern: "Timeout|Time limit exceeded"
      flags: ["IGNORECASE"]
    next_errors:
      - error_id: "notify_operations"
        when:
          type: "and"
          conditions:
            - type: "field_contains"
              field: "file_uri"
              value: "production"
            - type: "field_equals"
              field: "metadata.severity"
              value: "critical"
    metadata:
      severity: "critical"

  # Branch 3: Disk full handling
  disk_full_error:
    id: "disk_full_error"
    pattern:
      type: "regex"
      pattern: "No space left on device|Disk quota exceeded"
    next_errors:
      - error_id: "trigger_cleanup"
        when:
          type: "custom"
          callable: "checks:disk_space_critical"

  # Terminal actions
  escalate_to_ops:
    id: "escalate_to_ops"
    pattern:
      type: "literal"
      pattern: "ESCALATE"
    metadata:
      action: "send_alert"
      urgency: "immediate"

  notify_operations:
    id: "notify_operations"
    pattern:
      type: "literal"
      pattern: "NOTIFY"
    metadata:
      action: "send_alert"

  create_ticket:
    id: "create_ticket"
    pattern:
      type: "literal"
      pattern: "CREATE_TICKET"
    metadata:
      action: "create_ticket"

  trigger_cleanup:
    id: "trigger_cleanup"
    pattern:
      type: "literal"
      pattern: "CLEANUP_NEEDED"
    metadata:
      action: "trigger_cleanup_job"
```

## Field Access Patterns

### Accessing ErrorMatch Fields

```yaml
when:
  type: "field_equals"
  field: "line_number"
  value: 42
```

**Available fields:**
- `error_id`: Error definition ID
- `file_uri`: Source file URI
- `line_number`: Line number of match
- `matched_text`: Text that matched pattern
- `context_before`: List of lines before match
- `context_after`: List of lines after match
- `meaning`: Error meaning
- `suggestion`: Suggested fix
- `metadata.*`: Any metadata field

### Nested Field Access

```yaml
when:
  type: "field_equals"
  field: "metadata.environment"
  value: "production"
```

### Array Indexing

```yaml
when:
  type: "field_contains"
  field: "context_before[0]"  # First line before match
  value: "WARNING"
```

```yaml
when:
  type: "field_contains"
  field: "context_after[-1]"  # Last line after match
  value: "CRITICAL"
```

## Custom Condition Examples

### Example 1: Time-Based Routing

```python
# checks/timing.py

from datetime import datetime
from src.domain.models import ErrorMatch, ErrorDefinition, ErrorCatalog

def is_business_hours(
    match: ErrorMatch,
    error_def: ErrorDefinition,
    catalog: ErrorCatalog
) -> bool:
    """Check if error occurred during business hours (9 AM - 5 PM)."""
    hour = datetime.now().hour
    return 9 <= hour <= 17

def is_weekend(
    match: ErrorMatch,
    error_def: ErrorDefinition,
    catalog: ErrorCatalog
) -> bool:
    """Check if error occurred on weekend."""
    return datetime.now().weekday() >= 5
```

**Usage:**

```yaml
next_errors:
  - error_id: "escalate_immediate"
    when:
      type: "or"
      conditions:
        - type: "custom"
          callable: "checks.timing:is_weekend"
        - type: "custom"
          callable: "checks.timing:is_business_hours"
```

### Example 2: Context Analysis

```python
# checks/context.py

def has_previous_error(
    match: ErrorMatch,
    error_def: ErrorDefinition,
    catalog: ErrorCatalog
) -> bool:
    """Check if ERROR appears in previous lines."""
    return any("ERROR" in line for line in match.context_before)

def memory_pattern_in_context(
    match: ErrorMatch,
    error_def: ErrorDefinition,
    catalog: ErrorCatalog
) -> bool:
    """Check for memory-related keywords in context."""
    memory_keywords = ["memory", "OOM", "malloc", "alloc"]
    full_context = " ".join(match.context_before + match.context_after)
    return any(keyword.lower() in full_context.lower() for keyword in memory_keywords)
```

### Example 3: Severity Escalation

```python
# checks/severity.py

def repeated_error(
    match: ErrorMatch,
    error_def: ErrorDefinition,
    catalog: ErrorCatalog
) -> bool:
    """Check if same error appears multiple times in context."""
    pattern = match.matched_text
    count = sum(1 for line in match.context_before + match.context_after if pattern in line)
    return count >= 3

def critical_severity_with_production(
    match: ErrorMatch,
    error_def: ErrorDefinition,
    catalog: ErrorCatalog
) -> bool:
    """Check if critical severity in production environment."""
    is_critical = match.metadata.get("severity") == "critical"
    is_production = "production" in match.file_uri.lower()
    return is_critical and is_production
```

## Performance Considerations

### 1. Chain Depth

**Recommendation:** Keep chains shallow (2-3 levels max).

**Why:** Deep chains increase execution time and complexity.

**Bad:**
```
Error1 → Error2 → Error3 → Error4 → Error5 → Error6
```

**Good:**
```
Error1 → Error2 → Action
Error1 → Error3 → Action
```

### 2. Condition Complexity

**Simple conditions** (field_equals, field_contains) are fast.

**Complex conditions** (custom callables) add overhead.

**Optimization:**
- Use built-in conditions when possible
- Cache expensive computations in custom functions
- Avoid network calls in conditions

### 3. Avoid Circular Dependencies

**Bad:**
```yaml
error_a:
  next_errors:
    - error_id: "error_b"

error_b:
  next_errors:
    - error_id: "error_a"  # Circular!
```

**Detection:** Workflow will fail with circular dependency error.

## Debugging Railway Chains

### 1. Dry Run

```bash
as-scan scan --catalog errors.yaml --dryrun
```

Shows planned workflow including railway expansions.

### 2. Verbose Logging

```bash
as-scan scan --catalog errors.yaml --verbose
```

Logs condition evaluations and decisions.

### 3. Visualize Workflow

```bash
# Generate DAG after railway evaluation
snakemake --dag | dot -Tpng > railway_dag.png
```

### 4. Test Conditions Independently

```python
# test_conditions.py

from src.domain.models import ErrorMatch
from checks.severity import critical_severity_with_production

# Create test match
match = ErrorMatch(
    error_id="test",
    file_uri="ssh://prod-server:/logs/job.out",
    line_number=42,
    matched_text="OOM killed",
    metadata={"severity": "critical"}
)

# Test condition
result = critical_severity_with_production(match, None, None)
print(f"Condition result: {result}")  # Should be True
```

## Best Practices

### 1. Document Chain Logic

```yaml
errors:
  primary_error:
    id: "primary_error"
    next_errors:
      - error_id: "secondary_error"
        when:
          type: "field_equals"
          field: "severity"
          value: "critical"
        # Document why this chain exists
        description: "Critical errors require immediate memory check"
```

### 2. Use Meaningful Error IDs

**Bad:**
```yaml
error_1 → error_2 → error_3
```

**Good:**
```yaml
oom_detected → check_memory_config → recommend_increase
```

### 3. Test Edge Cases

- Empty context
- Missing metadata fields
- Null values
- Unexpected field types

### 4. Provide Fallbacks

```yaml
next_errors:
  - error_id: "specific_check"
    when:
      type: "field_equals"
      field: "environment"
      value: "production"
  - error_id: "general_check"
    when:
      type: "always"  # Fallback for non-production
```

## References

- [Condition Types Reference](../reference/condition-types.md)
- [Custom Callable Guide](../how-to/custom-conditions.md)
- [Performance Tuning](../how-to/performance-tuning.md)
