# Documentation Team Action Plan

**Purpose:** Prioritized, actionable tasks to make documentation accessible to graduate students

**Context:** Student review identified 47 critical issues. This plan focuses on the 15 highest-impact fixes.

**Timeline:** 4 weeks (can be parallelized across 4-agent team)

---

## Week 1: Stop-Gap Fixes (Unblock Students)

**Goal:** Students can complete first scan successfully

### Day 1-2: GLOSSARY.md (Documentation Specialist)

**Priority:** CRITICAL - Referenced by all other fixes

**Task:** Create comprehensive glossary with plain-English definitions

**Contents:**
- Railway Pattern (with medical diagnosis analogy)
- Catalog (configuration file that tells tool what to scan)
- Pattern Matching (literal, regex, callable with decision tree)
- Snakemake (works behind the scenes)
- fsspec (remote file access)
- JSON-LD (scan report format)
- TUI (interactive results viewer)
- SSH ControlMaster (connection reuse)
- Glob patterns (with visual examples)
- Context lines (purpose + examples)

**Deliverables:**
- [ ] `docs/GLOSSARY.md` created
- [ ] Each term has: definition, analogy (if complex), example, visual aid
- [ ] Linked from all documentation (header note)
- [ ] Reviewed by student reviewer for clarity

**Acceptance Criteria:**
- Student with no prior knowledge can understand each term
- No circular definitions ("X is a type of X")
- Each term includes "Why do I need this?"

---

### Day 2-3: QUICK_START_FOR_STUDENTS.md (Teacher + Python Expert)

**Priority:** CRITICAL - First experience for new users

**Task:** Create working tutorial with sample data

**Contents:**
1. Installation (pixi recommended, pip alternative)
2. Download sample log file (curl command)
3. Create first catalog (literal pattern, local file)
4. Run scan
5. View results (with screenshots)
6. What to do next (links to intermediate tutorials)

**Requirements:**
- Complete working example (copy-paste-run)
- Cross-platform paths (Mac/Linux/Windows)
- Expected output shown for each command
- Troubleshooting section for first-time issues
- No assumed knowledge (YAML syntax explained)

**Deliverables:**
- [ ] `docs/QUICK_START_FOR_STUDENTS.md` created
- [ ] `examples/quick_start/sample_log.txt` created
- [ ] `examples/quick_start/first_catalog.yaml` created
- [ ] Screenshots of TUI results
- [ ] Tested on Mac/Linux/Windows

**Acceptance Criteria:**
- Student completes first scan in 30 minutes
- No external research required
- Sample data works as described
- Error messages (if any) are explained

---

### Day 3-4: Railway Pattern Rewrite (Documentation Specialist + Teacher)

**Priority:** CRITICAL - Core feature, mentioned 47 times, never explained well

**Task:** Rewrite Railway Pattern explanation in all documents

**Target Documents:**
- README.md (lines 7, 31-40, 262-277)
- USER_GUIDE.md (lines 228-296)
- ARCHITECTURE.md (lines 84, 112-125)
- CLAUDE.md (lines 7, 84)

**New Structure:**
1. **Problem:** "Manually searching for related errors is tedious"
2. **Solution:** "Railway Pattern = automatic error flowchart"
3. **Analogy:** Medical diagnosis or troubleshooting guide
4. **Simple Example:** "Find A → always check B"
5. **Visual Diagram:** Flowchart showing chain
6. **Complex Example:** "Find A → check B if severity is high"
7. **When to Use:** Decision guide

**Deliverables:**
- [ ] Railway Pattern explanation added to GLOSSARY.md
- [ ] All mentions in README.md link to glossary
- [ ] USER_GUIDE.md section rewritten with analogy-first approach
- [ ] Visual flowchart created (ASCII or image)
- [ ] "When to Use Railway Pattern" decision tree added

**Acceptance Criteria:**
- Student can explain Railway Pattern in own words after reading
- Student can decide when to use it
- Student can create simple railway pattern (always condition)

