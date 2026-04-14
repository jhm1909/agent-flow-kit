---
description: Orchestrates code review using blast-radius analysis, risk-based escalation, and structured reporting. Chains code-graph analysis with review-delta or review-pr skills.
---

# Code Review Workflow

> **Execution context:** All script paths are relative to the `.agents/` root directory.

---

## Step 1: Identify Changes

// turbo

1. Determine the change scope:
   ```bash
   git diff --name-only HEAD~1..HEAD
   ```
   Or use user-specified range (PR branch, commit range, specific files).
2. If no changes found → inform user and stop.
3. Count changed files and list them.
4. **Assess scope**: if 50+ files changed, warn user: "Large change set — review will focus on highest-impact files."

**Output**: Changed file list + scope assessment

---

## Step 2: Blast-Radius Analysis

// turbo

1. **Invoke `[code-graph]` skill** — run blast-radius with JSON for structured data:
   ```bash
   mkdir -p .agents-output/code-graph/reports
   bash skills/code-graph/scripts/blast-radius.sh --json > .agents-output/code-graph/reports/blast-radius.json
   ```

2. Read the JSON output. Key fields:
   - `risk.level` → determines review depth (Step 3)
   - `callers` → files that directly use changed code
   - `tests` → affected test files (empty = coverage gap)
   - `review_order` → priority-sorted file list

3. **Decision gate** based on risk:
   - **LOW** → proceed to Step 3 with minimal review
   - **MEDIUM** → proceed to Step 3 with standard review
   - **HIGH/CRITICAL** → **WAIT** — alert user: "Risk level is [X]. Blast radius: [N] files. Proceed with deep review?"

**Output**: Risk level + blast-radius report in `.agents-output/code-graph/reports/`

---

## Step 3: Focused Review (Risk-Based Escalation)

// turbo

**Review depth scales with risk level:**

### LOW risk
1. **Invoke `[review-delta]` skill** — quick delta review.
2. Read only changed files. Check for obvious bugs, style issues.
3. Verify tests exist (if `tests` array is non-empty in blast-radius JSON).
4. Skip to Step 4.

### MEDIUM risk
1. **Invoke `[review-delta]` skill** — standard review.
2. Read changed files + all files listed under `callers`.
3. **Invoke `[code-graph]` skill** — read [security-checklist.md](skills/code-graph/references/security-checklist.md) and check for:
   - Security red flags (removed validation, hardcoded secrets, SQL concatenation)
   - Public API changes (breaking changes for consumers?)
   - Missing test coverage (any `callers` without corresponding tests?)
4. If test coverage gaps found → flag them explicitly.

### HIGH / CRITICAL risk
1. **Invoke `[review-pr]` skill** — full PR review.
2. Read ALL files in `review_order` (changed → callers → tests → transitive).
3. **Invoke `[code-graph]` skill** — read [security-checklist.md](skills/code-graph/references/security-checklist.md). For each high-risk file:
   - Run full security checklist (red flags + language-specific checks)
   - Check who calls it (from blast-radius callers list)
   - Check if tests cover the changed behavior
   - Look for removed validation, broken contracts, missing error handling
4. **Invoke `[code-graph]` skill** — run hub detection to check if changed files are hubs:
   ```bash
   bash skills/code-graph/scripts/hub-detect.sh
   ```
   If a changed file is a hub (10+ importers) → escalate priority.

**Output**: File-by-file review notes

---

## Step 4: Report

// turbo

1. Present findings using structured format:
   ```
   ## Code Review

   ### Summary
   <1-3 sentence overview of changes>

   ### Risk Assessment
   - **Risk level**: LOW / MEDIUM / HIGH / CRITICAL
   - **Blast radius**: X direct callers, Y transitive dependents
   - **Test coverage**: N files covered, M gaps found

   ### Issues Found
   - [CRITICAL] <file:line> — <description>
   - [HIGH] <file:line> — <description>
   - [MEDIUM] <file:line> — <description>

   ### Test Coverage Gaps
   - <function/file> — no tests found

   ### Recommendations
   1. <specific, actionable suggestion>
   2. <specific, actionable suggestion>
   ```

2. **WAIT** — ask user: "Want me to fix any of these issues, or dive deeper into a specific file?"

**Output**: Structured review report

---

## Quick Reference

| Step | Skill | Output |
|------|-------|--------|
| 1 | — | Changed file list |
| 2 | code-graph | Blast-radius JSON + risk level |
| 3 (LOW) | review-delta | Quick delta review |
| 3 (MED) | review-delta | Standard review + caller check |
| 3 (HIGH) | review-pr + code-graph | Full PR review + hub detection |
| 4 | — | Structured report |
