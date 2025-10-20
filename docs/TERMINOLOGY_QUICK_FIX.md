# Terminology Quick Fix Guide

**Purpose:** Replace confusing terms/phrases with student-friendly versions

**Target Audience:** Graduate students with basic Python skills (numpy, matplotlib, pandas)

---

## High-Priority Replacements

### 1. Railway Pattern

**Current Problems:**
- "Railway pattern for conditional error chaining" (too abstract)
- "Conditional branching based on match context" (circular definition)
- "Chain of responsibility for error evaluation" (design pattern jargon)

**Replace With:**

**First Mention (README):**
```markdown
**Railway Pattern**: Automatic error flowcharts. When the tool finds one error,
it can automatically check for related errors based on conditions you define.

Example: Find "Out of Memory" → Automatically check which process failed
```

**Detailed Explanation (USER_GUIDE):**
```markdown
## What is the Railway Pattern?

Imagine troubleshooting a broken car:
1. Check if engine starts → If no, check battery
2. Check battery → If dead, check alternator
3. Check alternator → If broken, order replacement

The Railway Pattern works the same way for log errors:
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
```

**Analogy Library:**
- Medical diagnosis flowchart (symptom → test → diagnosis)
- Troubleshooting guide ("If error A, check B")
- Choose-your-own-adventure book (conditional branching)
- Decision tree (if/then logic)

---

### 2. Catalog

**Current Problems:**
- Used before definition
- Assumed to be self-explanatory
- Confused with "error catalog" vs "catalog YAML"

**Replace With:**

**First Mention:**
```markdown
**Catalog**: A configuration file (YAML format) that tells the tool:
- What errors to look for (patterns)
- Where to find log files (file paths)
- How errors relate to each other (railway pattern)

Think of it as a recipe for error scanning.
```

**Consistent Usage:**
- Use "error catalog" consistently
- Don't alternate with "catalog YAML" or "catalog file"
- Always include format: "error catalog (YAML file)"

---

### 3. Pattern Matching

**Current Problems:**
- Sounds like basic text search (grep)
- Doesn't convey three different types
- No guidance on when to use which

**Replace With:**

**First Mention:**
```markdown
**Pattern Matching**: How the tool searches for errors in your log files.

Three types:
- **Literal**: Exact text match (e.g., find "Error 404")
- **Regex**: Flexible pattern (e.g., find "Error" followed by any number)
- **Callable**: Custom Python function for complex logic

Most users start with literal patterns and only use regex/callable when needed.
```

**Decision Tree:**
```markdown
## Choosing a Pattern Type

Use **Literal** when:
- You know the exact error text
- Error message doesn't vary
- Example: "OOM killed"

Use **Regex** when:
- Error text varies slightly
- You want to match multiple similar errors
- Example: "Error 404" or "Error 500" → "Error \\d{3}"

Use **Callable** when:
- Error detection needs custom logic
- You're comfortable writing Python functions
- Example: Check if error occurred during business hours
```

---

### 4. Snakemake

**Current Problems:**
- Mentioned frequently without explanation
- Sounds like something users need to learn
- Creates unnecessary intimidation

**Replace With:**

**First Mention:**
```markdown
**Snakemake**: A workflow management tool that runs behind the scenes.
You don't need to learn Snakemake to use autosubmit-scan.

What it does:
- Runs scans in parallel (faster scanning)
- Caches results (doesn't re-scan unchanged files)
- Handles failures gracefully

You interact with autosubmit-scan through the `as-scan` command, not Snakemake directly.
```

**Throughout Docs:**
- Minimize mentions of Snakemake
- When mentioned, always add "(works behind the scenes)"
- Don't explain Snakemake internals unless in developer docs

---

### 5. fsspec / Filesystem Abstraction

**Current Problems:**
- Technical library name used without context
- Sounds like something users need to install/configure
- Creates confusion about remote file access

**Replace With:**

**First Mention:**
```markdown
**Remote File Access**: The tool can scan files on different systems:
- Local files: `/path/to/file.log`
- SSH/SFTP: `ssh://server/path/to/file.log`
- Amazon S3: `s3://bucket/path/to/file.log`

The tool uses a library called fsspec behind the scenes to make this work.
You don't need to configure fsspec directly.
```

**Throughout Docs:**
- Replace "fsspec" with "remote file access"
- When mentioning fsspec, add "(file access library)"
- Focus on what users can DO, not how it's implemented

---

### 6. JSON-LD

**Current Problems:**
- Technical format name without explanation
- Unclear why not just "JSON"
- Makes simple reports sound complicated

**Replace With:**

**First Mention:**
```markdown
**Report Format**: Scan results are saved as JSON-LD, a structured format that's
both human-readable and machine-parseable.