---

### Day 4-5: SSH Connection Setup Promotion (Documentation Specialist)

**Priority:** CRITICAL - Students hit timeout errors without this

**Task:** Move SSH setup from "Best Practices" to "Installation"

**Changes Required:**
- **README.md:** Add "⚠️ Important for Remote Scans" section after installation
- **USER_GUIDE.md:** Move SSH Connection Pooling section to top, make it big/bold
- **SSH_CONNECTION_POOLING.md:** Rewrite intro to show user-visible problem first

**New Structure:**
1. **Symptom:** "Scan fails after 2 minutes with timeout error"
2. **Cause:** "SSH creates too many connections"
3. **Fix:** "Add these 3 lines to ~/.ssh/config"
4. **Test:** "`as-scan check-ssh hostname`"
5. **Details:** Link to full SSH_CONNECTION_POOLING.md

**Deliverables:**
- [ ] README.md updated with SSH setup warning
- [ ] USER_GUIDE.md Section 9 moved to Section 1 (after installation)
- [ ] SSH_CONNECTION_POOLING.md rewritten with symptom-first approach
- [ ] "Required vs Optional" marker added (REQUIRED for remote scans)
- [ ] Platform-specific notes added (Mac/Linux tested, Windows WSL)

**Acceptance Criteria:**
- Students can't miss this setup step
- Students know WHY it's needed (timeout prevention)
- Students can verify it's working (check-ssh command)

---

### Day 5: Fix First Example (Python Expert)

**Priority:** HIGH - First example must work

**Task:** Replace /var/log examples with working cross-platform example

**Current Problem:**
- README.md lines 335-370 use `/var/log/**/*.log`
- Doesn't exist on Mac/Windows
- No sample data provided

**New Approach:**
```markdown
## Your First Scan

Download sample data:
```bash
curl -O https://raw.githubusercontent.com/DestinE-Climate-DT/autosubmit-scan/main/examples/sample_logs.tar.gz
tar -xzf sample_logs.tar.gz
cd sample_logs/
```

Contents:
```
sample_logs/
  ├── model_run1.log
  ├── model_run2.log
  └── slurm_output.err
```

Create catalog:
[Complete working example]

Run scan:
```bash
as-scan scan --catalog my_catalog.yaml --output results
```

Expected output:
[Show actual output]
```

**Deliverables:**
- [ ] Create `examples/sample_logs/` with realistic log files
- [ ] Update README.md example to use sample_logs/
- [ ] Show expected output (text + screenshot)
- [ ] Add to GitHub releases for easy download
- [ ] Test on Mac/Linux/Windows

**Acceptance Criteria:**
- Example runs without modification
- Sample logs contain realistic errors (OOM, timeouts, Python tracebacks)
- Works on all platforms

---

## Week 2: Tutorial Content (Enable Self-Learning)

**Goal:** Students can learn progressively without external help

### Day 6-8: Jupyter Notebooks 1-3 (Python Expert + Teacher)

**Priority:** HIGH - Hands-on learning critical

**Notebooks to Create:**

#### 1. `tutorials/01_basic_scanning.ipynb`
- Installation verification
- Create first catalog (literal pattern)
- Scan local files
- Understand output structure
- Exercises with solutions

#### 2. `tutorials/02_pattern_types.ipynb`
- Literal vs regex comparison
- Common regex patterns for logs
- Testing patterns before running full scan
- When to use each type
- Exercises: Write patterns for given errors

#### 3. `tutorials/03_remote_files.ipynb`
- SSH configuration walkthrough
- URI syntax for different protocols
- Scanning remote files
- Troubleshooting connections
- Exercises: Set up and scan remote logs

**Requirements:**
- Each notebook is self-contained
- Includes sample data (no external dependencies)
- Has "Check Your Understanding" questions
- Shows expected output for each cell
- Works in Google Colab (for students without local setup)

