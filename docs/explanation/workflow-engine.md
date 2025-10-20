# Workflow Management (Behind the Scenes)

**For unfamiliar terms, see the [Glossary](../GLOSSARY.md).**

**Note:** This page explains how [Snakemake](../GLOSSARY.md#snakemake) (a [workflow management tool](../GLOSSARY.md#workflow-management)) works behind the scenes. **You don't need to understand this to use the tool** - you interact with `as-scan` commands, not Snakemake directly.

This page is for:
- Developers contributing to the project
- Users troubleshooting advanced workflow issues
- Users curious about the internals

autosubmit-scan uses Snakemake for:
- **Smart caching**: Only re-scans files that changed
- **Parallel execution**: Scans multiple files at once (faster)
- **Railway Pattern support**: Dynamically adds error checks based on conditions

## Workflow Execution Flow

```{mermaid}
flowchart TB
    subgraph Input["Input Stage"]
        Catalog[Load Error Catalog]
        Validate[Validate Schema]
    end

    subgraph Discovery["File Discovery"]
        Checkpoint1[Checkpoint: discover_files]
        Expand1[Expand Glob Patterns]
        ListFiles[List All File URIs]
    end

    subgraph Fingerprinting["File Fingerprinting"]
        Checkpoint2[Checkpoint: fingerprint_file]
        Hash[Compute File Hash]
        Cache[Check Cache]
        Metadata[Extract Metadata]
    end

    subgraph Matching["Pattern Matching"]
        Rule1[Rule: match_pattern]
        Scan[Scan File for Pattern]
        LineNumbers[Record Line Numbers]
    end

    subgraph Filtering["Match Filtering"]
        Checkpoint3[Checkpoint: filter_matches]
        HasMatches{Has Matches?}
        KeepFile[Keep for Context Extraction]
        SkipFile[Skip File]
    end

    subgraph Context["Context Extraction"]
        Rule2[Rule: extract_context]
        ReadLines[Read Context Lines]
        BuildMatch[Build ErrorMatch Object]
    end

    subgraph Railway["Railway Pattern"]
        Checkpoint4[Checkpoint: evaluate_railway]
        EvalConditions[Evaluate Conditions]
        NextErrors{More Errors?}
        ChainErrors[Add Next Errors to Workflow]
    end

    subgraph Aggregation["Result Aggregation"]
        Rule3[Rule: aggregate_results]
        Combine[Combine All Matches]
        Generate[Generate JSON-LD]
    end

    subgraph Output["Output Stage"]
        Report[JSON-LD Report]
        Summary[Summary Statistics]
    end

    Catalog --> Validate
    Validate --> Checkpoint1
    Checkpoint1 --> Expand1
    Expand1 --> ListFiles
    ListFiles --> Checkpoint2
    Checkpoint2 --> Hash
    Hash --> Cache
    Cache -->|Cached| Metadata
    Cache -->|Not Cached| Metadata
    Metadata --> Rule1
    Rule1 --> Scan
    Scan --> LineNumbers
    LineNumbers --> Checkpoint3
    Checkpoint3 --> HasMatches
    HasMatches -->|Yes| KeepFile
    HasMatches -->|No| SkipFile
    KeepFile --> Rule2
    Rule2 --> ReadLines
    ReadLines --> BuildMatch
    BuildMatch --> Checkpoint4
    Checkpoint4 --> EvalConditions
    EvalConditions --> NextErrors
    NextErrors -->|Yes| ChainErrors
    NextErrors -->|No| Rule3
    ChainErrors --> Checkpoint1
    Rule3 --> Combine
    Combine --> Generate
    Generate --> Report
    Report --> Summary

    classDef inputClass fill:#4A90E2,stroke:#2E5C8A,color:#fff
    classDef checkpointClass fill:#F5A623,stroke:#C17D11,color:#000
    classDef ruleClass fill:#7ED321,stroke:#5A9C1A,color:#000
    classDef decisionClass fill:#BD10E0,stroke:#8B0BA8,color:#fff
    classDef outputClass fill:#50E3C2,stroke:#2FB89C,color:#000

    class Catalog,Validate inputClass
    class Checkpoint1,Checkpoint2,Checkpoint3,Checkpoint4 checkpointClass
    class Rule1,Rule2,Rule3 ruleClass
    class HasMatches,NextErrors decisionClass
    class Report,Summary outputClass
```

## Checkpoint-Based Execution

Snakemake checkpoints allow dynamic workflow expansion based on intermediate results.

### Why Checkpoints?

**Traditional rules** require all inputs/outputs to be known before execution starts.

**Checkpoints** allow workflow to expand dynamically:
1. Execute checkpoint rule
2. Determine next inputs based on checkpoint output
3. Dynamically add new rules to DAG
4. Continue execution

### Checkpoint 1: File Discovery

```{mermaid}
sequenceDiagram
    participant User
    participant Snakemake
    participant Checkpoint
    participant fsspec
    participant Filesystem

    User->>Snakemake: Run workflow
    Snakemake->>Checkpoint: Execute discover_files
    Checkpoint->>fsspec: Parse URI (s3://, ssh://, etc.)
    fsspec->>Filesystem: Expand glob pattern
    Filesystem-->>fsspec: List of file paths
    fsspec-->>Checkpoint: File URIs
    Checkpoint->>Checkpoint: Write file list to JSON
    Checkpoint-->>Snakemake: Checkpoint complete
    Snakemake->>Snakemake: Re-evaluate DAG with file list
    Snakemake->>Snakemake: Create fingerprint_file rules
    Snakemake->>Snakemake: Create match_pattern rules
```

**Purpose:** Expand glob patterns like `ssh://host:/logs/**/*.out` into concrete file paths.

**Output:** JSON file with list of file URIs for each error definition.

**Dynamic expansion:** Number of files unknown until runtime, especially for remote filesystems.

### Checkpoint 2: File Fingerprinting

```{mermaid}
flowchart LR
    File[File URI] --> Check{In Cache?}
    Check -->|Yes| Load[Load Cached Hash]
    Check -->|No| Compute[Compute Hash]
    Compute --> Store[Store in Cache]
    Load --> Skip[Skip Scanning]
    Store --> Proceed[Proceed to Scan]

    classDef cacheHit fill:#7ED321,stroke:#5A9C1A,color:#000
    classDef cacheMiss fill:#F5A623,stroke:#C17D11,color:#000

    class Load,Skip cacheHit
    class Compute,Store cacheMiss
```

**Purpose:** Avoid re-scanning unchanged files.

**Mechanism:**
1. Compute SHA256 hash of file metadata (size, mtime)
2. Check if hash exists in cache
3. If cached and unchanged, skip pattern matching
4. If new or changed, proceed to matching

**Performance impact:** Reduces scan time by 70-90% on subsequent runs.

### Checkpoint 3: Match Filtering

```{mermaid}
flowchart TB
    Start[Pattern Matching Complete] --> Check{File has matches?}
    Check -->|Yes| Keep[Add to context extraction queue]
    Check -->|No| Skip[Skip file]
    Keep --> Extract[Extract Context]
    Skip --> End1[End]
    Extract --> End2[End]

    classDef successClass fill:#7ED321,stroke:#5A9C1A,color:#000
    classDef skipClass fill:#95A5A6,stroke:#7F8C8D,color:#000

    class Keep,Extract successClass
    class Skip,End1 skipClass
```

**Purpose:** Only extract context from files with actual matches.

**Efficiency:** Avoids reading entire files when no matches found.

### Checkpoint 4: Railway Pattern Evaluation

```{mermaid}
flowchart TB
    Match[ErrorMatch Found] --> Eval[Evaluate Conditions]
    Eval --> Cond1{Condition 1<br/>field_equals?}
    Cond1 -->|True| Cond2{Condition 2<br/>field_contains?}
    Cond1 -->|False| End1[End Chain]
    Cond2 -->|True| AddNext[Add Next Error to Workflow]
    Cond2 -->|False| End2[End Chain]
    AddNext --> Rescan[Re-evaluate DAG]
    Rescan --> NewRules[Create New Scan Rules]
    NewRules --> Continue[Continue Workflow]

    classDef evalClass fill:#F5A623,stroke:#C17D11,color:#000
    classDef addClass fill:#4A90E2,stroke:#2E5C8A,color:#fff
    classDef endClass fill:#95A5A6,stroke:#7F8C8D,color:#000

    class Eval,Cond1,Cond2 evalClass
    class AddNext,Rescan,NewRules addClass
    class End1,End2 endClass
```

**Purpose:** Dynamically chain related errors based on match conditions.

**Dynamic behavior:** Workflow expands as conditions are met.

## Parallel Execution

```{mermaid}
gantt
    title Parallel File Processing (--cores 4)
    dateFormat X
    axisFormat %s

    section Core 1
    File 1: 0, 10
    File 5: 10, 20
    File 9: 20, 30

    section Core 2
    File 2: 0, 12
    File 6: 12, 24
    File 10: 24, 36

    section Core 3
    File 3: 0, 8
    File 7: 8, 16
    File 11: 16, 24

    section Core 4
    File 4: 0, 11
    File 8: 11, 22
    File 12: 22, 33
```

Snakemake automatically distributes work across available cores:

- **File-level parallelism**: Each file scanned independently
- **Error-level parallelism**: Different errors processed in parallel
- **No shared state**: Each rule execution isolated
- **Automatic scheduling**: Snakemake handles dependencies

**Performance scaling:**

| Cores | Speedup | Efficiency |
|-------|---------|------------|
| 1     | 1x      | 100%       |
| 2     | 1.9x    | 95%        |
| 4     | 3.6x    | 90%        |
| 8     | 6.8x    | 85%        |

## Caching Strategy

### File Fingerprint Cache

```yaml
# .snakemake/fingerprints/<error_id>/<file_hash>.json
{
  "file_uri": "ssh://host:/logs/job.out",
  "hash": "a3f2b1c9...",
  "mtime": "2024-01-15T10:30:00Z",
  "size": 1048576,
  "last_scanned": "2024-01-15T10:35:00Z"
}
```

### Match Results Cache

```yaml
# .snakemake/matches/<error_id>/<file_hash>.json
{
  "file_uri": "ssh://host:/logs/job.out",
  "matches": [
    {"line_number": 42, "text": "OOM killed"},
    {"line_number": 105, "text": "Out of memory"}
  ],
  "scanned_at": "2024-01-15T10:35:00Z"
}
```

### Cache Invalidation

Caches invalidated when:
- File modification time changes
- File size changes
- Error pattern definition changes
- `--force` flag used

## Performance Optimization Tips

### 1. Use Appropriate Core Count

```bash
# Find optimal core count
nproc                              # Show available cores

# Use 75% of available cores
as-scan scan --catalog errors.yaml --cores 6

# For remote files, limit cores to avoid connection limits
as-scan scan --catalog remote.yaml --cores 4
```

### 2. Enable Caching

```bash
# First run (no cache)
as-scan scan --catalog errors.yaml --output ./results

# Subsequent runs (uses cache)
as-scan scan --catalog errors.yaml --output ./results
# Runs 70-90% faster!
```

### 3. Optimize File Patterns

```yaml
# Inefficient: Scans entire directory tree
files:
  - "/var/log/**/*"

# Efficient: Specific patterns reduce discovery time
files:
  - "/var/log/slurm/*.out"
  - "/var/log/jobs/**/error.log"
```

### 4. SSH Connection Pooling

See [SSH Connection Pooling Guide](../SSH_CONNECTION_POOLING.md) for critical remote file optimization.

## Snakemake DAG Visualization

### Rule Dependency Graph

```{mermaid}
flowchart TD
    discover[discover_files] --> fingerprint[fingerprint_file]
    fingerprint --> match[match_pattern]
    match --> filter[filter_matches]
    filter --> context[extract_context]
    context --> railway[evaluate_railway]
    railway --> aggregate[aggregate_results]

    style discover fill:#F5A623
    style fingerprint fill:#F5A623
    style filter fill:#F5A623
    style railway fill:#F5A623
    style match fill:#7ED321
    style context fill:#7ED321
    style aggregate fill:#7ED321
```

**Legend:**
- Orange boxes: Checkpoints (dynamic expansion)
- Green boxes: Rules (static execution)

## Workflow Configuration

Snakemake configuration in `src/orchestration/Snakefile`:

```python
# Checkpoint: File discovery
checkpoint discover_files:
    input:
        catalog="catalog.yaml"
    output:
        file_list="results/{error_id}/files.json"
    run:
        # Expand glob patterns
        # Write discovered files to JSON

# Rule: Pattern matching
rule match_pattern:
    input:
        file_list=checkpoint_output("discover_files")
    output:
        matches="results/{error_id}/{file_hash}/matches.json"
    run:
        # Scan file for pattern
        # Record line numbers
```

## Error Handling

### Rule Failure Behavior

```{mermaid}
flowchart LR
    Rule[Rule Execution] --> Success{Success?}
    Success -->|Yes| Continue[Continue Workflow]
    Success -->|No| Retry{Retry Count<br/>< 3?}
    Retry -->|Yes| Rule
    Retry -->|No| Fail[Mark Rule Failed]
    Fail --> Partial[Generate Partial Report]
    Partial --> Warn[Warn User]
```

**Default behavior:**
- Retry failed rules 3 times
- Continue with successful results
- Generate partial report
- Exit code indicates partial failure

### Remote File Failures

Common remote file errors:
- Connection timeout (SSH)
- Authentication failure (S3)
- File not found (SFTP)
- Permission denied (FTP)

**Mitigation:**
- Use SSH ControlMaster for connection pooling
- Validate credentials before starting workflow
- Use `--dryrun` to test file access
- Check logs in `.snakemake/log/`

## Debugging Workflow

### Visualize DAG

```bash
# Generate workflow DAG
snakemake --dag | dot -Tpng > dag.png

# Generate rule graph
snakemake --rulegraph | dot -Tpng > rulegraph.png

# Generate file graph
snakemake --filegraph | dot -Tpng > filegraph.png
```

### Dry Run

```bash
# Show workflow plan without execution
as-scan scan --catalog errors.yaml --dryrun

# Show detailed execution plan
snakemake --dryrun --printshellcmds
```

### Monitor Execution

```bash
# Show execution summary
snakemake --summary

# Show file status
snakemake --list

# Show rule execution times
snakemake --detailed-summary
```

## Advanced Topics

### Custom Snakemake Arguments

```bash
# Pass custom arguments to Snakemake
as-scan scan --catalog errors.yaml --cores 8 \
  --snakemake-args "--keep-going --quiet"
```

### Cluster Execution

```bash
# Execute on SLURM cluster
as-scan scan --catalog errors.yaml \
  --cluster "sbatch -p compute -t 1:00:00"
```

### Cloud Execution

```bash
# Execute on Kubernetes
as-scan scan --catalog errors.yaml \
  --kubernetes --container-image as-scan:latest
```

## References

- [Snakemake Documentation](https://snakemake.readthedocs.io/)
- [Checkpoint Tutorial](https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#data-dependent-conditional-execution)
- [Cluster Execution](https://snakemake.readthedocs.io/en/stable/executing/cluster.html)