You can:
- View results interactively: `as-scan view report.json`
- Export to Markdown: `as-scan export report.json --template markdown`
- Export to HTML: `as-scan export report.json --template html`

You don't need to understand JSON-LD format to use the results.
```

**Throughout Docs:**
- Replace "JSON-LD report" with "scan report"
- Only mention JSON-LD when discussing export formats
- Emphasize that users can export to familiar formats (Markdown, HTML)

---

### 7. TUI (Terminal User Interface)

**Current Problems:**
- Acronym without expansion
- Sounds technical
- Unclear what it looks like

**Replace With:**

**First Mention:**
```markdown
**Interactive Results Viewer**: After scanning, view results in an interactive
terminal interface (like a simple GUI in your terminal).

Navigate with arrow keys:
- Up/Down: Browse errors
- Enter: See details
- Q: Quit

[Screenshot of TUI]

Launch with: `as-scan view results/report.json`
```

**Throughout Docs:**
- Replace "TUI" with "interactive results viewer" or "results browser"
- Always include screenshot or description
- Explain keyboard controls

---

### 8. Context Lines

**Current Problems:**
- Technical term without purpose explanation
- Unclear why you'd want them
- No guidance on how many to use

**Replace With:**

**First Mention:**
```markdown
**Context Lines**: Lines before and after each error to help you understand what
happened.

Example with `context_lines: 2`:
```
2024-01-15 10:23:45 Starting process
2024-01-15 10:24:12 Loading data      ← 2 lines before
ERROR: Out of memory                   ← The error
2024-01-15 10:25:34 Process terminated ← 2 lines after
2024-01-15 10:25:35 Cleanup complete
```

**How many to use:**
- 0: Just the error line (fastest)
- 2-5: Immediate context (good for most cases)
- 10-20: Full context (for complex errors)
```

---

### 9. SSH ControlMaster / Connection Pooling

**Current Problems:**
- Very technical terminology
- Sounds optional but is critical
- Explanation focuses on HOW not WHY

**Replace With:**

**First Mention:**
```markdown
## Required Setup for Remote Scans

⚠️ **Important**: If scanning files over SSH, you MUST configure SSH connection
reuse. Without this, scans will fail after 2 minutes.

**Symptom without setup:**
```
[ERROR] SSH connection timeout after 120 seconds
```

**Fix (one-time setup):**

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
```

**Throughout Docs:**
- Replace "SSH ControlMaster" with "SSH connection reuse"
- Replace "connection pooling" with "connection sharing"
- Always explain the user-visible benefit first

---

### 10. Glob Patterns

**Current Problems:**
- Assumed knowledge of * and **
- Recursive matching not explained
- No examples showing what gets matched

**Replace With:**

**First Mention:**
```markdown
**File Patterns (Glob Syntax)**: Wildcards to match multiple files.

**Common patterns:**
- `*.log` - All .log files in current directory
  - Matches: `run.log`, `error.log`
  - Doesn't match: `data/run.log` (in subdirectory)

- `**/*.log` - All .log files in all subdirectories (recursive)
  - Matches: `run.log`, `data/run.log`, `data/2024/run.log`
  - Matches ANY depth