**Deliverables:**
- [ ] Three notebooks created in `tutorials/` directory
- [ ] Sample data included in `tutorials/data/`
- [ ] Each notebook tested on Colab and local Jupyter
- [ ] Solutions provided in separate cells (initially hidden)
- [ ] README in tutorials/ explaining learning path

**Acceptance Criteria:**
- Student completes notebooks 1-3 in 2 hours
- Student can create catalog for own logs after completion
- No blockers requiring external research

---

### Day 8-10: Jupyter Notebooks 4-6 (Python Expert + Documentation Specialist)

**Notebooks to Create:**

#### 4. `tutorials/04_railway_pattern_intro.ipynb`
- Why chain errors? (manual vs automatic)
- Always condition (simplest case)
- Visualizing error chains
- Real-world scenario
- Exercises: Create simple chains

#### 5. `tutorials/05_advanced_railway.ipynb`
- Field-based conditions (field_equals, field_contains)
- Logical operators (AND/OR)
- Nested conditions
- Testing conditions
- Exercises: Complex railway patterns

#### 6. `tutorials/06_climate_model_examples.ipynb`
- SLURM error catalog
- HPC-specific patterns
- Large file handling
- Performance optimization
- Real Autosubmit log examples

**Deliverables:**
- [ ] Three advanced notebooks created
- [ ] Sample SLURM logs included
- [ ] Railway pattern visualization (diagram or animation)
- [ ] Performance benchmarks shown
- [ ] Link to Autosubmit documentation

**Acceptance Criteria:**
- Student understands Railway Pattern after notebook 4
- Student can create complex conditions after notebook 5
- Student can scan HPC logs after notebook 6

---

### Day 10-12: COMMON_ERRORS.md (Documentation Specialist + Python Expert)

**Priority:** HIGH - Reduces support burden

**Task:** Document all common error messages with solutions

**Structure:**
```markdown
# Common Error Messages and Solutions

## Installation Errors
### "Command 'pixi' not found"
[Full error, explanation, solution]

## Catalog Errors
### "ValidationError: field required"
[Full error, explanation, solution]

### "YAML syntax error"
[Full error, explanation, solution]

## Scanning Errors
### "No files matched pattern"
[Full error, explanation, solution]

### "SSH connection timeout"
[Full error, explanation, solution]

## Pattern Errors
### "Regex syntax error"
[Full error, explanation, solution]

## Railway Pattern Errors
### "Condition evaluation failed"
[Full error, explanation, solution]
```

**Deliverables:**
- [ ] `docs/COMMON_ERRORS.md` created
- [ ] 15-20 most common errors documented
- [ ] Each error includes: full message, cause, solution, prevention
- [ ] Linked from README troubleshooting section
- [ ] Searchable (good section headers)

**Acceptance Criteria:**
- Students can find their error in the list
- Solutions are actionable (specific commands to run)
- Prevention tips help avoid errors in future

---

## Week 3: Visual Aids and Climate Guide

**Goal:** Make complex concepts clear, connect to student domain

### Day 13-14: Visual Diagrams (Documentation Specialist + Teacher)

**Priority:** MEDIUM-HIGH - Complex concepts need visuals

**Diagrams to Create:**

1. **Workflow Flowchart**
   - User runs scan → Tool reads catalog → Finds files → Scans for errors → Saves report
   - Simple boxes and arrows
   - SVG or high-res PNG

2. **Railway Pattern Visualization**
   - Side-by-side: Manual vs Automatic
   - Flowchart with conditions
   - Example with real error chain

3. **File Pattern Matching**
   - Directory tree showing what `**/*.log` matches
   - Visual highlighting of matched files
   - Comparison of `*` vs `**`

4. **SSH Connection Pooling**
   - Before: Multiple connections diagram
   - After: Single shared connection
   - Timing comparison

