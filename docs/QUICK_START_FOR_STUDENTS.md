# Quick Start for Students

**Time required:** 30 minutes
**Prerequisites:** Basic command-line knowledge, Python installed
**Outcome:** Complete your first scan and understand the results

---

## What You'll Do

By the end of this tutorial, you will:
1. Install autosubmit-scan
2. Create realistic sample log files
3. Write your first error catalog
4. Run a scan that finds errors
5. View and understand the results
6. Know what to learn next

---

## Step 1: Installation (5 minutes)

### Option A: Using Pixi (Recommended)

Pixi is a modern Python package manager that handles all dependencies automatically.

**Install Pixi:**
- **macOS/Linux:**
  ```bash
  curl -fsSL https://pixi.sh/install.sh | bash
  ```

- **Windows:**
  ```powershell
  iwr -useb https://pixi.sh/install.ps1 | iex
  ```

**Install autosubmit-scan:**
```bash
# Clone the repository
git clone https://github.com/DestinE-Climate-DT/autosubmit-scan.git
cd autosubmit-scan

# Install dependencies
pixi install

# Verify installation
pixi run as-scan --help
```

**Expected output:**
```
Usage: as-scan [OPTIONS] COMMAND [ARGS]...

  Autosubmit error scanner - Remote log analysis tool

Commands:
  init      Create sample error catalog
  scan      Run error scanning workflow
  validate  Validate error catalog
  view      Launch interactive TUI
  export    Export report with template
```

### Option B: Using pip

If you already have Python 3.12+ and pip installed:

```bash
# Clone the repository
git clone https://github.com/DestinE-Climate-DT/autosubmit-scan.git
cd autosubmit-scan

# Install in editable mode
pip install -e .

# Verify installation
as-scan --help
```

**Troubleshooting:**

| Problem | Solution |
|---------|----------|
| "Command 'pixi' not found" after install | Close and reopen your terminal, or run `source ~/.bashrc` |
| "Python version error" | autosubmit-scan requires Python 3.12+. Check with `python --version` |
| Permission error with pip | Use `pip install --user -e .` or a virtual environment |

---

## Step 2: Create Sample Log Files (5 minutes)

Instead of scanning system logs (which might not exist on your computer), we'll create realistic sample log files.

**Create a working directory:**

```bash
# Create sample_logs directory (in the autosubmit-scan folder)
mkdir -p sample_logs
cd sample_logs
```

**Create sample_logs/job_success.log:**

```bash
cat > job_success.log << 'EOF'
[2024-10-20 10:00:00] Job 12345 starting
[2024-10-20 10:00:01] Loading configuration from config.yaml
[2024-10-20 10:00:02] Initializing climate model simulation
[2024-10-20 10:00:03] Allocated 32 GB RAM for arrays
[2024-10-20 10:00:05] Reading input data: era5_temperature.nc
[2024-10-20 10:00:10] Starting simulation for timestep 1/100
[2024-10-20 10:01:15] Simulation progress: 50% complete
[2024-10-20 10:02:20] Simulation progress: 100% complete
[2024-10-20 10:02:21] Writing output to results/simulation_output.nc
[2024-10-20 10:02:25] Simulation completed successfully
[2024-10-20 10:02:26] Total runtime: 146 seconds
[2024-10-20 10:02:27] Job 12345 finished
EOF
```

**Create sample_logs/job_oom_error.log:**

```bash
cat > job_oom_error.log << 'EOF'
[2024-10-20 11:00:00] Job 12346 starting
[2024-10-20 11:00:01] Loading configuration from config.yaml
[2024-10-20 11:00:02] Initializing climate model simulation
[2024-10-20 11:00:03] Allocated 32 GB RAM for arrays
[2024-10-20 11:00:05] Reading input data: era5_temperature.nc
[2024-10-20 11:00:06] WARNING: Large dataset detected (120 GB)
[2024-10-20 11:00:10] Starting simulation for timestep 1/100
[2024-10-20 11:00:45] Memory usage: 28 GB / 32 GB
[2024-10-20 11:01:15] Memory usage: 31.5 GB / 32 GB
[2024-10-20 11:01:18] WARNING: Memory usage critical
[2024-10-20 11:01:20] slurmstepd: error: Detected 1 oom-kill event(s) in StepId=12346
[2024-10-20 11:01:21] Process killed by SLURM (OOM)
[2024-10-20 11:01:22] Exit code: 137
[2024-10-20 11:01:23] Job 12346 failed
EOF
```

