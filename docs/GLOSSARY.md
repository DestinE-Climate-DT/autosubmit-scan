# Glossary

This glossary defines technical terms used in autosubmit-scan documentation. Terms are explained for users with basic Python skills (numpy, matplotlib, pandas).

---

## A

### Analogy

**Simple Definition:** A comparison that explains something complex by comparing it to something familiar.

**In autosubmit-scan:** We use analogies to explain technical concepts. For example, the [Railway Pattern](#railway-pattern) is like a medical diagnosis flowchart.

**Example:**
- Railway Pattern = Medical diagnosis flowchart (symptom → test → diagnosis)

---

## C

### Callable Pattern

**Simple Definition:** A custom Python function you write to detect errors with complex logic.

**When to use:** When [literal patterns](#literal-pattern) and [regex patterns](#regex-pattern) aren't flexible enough.

**Example:**
```yaml
pattern:
  type: "callable"
  pattern: "my_module:check_business_hours"
```

This runs a Python function that checks if an error occurred during business hours.

**See also:** [Pattern Matching](#pattern-matching), [Literal Pattern](#literal-pattern), [Regex Pattern](#regex-pattern)

---

### Catalog

**Simple Definition:** A configuration file (YAML format) that tells the tool what errors to look for, where to find log files, and how errors relate to each other.

**Think of it as:** A recipe for error scanning.

**File format:** YAML (`.yaml` or `.yml`)

**Contains:**
- What errors to look for ([patterns](#pattern-matching))
- Where to find log files (file paths with [glob patterns](#glob-patterns))
- How errors relate to each other ([railway pattern](#railway-pattern))

**Example:**
```yaml
errors:
  - id: "out_of_memory"
    pattern:
      type: "literal"
      pattern: "OOM killed"
    file_locations:
      - "logs/**/*.log"
```

**Consistent naming:** Always use "error catalog" or "catalog" consistently. Don't alternate between "catalog YAML" or "catalog file."

**See also:** [Pattern Matching](#pattern-matching), [Railway Pattern](#railway-pattern), [Glob Patterns](#glob-patterns)

---

### Condition

**Simple Definition:** A rule that determines when to check for the next error in a [railway pattern](#railway-pattern) chain.

**In plain English:** "When to check the next error"

**Example:**
```yaml
next_errors:
  - error_id: "memory_leak"
    when:
      type: "field_equals"
      field: "severity"
      value: "critical"
```

This means: "Check for memory_leak error only if the current error has severity = critical"

**Condition types:**
- `always` - Always check the next error
- `field_equals` - Check if a field equals a specific value
- `field_contains` - Check if a field contains specific text
- `field_regex` - Check if a field matches a pattern
- `and` / `or` - Combine multiple conditions
- `custom` - Use a custom Python function

**See also:** [Railway Pattern](#railway-pattern)

---

### Context Lines

**Simple Definition:** Lines before and after each error to help you understand what happened.

**Analogy:** Like showing paragraphs around search results in a document.

**Example with `context_lines: 2`:**
```
2024-01-15 10:23:45 Starting process
2024-01-15 10:24:12 Loading data      ← 2 lines before
ERROR: Out of memory                   ← The error
2024-01-15 10:25:34 Process terminated ← 2 lines after
2024-01-15 10:25:35 Cleanup complete
```

**How many to use:**
- `0` - Just the error line (fastest)
- `2-5` - Immediate context (good for most cases)
- `10-20` - Full context (for complex errors)

**Configuration:**
```yaml
errors:
  - id: "my_error"
    pattern: ...
    context_lines: 5  # Show 5 lines before and after
```

---

## F

### fsspec

**Simple Definition:** A Python library that lets autosubmit-scan access files on different systems (local, SSH, S3, etc.) using the same code.

**You don't need to know:** How fsspec works internally. The tool handles it automatically.

**What it enables:**
- Local files: `/path/to/file.log`
- SSH/SFTP: `ssh://server/path/to/file.log`
- Amazon S3: `s3://bucket/path/to/file.log`
- FTP: `ftp://server/path/to/file.log`

**See also:** [Remote File Access](#remote-file-access), [URI](#uri)

---

## G

### Glob Patterns

**Simple Definition:** Wildcards to match multiple files at once.

**Common patterns:**

| Pattern | What it matches | Examples |
|---------|----------------|----------|
| `*.log` | All .log files in current directory | `run.log`, `error.log` |
| `**/*.log` | All .log files in all subdirectories (recursive) | `run.log`, `data/run.log`, `data/2024/run.log` |
| `run*.log` | Files starting with "run" and ending with ".log" | `run1.log`, `run_final.log` |
| `data/*/run.log` | run.log one level deep in data/ | `data/exp1/run.log`, `data/exp2/run.log` |

**Visual example:**
```
project/
  ├── run.log           ← Matched by *.log and **/*.log
  ├── data/
  │   └── run.log       ← Matched by **/*.log only
  └── archive/
      └── 2024/
          └── run.log   ← Matched by **/*.log only
```

**Key difference:**
- `*` - Match in current directory only
- `**` - Match in all subdirectories (recursive)

**See also:** [Catalog](#catalog)

---

## I

### Interactive Results Viewer

**Simple Definition:** A terminal-based interface for browsing scan results with keyboard navigation (like a simple GUI in your terminal).

**Also called:** TUI (Terminal User Interface), results browser

**Navigation:**
- Up/Down: Browse errors
- Enter: See details
- Q: Quit

**Launch:**
```bash
as-scan view results/report.json
```

**Features:**
- Browse all detected errors
- See full context for each error
- Filter by error type
- Jump to file locations

**See also:** [Scan Report](#scan-report)

---

## J

### JSON-LD

**Simple Definition:** A structured data format that's both human-readable and machine-parseable. Scan results are saved in this format.

**You don't need to know:** JSON-LD format details. You can export results to familiar formats.

**What you can do:**
- View results interactively: `as-scan view report.json`
- Export to Markdown: `as-scan export report.json --template markdown`
- Export to HTML: `as-scan export report.json --template html`

**Why JSON-LD:** It adds semantic meaning to data, making it easier for other tools to understand and process results.

**See also:** [Scan Report](#scan-report), [Interactive Results Viewer](#interactive-results-viewer)

---

## L

### Literal Pattern

**Simple Definition:** Exact text matching. The tool searches for the exact text you specify.

**When to use:** When you know the exact error message and it doesn't vary.

**Example:**
```yaml
pattern:
  type: "literal"
  pattern: "OOM killed"
```

This finds only lines containing exactly "OOM killed" (case-sensitive).

**Choosing a pattern type:**
- Use **Literal** when: You know the exact error text and it doesn't vary
- Use **[Regex](#regex-pattern)** when: Error text varies slightly
- Use **[Callable](#callable-pattern)** when: You need custom logic

**See also:** [Pattern Matching](#pattern-matching), [Regex Pattern](#regex-pattern), [Callable Pattern](#callable-pattern)

---

### Log File

**Simple Definition:** A text file containing output from a program (messages, errors, warnings, debugging info).

**Common names:** `run.log`, `error.log`, `output.log`, `debug.log`

**Example content:**
```
2024-01-15 10:23:45 INFO Starting process
2024-01-15 10:24:12 DEBUG Loading data
2024-01-15 10:24:58 ERROR Out of memory
2024-01-15 10:25:34 INFO Process terminated
```

**autosubmit-scan purpose:** Scan log files to find and analyze errors automatically.

---

## P

### Pattern Matching

**Simple Definition:** How the tool searches for errors in your log files.

**Three types:**

1. **[Literal](#literal-pattern)** - Exact text match
   - Example: Find "Error 404"
   - When to use: You know the exact error text

2. **[Regex](#regex-pattern)** - Flexible pattern
   - Example: Find "Error" followed by any number
   - When to use: Error text varies slightly

3. **[Callable](#callable-pattern)** - Custom Python function
   - Example: Check if error occurred during business hours
   - When to use: Complex logic needed

**Most users start with literal patterns** and only use regex/callable when needed.

**Decision tree:**

```
Do you know the exact error text?
├─ Yes → Use Literal pattern
└─ No
   ├─ Can you describe it with a pattern? → Use Regex
   └─ Need complex logic? → Use Callable
```

**See also:** [Literal Pattern](#literal-pattern), [Regex Pattern](#regex-pattern), [Callable Pattern](#callable-pattern)

---

## R

### Railway Pattern

**Simple Definition:** Automatic error flowcharts. When the tool finds one error, it can automatically check for related errors based on conditions you define.

**Analogy:** Like a medical diagnosis flowchart:
1. Check symptom → If fever, measure temperature
2. Check temperature → If > 102°F, check for infection
3. Check infection → If bacterial, prescribe antibiotics

**Troubleshooting example:**
1. Find "Python Error" → Check if it's a memory error
2. If memory error → Check if it happened during large computation
3. If large computation → Suggest increasing memory allocation

**Without Railway Pattern:**
- You find each error separately
- You manually search for related errors
- Easy to miss error chains

**With Railway Pattern:**
- Tool automatically follows your flowchart
- Related errors found in one scan
- Saves hours of manual log searching

**Example configuration:**
```yaml
errors:
  - id: "out_of_memory"
    pattern:
      type: "literal"
      pattern: "OOM killed"
    next_errors:
      - error_id: "process_failure"
        when:
          type: "always"
```

**Other analogies:**
- Troubleshooting guide ("If error A, check B")
- Choose-your-own-adventure book (conditional branching)
- Decision tree (if/then logic)

**See also:** [Condition](#condition), [Catalog](#catalog)

---

### Regex

**Simple Definition:** A flexible pattern language for matching text. Short for "Regular Expression."

**When to use:** When error text varies and literal matching isn't flexible enough.

**Example:**
```yaml
pattern:
  type: "regex"
  pattern: "ERROR|CRITICAL|FATAL"
  flags: ["IGNORECASE"]
```

This matches any line containing "ERROR", "CRITICAL", or "FATAL" (case-insensitive).

**Common regex patterns:**

| Pattern | Matches | Example |
|---------|---------|---------|
| `Error \d+` | "Error" + any number | `Error 404`, `Error 500` |
| `ERROR\|CRITICAL` | "ERROR" or "CRITICAL" | `ERROR: timeout`, `CRITICAL: crash` |
| `.*memory.*` | Any text containing "memory" | `Out of memory`, `Memory leak detected` |

**Learning resources:**
- [regex101.com](https://regex101.com) - Test patterns online
- [regexr.com](https://regexr.com) - Interactive regex tutorial

**See also:** [Pattern Matching](#pattern-matching), [Regex Pattern](#regex-pattern)

---

### Regex Pattern

**Simple Definition:** A pattern matching type that uses [regex](#regex) for flexible text matching.

**When to use:** When error text varies slightly and you want to match multiple similar errors.

**Example:**
```yaml
pattern:
  type: "regex"
  pattern: "Error \\d{3}"  # Match "Error" + 3 digits
  flags: ["IGNORECASE"]
```

This matches: `Error 404`, `Error 500`, `ERROR 403`

**Flags:**
- `IGNORECASE` - Case-insensitive matching
- `MULTILINE` - `^` and `$` match line boundaries
- `DOTALL` - `.` matches newlines too

**See also:** [Pattern Matching](#pattern-matching), [Literal Pattern](#literal-pattern), [Callable Pattern](#callable-pattern), [Regex](#regex)

---

### Remote File Access

**Simple Definition:** The ability to scan log files on different systems (not just your local computer).

**Supported systems:**
- Local files: `/path/to/file.log`
- SSH/SFTP: `ssh://user@server/path/to/file.log`
- Amazon S3: `s3://bucket/path/to/file.log`
- FTP: `ftp://user@server/path/to/file.log`

**How it works:** The tool uses a library called [fsspec](#fsspec) behind the scenes. You don't need to configure fsspec directly.

**Important:** For SSH access, you must configure [SSH connection reuse](#ssh-connection-reuse) to prevent timeouts.

**Example catalog:**
```yaml
errors:
  - id: "remote_error"
    file_locations:
      - "ssh://server/var/log/**/*.log"
```

**Credentials:** Use environment variables, not embedded in catalogs. See [SSH Connection Reuse](#ssh-connection-reuse).

**See also:** [fsspec](#fsspec), [URI](#uri), [SSH Connection Reuse](#ssh-connection-reuse)

---

## S

### Scan Report

**Simple Definition:** The output from running `as-scan scan`. Contains all detected errors with context.

**Format:** JSON-LD (but you don't need to understand JSON-LD)

**Viewing options:**
```bash
# Interactive viewer
as-scan view results/report.json

# Export to Markdown
as-scan export results/report.json --template markdown --output report.md

# Export to HTML
as-scan export results/report.json --template html --output report.html
```

**Report contents:**
- All detected errors
- File locations
- Line numbers
- [Context lines](#context-lines)
- Error chains ([Railway Pattern](#railway-pattern) results)
- Timestamps
- File fingerprints

**See also:** [JSON-LD](#json-ld), [Interactive Results Viewer](#interactive-results-viewer)

---

### Snakemake

**Simple Definition:** A workflow management tool that runs behind the scenes. You don't need to learn Snakemake to use autosubmit-scan.

**What it does:**
- Runs scans in parallel (faster scanning)
- Caches results (doesn't re-scan unchanged files)
- Handles failures gracefully

**You interact with:** The `as-scan` command, not Snakemake directly.

**Smart caching example:**
```
First scan:  Scans 1000 files → Takes 5 minutes
Second scan: Only 10 files changed → Takes 10 seconds
```

**Analogy:** Like only reheating food that got cold, not fresh food.

**You don't need to know:** Snakemake syntax, rules, or workflow details.

**See also:** [Workflow Management](#workflow-management)

---

### SSH Connection Reuse

**Simple Definition:** Sharing SSH connections instead of creating new ones for each file access.

**Also called:** SSH ControlMaster, connection pooling, connection sharing

**Why it's critical:** Without this, remote scans will fail after 2 minutes.

**Symptom without setup:**
```
[ERROR] SSH connection timeout after 120 seconds
```

**One-time setup:**

Add these lines to `~/.ssh/config`:
```ssh-config
Host *
    ControlMaster auto
    ControlPath ~/.ssh/control-%C
    ControlPersist 10m
```

**What this does:**
- Reuses SSH connections instead of creating new ones
- Makes scans 10-40x faster
- Prevents timeout errors

**Verify it works:**
```bash
as-scan check-ssh your-server
```

**Analogy:** Carpooling vs everyone driving separately. Connection reuse is like carpooling - more efficient and faster.

**See also:** [Remote File Access](#remote-file-access)

---

## T

### TUI

**Simple Definition:** Terminal User Interface. An interactive interface in your terminal (like a simple GUI but text-based).

**In autosubmit-scan:** See [Interactive Results Viewer](#interactive-results-viewer)

---

## U

### URI

**Simple Definition:** A file path that can point to local or remote files.

**Also called:** File path, fsspec URI

**Examples:**
- Local: `/home/user/logs/run.log`
- SSH: `ssh://server/var/log/run.log`
- S3: `s3://my-bucket/logs/run.log`
- FTP: `ftp://server/logs/run.log`

**In plain English:** "File path (can be remote)"

**See also:** [Remote File Access](#remote-file-access), [fsspec](#fsspec)

---

## W

### Workflow Management

**Simple Definition:** How the tool coordinates and runs the scan steps efficiently.

**What it handles:**
- Running file scans in parallel (faster)
- Tracking which files changed (smart caching)
- Following error chains ([Railway Pattern](#railway-pattern))
- Combining results

**Implementation:** Uses [Snakemake](#snakemake) behind the scenes

**You interact with:** The `as-scan scan` command

**Smart features:**
- Only re-scans files that changed
- Runs multiple scans in parallel
- Handles errors without crashing
- Caches intermediate results

**See also:** [Snakemake](#snakemake)

---

## Y

### YAML

**Simple Definition:** A human-readable configuration file format. Used for error catalogs.

**File extension:** `.yaml` or `.yml`

**Example:**
```yaml
errors:
  - id: "my_error"
    pattern:
      type: "literal"
      pattern: "ERROR"
    file_locations:
      - "logs/**/*.log"
```

**Key features:**
- Indentation matters (like Python)
- Uses colons for key-value pairs
- Uses dashes for lists
- Human-readable and writable

**Learning resources:**
- [yaml.org](https://yaml.org) - Official documentation
- [Learn YAML in Y minutes](https://learnxinyminutes.com/docs/yaml/) - Quick tutorial

**See also:** [Catalog](#catalog)

---

## Additional Resources

### Related Documentation

- [USER_GUIDE.md](USER_GUIDE.md) - Complete user guide
- [getting-started/quickstart.md](getting-started/quickstart.md) - Quick start tutorial
- [getting-started/concepts.md](getting-started/concepts.md) - Core concepts explained
- [explanation/railway-pattern.md](explanation/railway-pattern.md) - Railway Pattern deep dive
- [SSH_CONNECTION_POOLING.md](SSH_CONNECTION_POOLING.md) - SSH setup guide

### Writing Conventions

When reading documentation, technical terms are linked to this glossary on first mention like this: [Railway Pattern](#railway-pattern)

### Feedback

If any term needs better explanation, please open an issue or contact the documentation team.