- `run*.log` - Files starting with "run" and ending with ".log"
  - Matches: `run1.log`, `run_final.log`
  - Doesn't match: `test.log`

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
```

---

## General Writing Guidelines

### Replace Developer Language with Student Language

| Instead of... | Use... |
|---------------|--------|
| "Implements chain of responsibility pattern" | "Automatically checks related errors" |
| "Pydantic models validate schema" | "The tool checks your catalog for errors" |
| "Polymorphic pattern matchers" | "Three types of pattern matching" |
| "Checkpoint-based workflow" | "Smart caching (doesn't re-scan unchanged files)" |
| "File fingerprinting" | "Tracking which files changed" |
| "Domain models" | "Data structures" or skip entirely |
| "Orchestration layer" | "Workflow management" or skip entirely |
| "Strategy pattern" | Skip entirely (implementation detail) |
| "Repository pattern" | Skip entirely (implementation detail) |

### Replace Technical Explanations with Purpose-First

**Instead of:**
> "The scan execution uses checkpoint-based workflow in src/orchestration/Snakefile"

**Use:**
> "The scan is smart: it only re-scans files that changed since last time, making repeat scans much faster"

---

**Instead of:**
> "Pattern matching uses polymorphic matchers: LiteralPatternMatcher, RegexPatternMatcher, CallablePatternMatcher"

**Use:**
> "Three ways to find errors: exact text match, flexible patterns (regex), or custom logic (Python function)"

---

**Instead of:**
> "ErrorMatch objects contain context_before, context_after, and matched_text fields"

**Use:**
> "When an error is found, the tool saves the error line plus surrounding context to help you understand what happened"

---

### Use Concrete Examples Before Abstract Concepts

**Bad Order:**
1. Explain railway pattern theory
2. Show complex railway pattern YAML
3. Mention use cases

**Good Order:**
1. Show problem: "Searching for related errors manually is tedious"
2. Show solution: "Tool can automatically check for related errors"
3. Show simple example: "Find error A → always check for error B"
4. Explain concept: "This is called the Railway Pattern"
5. Show complex example: "Check error B only if severity is high"

---

### Add Analogies for Complex Concepts

| Concept | Analogy |
|---------|---------|
| Railway Pattern | Medical diagnosis flowchart |
| Pattern Matching | Find/Replace in Word but with rules |
| Context Lines | Showing paragraphs around search results |
| SSH Connection Reuse | Carpooling vs everyone driving separately |
| Snakemake Caching | Only reheating food that got cold, not fresh food |
| Glob Patterns | Searching computer with wildcards |

---

### Front-Load the "Why"

**Before explaining HOW:**
1. What problem does this solve?
2. When would I use this?
3. What happens if I don't use this?

**Then explain HOW:**
4. Here's how to use it
5. Here's an example
6. Here's how to tell if it's working

---

## Quick Reference: Jargon Checklist

When writing documentation, check for these terms and replace/explain:

**High Confusion:**
- [ ] Railway Pattern → Explain with analogy
- [ ] Catalog → Define before using
- [ ] Snakemake → "Works behind the scenes"
- [ ] fsspec → "Remote file access"
- [ ] JSON-LD → "Scan report"
- [ ] TUI → "Interactive results viewer"
- [ ] SSH ControlMaster → "SSH connection reuse"
- [ ] Glob patterns → Show examples

**Medium Confusion:**
- [ ] Context lines → Explain purpose
- [ ] Pattern matching → List three types
- [ ] Condition → "When to check next error"
- [ ] Callable → "Custom Python function"
- [ ] URI → "File path (can be remote)"
- [ ] Workflow → "How the scan runs"

**Low Confusion (OK to use with brief explanation):**
- [ ] YAML (config file format)
- [ ] Regex (flexible pattern matching)
- [ ] SSH (secure remote access)
- [ ] Log file (program output file)

**Never Use (Developer Terms):**
- [ ] Polymorphic
- [ ] Strategy pattern
- [ ] Repository pattern
- [ ] Domain model
- [ ] Orchestration layer
- [ ] Dependency injection
- [ ] Checkpoint-based workflow (say "smart caching")

---

## Testing Your Writing

### Readability Test

Paste text into: https://hemingwayapp.com/

**Target:** Grade 12 or lower (high school senior)
**Maximum:** Grade 14 (college sophomore)
**Current:** Grade 16-18 (graduate level)

### Jargon Density Test

**Rule:** Maximum 2 technical terms per sentence

**Example - Too Dense:**
> "The Snakemake workflow uses checkpoint-based execution to orchestrate parallel pattern matching with the railway pattern evaluator."

**Jargon count:** 6 terms in one sentence (Snakemake, workflow, checkpoint-based, orchestrate, parallel, pattern matching, railway pattern)

**Better:**
> "The tool scans files in parallel for faster results. If you're using the railway pattern (automatic error chaining), it checks related errors based on your conditions."

**Jargon count:** 2 terms, both explained (railway pattern, parallel)

---

## Implementation Checklist

For each documentation file:

- [ ] Replace "Railway Pattern" with analogy-first explanation
- [ ] Define "catalog" before first use
- [ ] Replace developer terminology with purpose-focused language
- [ ] Add examples before abstract concepts
- [ ] Include "Why" before "How"
- [ ] Add visual aids for complex concepts
- [ ] Test readability (target grade 12)
- [ ] Check jargon density (max 2 per sentence)
- [ ] Link to glossary for all technical terms
- [ ] Add "Prerequisites" section listing required knowledge

---

**For Documentation Team:**

Use this as a find-and-replace guide when revising docs.

Priority order:
1. Railway Pattern explanation (appears everywhere)
2. SSH connection setup (critical for remote scans)
3. Catalog definition (needed for quick start)
4. Pattern matching types (core functionality)
5. Everything else

**Testing:**
Give revised section to someone unfamiliar with the tool.
If they ask "what does X mean?", that term needs better explanation.
