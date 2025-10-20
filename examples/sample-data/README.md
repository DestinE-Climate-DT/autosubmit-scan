# Sample Data for Testing autosubmit-scan

This directory contains realistic climate model and HPC log files for testing and learning autosubmit-scan.

## What's Included

### Log Files

1. **climate_model_success.log** - Successful CESM climate model run
   - Duration: 9 hours
   - No errors
   - Useful for testing pattern matching (should find no errors)

2. **slurm_oom_error.log** - Out-of-memory (OOM) error
   - Job killed due to memory limit
   - Contains: `oom-kill` error
   - Memory usage climbs from 70% to 99% before failure
   - Exit code: 137

3. **slurm_timeout.log** - Time limit exceeded
   - Job cancelled after 12 hours
   - Contains: `TIME LIMIT` error
   - Shows checkpoint attempt before cancellation
   - Exit code: 124

4. **python_error.log** - Python TypeError
   - Post-processing script failure
   - Contains: Python `Traceback`
   - Type mismatch: string vs float operation

5. **mpi_failure.log** - MPI communication error
   - Parallel simulation failure
   - Contains: `MPI_ERR_TRUNCATE` error
   - 256 processes across 32 nodes
   - Node 17 communication failure

### Catalog

**sample_catalog.yaml** - Pre-configured error catalog
- Defines patterns for all 5 error types
- Ready to use with the sample log files
- Includes meaningful error descriptions and suggestions

## Quick Start

### 1. Run Your First Scan

```bash
# From the autosubmit-scan root directory
cd examples/sample-data

# Run scan with pixi
pixi run as-scan scan \
  --catalog sample_catalog.yaml \
  --output ../../sample_scan_results \
  --cores 4

# Or with pip
as-scan scan \
  --catalog sample_catalog.yaml \
  --output ../../sample_scan_results \
  --cores 4
```

### 2. View Results

```bash
# Interactive TUI
pixi run as-scan view ../../sample_scan_results/report.json

# Or with pip
as-scan view ../../sample_scan_results/report.json
```

### 3. Export Report

```bash
# Export to Markdown
pixi run as-scan export \
  ../../sample_scan_results/report.json \
  --template markdown \
  --output ../../sample_scan_report.md

# Or with pip
as-scan export \
  ../../sample_scan_results/report.json \
  --template markdown \
  --output ../../sample_scan_report.md
```

## Expected Results

The scan should find **4 errors** across **4 log files**:

| Error Type | File | Line | Description |
|------------|------|------|-------------|
| `out_of_memory` | slurm_oom_error.log | ~15 | SLURM OOM kill event |
| `timeout_error` | slurm_timeout.log | ~30 | Time limit cancellation |
| `python_traceback` | python_error.log | ~21 | Python TypeError traceback |
| `mpi_communication_error` | mpi_failure.log | ~23 | MPI communication failure |

**climate_model_success.log** should have **0 errors** (successful run).

## Learning Exercises

### Exercise 1: Modify the Catalog

Try adding a new error pattern:

```yaml
memory_warning:
  id: "memory_warning"
  pattern:
    type: "literal"
    pattern: "WARNING: Memory usage"
  files:
    - "*.log"
  meaning: "Memory usage is high but not critical yet"
  suggestion: "Monitor memory usage, may lead to OOM if it continues growing"
  context_lines: 3
  next_errors: []
  metadata:
    severity: "low"
    category: "resource"
```

Re-run the scan and check if it finds the warnings in `slurm_oom_error.log`.

### Exercise 2: Change Context Lines

Edit `sample_catalog.yaml` and change `context_lines: 5` to `context_lines: 10` for the `out_of_memory` error.

Re-run the scan and compare how much context is shown in the results.

### Exercise 3: Use Regex Patterns

Change the `python_traceback` pattern from literal to regex to catch variations:

```yaml
python_traceback:
  pattern:
    type: "regex"
    pattern: "Traceback|Exception|Error:"
    flags: ["IGNORECASE"]
```

### Exercise 4: Test Railway Pattern (Advanced)

Add a railway pattern chain to automatically check for memory warnings when OOM is found:

```yaml
out_of_memory:
  id: "out_of_memory"
  pattern:
    type: "literal"
    pattern: "oom-kill"
  files:
    - "*.log"
  next_errors:
    - error_id: "memory_warning"
      when:
        type: "always"  # Always check for warnings when OOM is found
  # ... rest of definition

memory_warning:
  id: "memory_warning"
  pattern:
    type: "literal"
    pattern: "WARNING: Memory usage"
  files:
    - "*.log"
  # ... rest of definition
```

Re-run the scan. The tool should now automatically check for memory warnings in the same file where it found the OOM error.

## Cross-Platform Notes

These sample files work on:
- **macOS** ✓
- **Linux** ✓
- **Windows** ✓ (with WSL or Git Bash)

The paths use relative references (`*.log`), so they work regardless of your file system.

## Realistic Climate Modeling Context

These logs are based on real climate modeling workflows:

- **CESM** (Community Earth System Model) - Atmospheric simulations
- **WRF** (Weather Research and Forecasting) - Weather modeling
- **NEMO** (Nucleus for European Modelling of the Ocean) - Ocean simulations
- **SLURM** (Simple Linux Utility for Resource Management) - HPC job scheduler
- **MPI** (Message Passing Interface) - Parallel computing standard

The error patterns and scenarios reflect common issues in HPC climate modeling:
- Memory exhaustion from large datasets
- Long simulations hitting time limits
- Python post-processing failures
- Network/hardware issues in parallel runs

## Next Steps

After experimenting with sample data:

1. **Read the guides:**
   - [docs/QUICK_START_FOR_STUDENTS.md](../../docs/QUICK_START_FOR_STUDENTS.md)
   - [docs/USER_GUIDE.md](../../docs/USER_GUIDE.md)
   - [docs/GLOSSARY.md](../../docs/GLOSSARY.md)

2. **Try advanced tutorials:**
   - [docs/tutorials/02_pattern_matching.ipynb](../../docs/tutorials/02_pattern_matching.ipynb)
   - [docs/tutorials/04_railway_pattern.ipynb](../../docs/tutorials/04_railway_pattern.ipynb)

3. **Create your own catalog:**
   - Use your actual log files
   - Define patterns for your specific errors
   - Test and iterate

4. **Scan remote files:**
   - Set up SSH ControlMaster (see [docs/SSH_CONNECTION_POOLING.md](../../docs/SSH_CONNECTION_POOLING.md))
   - Update catalog with SSH URIs
   - Scan HPC cluster logs

## Troubleshooting

### "No files matched pattern"

Make sure you're running the command from the `examples/sample-data` directory, or use absolute paths in the catalog.

### "No matches found"

Check that:
1. The pattern text matches exactly (case-sensitive for literal patterns)
2. You're scanning the correct files (`files: ["*.log"]` looks in current directory)

### "Command not found"

- With pixi: Always use `pixi run as-scan ...`
- With pip: Make sure you installed with `pip install -e .`

## Contributing

Found an issue with the sample data? Please open an issue on GitHub or submit a pull request.

---

**Created:** Week 1, Day 5 (Documentation Overhaul)

**Purpose:** Provide working, cross-platform sample data for learning and testing