**Create sample_logs/job_timeout.log:**

```bash
cat > job_timeout.log << 'EOF'
[2024-10-20 12:00:00] Job 12347 starting
[2024-10-20 12:00:01] Loading configuration from config.yaml
[2024-10-20 12:00:02] Initializing climate model simulation
[2024-10-20 12:00:03] Allocated 32 GB RAM for arrays
[2024-10-20 12:00:05] Reading input data: era5_temperature.nc
[2024-10-20 12:00:10] Starting simulation for timestep 1/1000
[2024-10-20 12:30:15] Simulation progress: 25% complete
[2024-10-20 13:00:20] Simulation progress: 50% complete
[2024-10-20 13:30:25] Simulation progress: 75% complete
[2024-10-20 13:59:50] Simulation progress: 99% complete
[2024-10-20 13:59:55] Time limit warning: 5 seconds remaining
[2024-10-20 14:00:00] CANCELLED AT 2024-10-20T14:00:00 DUE TO TIME LIMIT
[2024-10-20 14:00:01] Exit code: 124
[2024-10-20 14:00:02] Job 12347 failed
EOF
```

**Create sample_logs/python_traceback.log:**

```bash
cat > python_traceback.log << 'EOF'
[2024-10-20 13:00:00] Running data processing script
[2024-10-20 13:00:01] Loading pandas and numpy
[2024-10-20 13:00:02] Reading CSV file: climate_data.csv
[2024-10-20 13:00:03] Processing 100,000 rows
[2024-10-20 13:00:05] Applying temperature conversion
[2024-10-20 13:00:06] Traceback (most recent call last):
[2024-10-20 13:00:06]   File "process_data.py", line 45, in <module>
[2024-10-20 13:00:06]     result = convert_temperature(data)
[2024-10-20 13:00:06]   File "process_data.py", line 23, in convert_temperature
[2024-10-20 13:00:06]     return (temp - 32) * 5/9
[2024-10-20 13:00:06] TypeError: unsupported operand type(s) for -: 'str' and 'int'
[2024-10-20 13:00:07] Script failed
[2024-10-20 13:00:08] Exit code: 1
EOF
```

**Verify files were created:**

```bash
ls -lh
```

**Expected output:**
```
total 16K
-rw-r--r-- 1 user user  645 Oct 20 15:00 job_oom_error.log
-rw-r--r-- 1 user user  456 Oct 20 15:00 job_success.log
-rw-r--r-- 1 user user  587 Oct 20 15:00 job_timeout.log
-rw-r--r-- 1 user user  532 Oct 20 15:00 python_traceback.log
```

---

## Step 3: Create Your First Catalog (10 minutes)

A **catalog** is a YAML file that tells autosubmit-scan:
- What errors to look for (patterns)
- Where to find log files (file paths)
- What each error means and how to fix it

**Create sample_logs/my_first_catalog.yaml:**