5. **Pattern Type Decision Tree**
   - "What pattern type should I use?"
   - Yes/No questions leading to literal/regex/callable

**Deliverables:**
- [ ] Five diagrams created (SVG preferred for accessibility)
- [ ] Alt text written for each diagram
- [ ] Diagrams added to appropriate documentation sections
- [ ] Source files saved (for future edits)
- [ ] High-res versions for print

**Acceptance Criteria:**
- Diagrams are clear without explanation
- Alt text fully describes diagram for screen readers
- Diagrams match documentation text

---

### Day 14-16: CLIMATE_MODELING_GUIDE.md (Teacher + Python Expert)

**Priority:** HIGH - Target audience domain

**Task:** Create domain-specific guide for climate modelers

**Contents:**
1. **Why Climate Modelers Need This Tool**
   - Large simulation campaigns
   - Distributed HPC logs
   - Common error patterns
   - Time savings

2. **Common Climate Model Errors**
   - SLURM out-of-memory
   - MPI communication failures
   - File I/O errors
   - NetCDF errors
   - Time limit exceeded

3. **Example Catalogs**
   - CESM error catalog
   - WRF error catalog
   - Generic HPC catalog
   - Autosubmit-specific catalog

4. **HPC Best Practices**
   - SSH setup for clusters (LUMI, MareNostrum)
   - Performance tuning for large logs
   - Parallel scanning strategies
   - Quota-friendly scanning

5. **Integration with Autosubmit**
   - Where logs are stored
   - Dynamic experiment ID resolution
   - Workflow-specific patterns
   - Automated monitoring

6. **Real-World Examples**
   - Case study: Finding OOM errors in 10,000 jobs
   - Case study: Tracking MPI failures across nodes
   - Case study: Automated post-simulation checks

**Deliverables:**
- [ ] `docs/CLIMATE_MODELING_GUIDE.md` created
- [ ] Sample catalogs in `examples/climate_models/`
- [ ] Screenshots of real SLURM logs
- [ ] Performance benchmarks (scan 1000 files in X minutes)
- [ ] Links to HPC center documentation

**Acceptance Criteria:**
- Climate modeler sees immediate value
- Examples match their actual workflows
- Catalog templates are copy-paste ready
- Performance is acceptable for large campaigns

---

### Day 16-17: Add Visual Aids to Existing Docs (Documentation Specialist)

**Task:** Integrate diagrams into README, USER_GUIDE, etc.

**Changes:**
- README.md: Add workflow diagram to "How It Works"
- USER_GUIDE.md: Add Railway Pattern visualization
- SSH_CONNECTION_POOLING.md: Add connection diagram
- Pattern sections: Add decision tree

**Deliverables:**
- [ ] Diagrams embedded in all relevant docs
- [ ] Alt text added
- [ ] Caption text written
- [ ] Links to high-res versions

---

## Week 4: Polish and Testing

**Goal:** Ensure completeness and test with real students

### Day 18-19: Prerequisites and Progressive Disclosure (Teacher)

**Task:** Add learning path guidance to all documents

**For Each Document:**
1. Add "Prerequisites" section at top
   - Required knowledge
   - Helpful background
   - Links to learning resources
   - Self-assessment quiz

2. Add difficulty markers
   - 🟢 Beginner
   - 🟡 Intermediate
   - 🔴 Advanced

3. Add "Learning Path" section
   - What to read first
   - What to read next
   - What to skip if...

**Deliverables:**
- [ ] Prerequisites added to README, USER_GUIDE, tutorials
- [ ] Difficulty markers on all sections
- [ ] Learning path guide created (`docs/LEARNING_PATH.md`)
- [ ] "Skip this if..." notes added to advanced sections

**Acceptance Criteria:**
- Students know what to learn first
- Students can skip irrelevant content
- Prerequisites are realistic (no PhD required)

---

### Day 19-20: Readability Pass (Documentation Specialist)

**Task:** Improve reading level and reduce jargon