```bash
cat > my_first_catalog.yaml << 'EOF'
version: "1.0.0"
schema_version: "1.0.0"

metadata:
  name: "Student Quick Start Catalog"
  description: "My first error catalog for learning autosubmit-scan"
  author: "Student Name"
  created: "2024-10-20T15:00:00Z"
  updated: "2024-10-20T15:00:00Z"

errors:
  # Error 1: Out of Memory (OOM) errors
  out_of_memory:
    id: "out_of_memory"
    pattern:
      type: "literal"
      pattern: "oom-kill"
    files:
      - "*.log"
    meaning: "Job was killed because it ran out of memory"
    suggestion: "Increase memory allocation in your job script (e.g., #SBATCH --mem=64GB)"
    context_lines: 3
    next_errors: []
    metadata:
      severity: "critical"
      category: "resource"

  # Error 2: Time limit exceeded
  timeout_error:
    id: "timeout_error"
    pattern:
      type: "literal"
      pattern: "TIME LIMIT"
    files:
      - "*.log"
    meaning: "Job exceeded the requested wall-clock time and was cancelled"
    suggestion: "Increase time limit in job script (e.g., #SBATCH --time=04:00:00) or optimize code"
    context_lines: 3
    next_errors: []
    metadata:
      severity: "high"
      category: "resource"

  # Error 3: Python errors
  python_traceback:
    id: "python_traceback"
    pattern:
      type: "literal"
      pattern: "Traceback (most recent call last)"
    files:
      - "*.log"
    meaning: "Python script crashed with an exception"
    suggestion: "Review the traceback to identify the error line and fix the code"
    context_lines: 5
    next_errors: []
    metadata:
      severity: "medium"
      category: "code"
EOF
```

**Understanding the catalog:**

Let's break down the `out_of_memory` error definition:

```yaml
out_of_memory:                    # Error ID (used to reference this error)
  id: "out_of_memory"            # Must match the key above
  pattern:
    type: "literal"               # Exact text matching (simplest pattern type)
    pattern: "oom-kill"           # Look for this exact text in logs
  files:
    - "*.log"                     # Scan all .log files in current directory
  meaning: "Job was killed..."    # What does this error mean?
  suggestion: "Increase memory..." # How to fix it
  context_lines: 3                # Show 3 lines before and after each match
  next_errors: []                 # Railway Pattern chains (empty for now)
  metadata:
    severity: "critical"          # Custom metadata (you define these)
    category: "resource"
```

**YAML syntax quick reference:**
- **Indentation matters** (like Python) - use 2 spaces, not tabs
- **Colons** `:` separate keys and values
- **Dashes** `-` indicate list items
- **Quotes** `"..."` are required for strings with special characters

**Validate your catalog:**

```bash
# Go back to main directory
cd ..

# Validate the catalog
pixi run as-scan validate sample_logs/my_first_catalog.yaml
```

Or with pip:
```bash
as-scan validate sample_logs/my_first_catalog.yaml
```

**Expected output:**
```
✓ Catalog is valid
✓ Found 3 error definitions
✓ All error IDs are unique
✓ All patterns are valid
```

**If you see errors:**
- Check indentation (must be consistent)
- Check for missing colons or quotes
- Check that `id` matches the error key

---

## Step 4: Run Your First Scan (5 minutes)

Now we'll scan the sample log files for errors.

**Run the scan:**

```bash
# With pixi
pixi run as-scan scan \
  --catalog sample_logs/my_first_catalog.yaml \
  --output ./my_first_scan \
  --cores 4

# With pip
as-scan scan \
  --catalog sample_logs/my_first_catalog.yaml \
  --output ./my_first_scan \
  --cores 4
```

**What this command does:**
- `--catalog`: Specifies which catalog to use
- `--output`: Where to save results
- `--cores 4`: Use 4 CPU cores for parallel processing (faster)

**Expected output (Snakemake workflow):**
```
Building DAG of jobs...
Using shell: /bin/bash
Provided cores: 4
Rules claiming more threads will be scaled down.
Job stats:
job                   count
------------------  -------
discover_files            1
fingerprint_file          4
match_pattern            12
extract_context           3
aggregate_results         1
total                    21

[Mon Oct 20 15:05:01 2024]
rule discover_files:
    output: my_first_scan/.snakemake/discover_files.done
    jobid: 0

[Mon Oct 20 15:05:02 2024]
Finished job 0.

[Mon Oct 20 15:05:02 2024]
rule match_pattern:
    input: sample_logs/job_oom_error.log
    output: my_first_scan/matches/out_of_memory/...
    jobid: 3

[Mon Oct 20 15:05:03 2024]
Finished job 3.

...

[Mon Oct 20 15:05:10 2024]
rule aggregate_results:
    output: my_first_scan/report.json
    jobid: 20

[Mon Oct 20 15:05:11 2024]
Finished job 20.
21 of 21 steps (100%) done
```