**Process:**
1. Run all docs through Hemingway Editor
2. Target reading level: Grade 12-14 (currently 16-18)
3. Simplify complex sentences
4. Replace jargon using TERMINOLOGY_QUICK_FIX.md
5. Add examples where text is too abstract

**Specific Targets:**
- Replace "implements X pattern" with "does X"
- Replace "orchestration" with "workflow management"
- Replace "polymorphic" with "multiple types"
- Replace "domain model" with "data structure"
- Remove design pattern references (strategy, repository, etc.)

**Deliverables:**
- [ ] All docs at Grade 14 or below
- [ ] Jargon density ≤ 2 technical terms per sentence
- [ ] Technical terms link to glossary
- [ ] Complex sentences split into shorter ones

**Acceptance Criteria:**
- Hemingway Editor shows Grade 12-14
- Student reviewer approves readability
- No circular definitions remain

---

### Day 21-22: Student Testing (Teacher + Student Reviewer)

**Task:** Test documentation with 3-5 real graduate students

**Protocol:**
1. Recruit students (climate modeling background, basic Python)
2. Give documentation only (no live help)
3. Ask them to:
   - Install tool
   - Complete quick start
   - Work through tutorials 1-3
   - Create catalog for their own logs
   - Run scan
4. Track metrics:
   - Time per task
   - Where they get stuck
   - Questions they ask
   - External resources consulted
   - Sections they skip

**Deliverables:**
- [ ] Testing protocol documented
- [ ] 3-5 students recruited and tested
- [ ] Results compiled (time per task, blockers, questions)
- [ ] Recommendations for iteration
- [ ] Updated docs based on feedback

**Acceptance Criteria:**
- 80% of students complete quick start without help
- Average time to first scan: 30-45 minutes
- Students can explain Railway Pattern in own words
- No critical blockers identified

---

### Day 23-24: Final Integration and Release (All Team)

**Task:** Finalize, integrate, and publish documentation

**Activities:**
1. **Documentation Specialist:**
   - Final consistency check (terminology, formatting)
   - Link verification (all internal links work)
   - Table of contents updates
   - Spell check

2. **Teacher:**
   - Learning path verification
   - Tutorial flow testing
   - Exercise solution verification

3. **Python Expert:**
   - Code example testing (all examples run)
   - Sample data verification
   - Error message accuracy

4. **Student Reviewer:**
   - Final accessibility check
   - Readability verification
   - Beginner experience test

**Deliverables:**
- [ ] All documentation merged to main branch
- [ ] Tutorials published to JupyterBook
- [ ] Read the Docs site updated
- [ ] CHANGELOG updated with "Documentation overhaul"
- [ ] Announcement post written (blog/email)

**Acceptance Criteria:**
- All links work
- All code examples run
- All images display
- No typos or formatting errors
- Read the Docs builds successfully

---

## Success Metrics

### Quantitative

- [ ] Documentation reading level: Grade 12-14 (currently 16-18)
- [ ] Time to first scan: 30 minutes (currently 60-90 minutes)
- [ ] Time to understand Railway Pattern: 30 minutes (currently 2+ hours)
- [ ] Tutorial completion rate: 80% (currently unknown)
- [ ] Support requests for "getting started": -70%

### Qualitative

- [ ] Students can explain Railway Pattern in own words
- [ ] Students can decide when to use literal vs regex patterns
- [ ] Students successfully scan remote logs
- [ ] Students create catalogs for their own logs
- [ ] Positive feedback from test students

---

## Team Assignments

### Documentation Specialist
- GLOSSARY.md creation
- Railway Pattern rewrite
- SSH setup promotion
- Visual aids integration
- Readability pass
- Final integration

### Teacher
- QUICK_START_FOR_STUDENTS.md
- Railway Pattern rewrite (with Documentation Specialist)
- Tutorial notebooks (with Python Expert)
- CLIMATE_MODELING_GUIDE.md
- Prerequisites and progressive disclosure
- Student testing coordination

### Python Expert
- QUICK_START_FOR_STUDENTS.md (with Teacher)
- Fix first example (sample data)
- Tutorial notebooks (all six)
- COMMON_ERRORS.md
- Code example verification

### Student Reviewer
- Review all deliverables from student perspective
- Test documentation with real students
- Identify remaining confusion points
- Final accessibility check

---

## Risk Mitigation

### Risk: Students still confused after fixes

**Mitigation:**
- Test with real students in Week 4
- Iterate based on feedback
- Create FAQ from common questions

### Risk: Timeline slips

**Mitigation:**
- Parallelize work across team
- Prioritize critical items (Week 1)
- Polish items can extend to Week 5 if needed

### Risk: Example code breaks

**Mitigation:**
- Python Expert verifies all code
- Automated testing in CI/CD
- Sample data checked into repo

### Risk: Terminology inconsistency

**Mitigation:**
- GLOSSARY.md created first (Day 1-2)
- All team members reference it
- Final consistency check in Week 4

---

## Deliverables Checklist

### Week 1
- [ ] GLOSSARY.md
- [ ] QUICK_START_FOR_STUDENTS.md
- [ ] Railway Pattern rewritten in all docs
- [ ] SSH setup promoted to installation
- [ ] First example fixed with sample data

### Week 2
- [ ] Tutorials 01-03 (basic, patterns, remote)
- [ ] Tutorials 04-06 (railway, advanced, climate)
- [ ] COMMON_ERRORS.md

### Week 3
- [ ] Five visual diagrams created
- [ ] CLIMATE_MODELING_GUIDE.md
- [ ] Diagrams integrated into existing docs

### Week 4
- [ ] Prerequisites added to all docs
- [ ] Readability improvements (Grade 12-14)
- [ ] Student testing completed
- [ ] Final integration and publication

---

## Maintenance Plan

**Post-Release:**

1. **Monitor Support Channels**
   - Track new "getting started" questions
   - Update COMMON_ERRORS.md with new issues
   - Identify documentation gaps

2. **Collect Feedback**
   - Survey students after first scan
   - Track tutorial completion rates
   - Monitor time-to-first-scan metric

3. **Iterate**
   - Monthly documentation review
   - Update examples with new use cases
   - Improve sections with high confusion

4. **Keep Current**
   - Update when features change
   - Add new tutorials for new features
   - Refresh screenshots

---

## Appendix: Templates

### Tutorial Notebook Template

```python
# Notebook Title
"""
Learning objectives:
- Objective 1
- Objective 2

Prerequisites:
- Prerequisite 1
- Prerequisite 2

Time: X minutes
"""

## Setup
# Installation verification
# Sample data download

## Section 1: Concept Introduction
# Plain English explanation
# Analogy
# Why you need this

## Section 2: Simple Example
# Step-by-step walkthrough
# Expected output shown

## Section 3: Your Turn
# Exercise
# Solution (hidden by default)

## Section 4: Common Mistakes
# What can go wrong
# How to fix

## Section 5: Check Your Understanding
# Self-assessment questions
# Links to next tutorial
```

### Error Documentation Template

```markdown
### Error Name

**Full error message:**
```
[Complete error text as student sees it]
```

**What this means:** [Plain English explanation]

**Common causes:**
1. Cause 1
2. Cause 2

**How to fix:**

Step 1:
```bash
[Command to run]
```

Step 2:
[Action to take]

**How to prevent this in future:**
[Best practice to avoid error]

**Still stuck?**
[Link to forum / where to get help]
```

---

**End of Action Plan**

**Timeline:** 4 weeks (24 working days)
**Team Size:** 4 agents (can parallelize)
**Output:** 15+ new documentation files, 6 tutorials, major revisions to existing docs
**Expected Impact:** 70% reduction in "getting started" support requests, 2x faster time-to-first-scan