**Check the output:**

```bash
ls -lh my_first_scan/
```

**Expected files:**
```
drwxr-xr-x  .snakemake/     (Snakemake internal files - ignore these)
drwxr-xr-x  matches/        (Raw match results)
drwxr-xr-x  context/        (Error context with surrounding lines)
-rw-r--r--  report.json     (Final report - this is what you want!)
```

---

## Step 5: View Results Interactively (5 minutes)

The scan created a `report.json` file with all the detected errors. Let's view it interactively with the TUI (Terminal User Interface).

**Launch the TUI:**

```bash
# With pixi
pixi run as-scan view my_first_scan/report.json

# With pip
as-scan view my_first_scan/report.json
```

**Expected TUI display:**

```
┌─ Error Scan Results ──────────────────────────────────────┐
│                                                            │
│ ▶ out_of_memory (1 match)                                │
│ ▶ timeout_error (1 match)                                │
│ ▶ python_traceback (1 match)                             │
│                                                            │
│ Total: 3 errors found across 4 files                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
Press ↑/↓ to navigate, Enter to expand, 'q' to quit
```

**Navigate the TUI:**
1. Press **↓** (down arrow) to select `out_of_memory`
2. Press **Enter** to expand it
3. You should see:

```
▼ out_of_memory (1 match)
  ▶ sample_logs/job_oom_error.log (1 match)
```

4. Press **↓** then **Enter** again to see details:

```
▼ out_of_memory (1 match)
  ▼ sample_logs/job_oom_error.log (1 match)
    ├─ Line 11: slurmstepd: error: Detected 1 oom-kill event(s)
    │
    │  Context (3 lines before and after):
    │
    │  [2024-10-20 11:01:15] Memory usage: 31.5 GB / 32 GB
    │  [2024-10-20 11:01:18] WARNING: Memory usage critical
    │  [2024-10-20 11:01:20] slurmstepd: error: Detected 1 oom-kill event(s) in StepId=12346
    │  [2024-10-20 11:01:21] Process killed by SLURM (OOM)
    │  [2024-10-20 11:01:22] Exit code: 137
    │
    │  Meaning: Job was killed because it ran out of memory
    │  Suggestion: Increase memory allocation in your job script (e.g., #SBATCH --mem=64GB)
```

5. Press **q** to quit the TUI

**Understanding the results:**
- The error was found at **Line 11** of `job_oom_error.log`
- The **context** shows what happened before (memory warnings) and after (process killed)
- The **meaning** and **suggestion** come from your catalog

---

## Step 6: Export Results to Markdown (3 minutes)

The TUI is great for interactive browsing, but sometimes you want a static report you can share.

**Export to Markdown:**

```bash
# With pixi
pixi run as-scan export \
  my_first_scan/report.json \
  --template markdown \
  --output my_scan_report.md

# With pip
as-scan export \
  my_first_scan/report.json \
  --template markdown \
  --output my_scan_report.md
```

**View the Markdown file:**

```bash
cat my_scan_report.md
```

Or open it in your text editor or Markdown viewer.

**What the report contains:**
- Summary statistics (total errors found)
- Errors grouped by type
- File locations and line numbers
- Full context for each error
- Meaning and suggestions

**You can also export to HTML:**

```bash
pixi run as-scan export \
  my_first_scan/report.json \
  --template html \
  --output my_scan_report.html
```

Then open `my_scan_report.html` in your web browser.

---

## Understanding What Happened

Let's review what autosubmit-scan did:

### 1. Discovery Phase
- Read `my_first_catalog.yaml`
- Found the pattern `files: ["*.log"]`
- Searched for all `.log` files in `sample_logs/`
- Discovered 4 log files

### 2. Fingerprinting Phase
- Created checksums of each log file
- These fingerprints enable caching (if you re-run the scan and files haven't changed, it skips re-scanning them)

### 3. Matching Phase
- For each error (out_of_memory, timeout_error, python_traceback)
- For each file (job_success.log, job_oom_error.log, etc.)
- Search for the pattern
- Record line numbers where matches were found

### 4. Context Extraction Phase
- For each match, read `context_lines` before and after
- Combine match + context into an ErrorMatch object

### 5. Railway Pattern Evaluation Phase
- Check if any `next_errors` should be triggered
- (In this example, `next_errors: []` is empty, so nothing happens here)

### 6. Aggregation Phase
- Combine all ErrorMatch objects into a single JSON-LD report
- Save to `report.json`

---

## Key Concepts Explained

### Literal vs Regex vs Callable Patterns

We used **literal patterns** in this tutorial:
```yaml
pattern:
  type: "literal"
  pattern: "oom-kill"  # Exact text match
```

**When to use each type:**

| Pattern Type | When to Use | Example |
|--------------|-------------|---------|
| **Literal** | You know the exact error text | `"oom-kill"`, `"Connection timeout"` |
| **Regex** | Error text varies slightly | `"ERROR\|CRITICAL\|FATAL"` (matches any of these) |
| **Callable** | Complex logic needed | Custom Python function to check if error occurred during business hours |

**For most cases, start with literal patterns.** They're simplest and fastest.

### Glob Patterns

We used `*.log` to match all `.log` files in the current directory.

**Common glob patterns:**
- `*.log` - All `.log` files in current directory
- `**/*.log` - All `.log` files in current directory AND all subdirectories (recursive)
- `job_*.log` - Files starting with `job_` and ending with `.log`

**Visual example:**
```
sample_logs/
├── job_success.log       ← Matched by *.log
├── job_oom_error.log     ← Matched by *.log
├── archive/
│   └── old_job.log       ← Matched by **/*.log but NOT *.log
```

### Context Lines

We set `context_lines: 3` for most errors:
```yaml
context_lines: 3  # Show 3 lines before and 3 lines after
```

**Why context matters:**
An error line alone isn't always enough. For the OOM error, the context showed:
- **Before:** Memory warnings (usage climbing to 31.5 GB)
- **Error:** `oom-kill event`
- **After:** Process killed, exit code 137

This helps you understand *why* the error occurred, not just *that* it occurred.

---

## Common First-Time Issues

### Issue 1: "No files matched pattern"

**Symptom:**
```
Warning: No files matched pattern *.log
```

**Causes:**
1. You're running the scan from the wrong directory
2. The file pattern is incorrect

**Solution:**
```bash
# Check current directory
pwd

# List log files
ls sample_logs/*.log

# Update catalog to use full path
files:
  - "sample_logs/*.log"  # Add directory prefix
```

### Issue 2: "No matches found for any error"

**Symptom:**
```
Total: 0 errors found
```

**Causes:**
1. The pattern text doesn't match what's in the logs
2. Case sensitivity (pattern is case-sensitive by default)

**Solution:**
```bash
# Check what's actually in the log file
cat sample_logs/job_oom_error.log | grep -i "oom"

# Update pattern to match exactly what you see
pattern: "oom-kill"  # Must match exact case and spelling
```

### Issue 3: "Command 'as-scan' not found"

**Symptom:**
```bash
as-scan: command not found
```

**Causes:**
1. Using pip installation but forgot to activate virtual environment
2. Installation didn't complete successfully

**Solution:**
```bash
# With pixi (always use prefix)
pixi run as-scan --help

# With pip, verify installation
pip list | grep autosubmit-scan

# If missing, reinstall
pip install -e .
```

---

## Next Steps: What to Learn

### Beginner Level (You Are Here)

You now know:
- ✓ How to install autosubmit-scan
- ✓ How to create simple catalogs
- ✓ How to run basic scans
- ✓ How to view results

### Intermediate Level

Learn next:
1. **Regex patterns** - Match variable error messages
   - Tutorial: [tutorials/02_pattern_types.md](tutorials/02_pattern_types.md)
   - Example: `pattern: "ERROR|CRITICAL"` matches either word

2. **Railway Pattern basics** - Chain related errors automatically
   - Tutorial: [tutorials/04_railway_pattern_intro.md](tutorials/04_railway_pattern_intro.md)
   - Example: Find OOM error → Always check for memory warnings

3. **Remote file scanning** - Scan logs on SSH servers
   - Tutorial: [tutorials/03_remote_files.md](tutorials/03_remote_files.md)
   - Important: Must configure SSH ControlMaster first!

### Advanced Level

After mastering intermediate topics:
1. **Complex Railway Patterns** - Conditional error chains
2. **Custom pattern matchers** - Write Python functions for complex matching
3. **Performance optimization** - Scan thousands of files efficiently
4. **Custom templates** - Create your own report formats

### Domain-Specific Guides

If you're working on climate modeling:
- [CLIMATE_MODELING_GUIDE.md](CLIMATE_MODELING_GUIDE.md) - HPC-specific examples
- SLURM error catalogs
- Autosubmit integration
- Large-scale scanning strategies

---

## Recommended Learning Path

```
1. Complete this Quick Start                    [✓ You are here]
   ↓
2. Read the Glossary (familiarize with terms)   [docs/GLOSSARY.md]
   ↓
3. Tutorial 01: Getting Started                 [tutorials/01_getting_started.md]
   ↓
4. Tutorial 02: Pattern Types                   [tutorials/02_pattern_types.md]
   ↓
5. Set up SSH for remote scanning              [docs/SSH_CONNECTION_POOLING.md]
   ↓
6. Tutorial 03: Remote Files                    [tutorials/03_remote_files.md]
   ↓
7. Tutorial 04: Railway Pattern Intro           [tutorials/04_railway_pattern_intro.md]
   ↓
8. Work through your own use case!
```

---

## Reference Documentation

- **[GLOSSARY.md](GLOSSARY.md)** - Definitions of all technical terms
- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user reference
- **[SSH_CONNECTION_POOLING.md](SSH_CONNECTION_POOLING.md)** - Required for remote scans
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - How the tool works (for developers)

---

## Getting Help

### Documentation
1. Check [GLOSSARY.md](GLOSSARY.md) for term definitions
2. Search [USER_GUIDE.md](USER_GUIDE.md) for detailed instructions
3. Read [tutorials/](tutorials/) for hands-on examples

### Common Errors
- See [COMMON_ERRORS.md](COMMON_ERRORS.md) for solutions to frequent problems (coming in Week 2)

### Community Support
- Open an issue on GitHub: [github.com/DestinE-Climate-DT/autosubmit-scan/issues](https://github.com/DestinE-Climate-DT/autosubmit-scan/issues)
- Email the development team (see AUTHORS.yaml)

---

## Summary

**What you learned:**
- Installation (pixi or pip)
- Creating sample log files
- Writing error catalogs (YAML syntax)
- Running scans with the CLI
- Viewing results interactively (TUI)
- Exporting reports (Markdown/HTML)

**What you created:**
- 4 sample log files with realistic errors
- Your first error catalog (3 error definitions)
- A complete scan report

**Time to first scan:** 30 minutes

**What's next:**
Choose your path:
- Pattern matching → [tutorials/02_pattern_types.md](tutorials/02_pattern_types.md)
- Remote scanning → [docs/SSH_CONNECTION_POOLING.md](SSH_CONNECTION_POOLING.md)
- Railway Pattern → [tutorials/04_railway_pattern_intro.md](tutorials/04_railway_pattern_intro.md)

---

**Last updated:** Week 1, Day 2 (Documentation Overhaul)

**Feedback:** If any step was confusing, please open an issue with the "documentation" label.
