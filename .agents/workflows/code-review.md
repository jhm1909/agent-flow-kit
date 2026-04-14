---
description: Orchestrates code review using blast-radius analysis, risk scoring, and structured reporting.
---

# Code Review Workflow

> **Execution context:** All script paths are relative to the `.agents/` root directory.

---

## Step 1: Identify Changes

// turbo

1. **Invoke `[code-graph]` skill** to identify changed files:
   ```bash
   git diff --name-only HEAD~1..HEAD
   ```
   Or user-specified range / PR branch.
2. If no changes found → inform user and stop.
3. List changed files for context.

---

## Step 2: Blast-Radius Analysis

// turbo

1. **Invoke `[code-graph]` skill** — run blast-radius:
   ```bash
   bash scripts/blast-radius.sh <changed-files>
   ```
2. Capture output: direct callers, transitive dependents, affected tests, risk level.
3. If blast-radius > 50 files → warn user: "Large scope, review may be incomplete."
4. **WAIT** for user to confirm review scope.

---

## Step 3: Focused Review

// turbo

1. **Invoke `[review-delta]` skill** for risk-based review strategy:
   - **CRITICAL/HIGH** → read ALL files in blast radius
   - **MEDIUM** → read changed files + direct callers
   - **LOW** → read changed files only
2. For each file, check:
   - Security-sensitive changes (auth, validation, access control)
   - Breaking changes to public APIs
   - Missing test coverage for changed functions
3. **Invoke `[review-pr]` skill** if reviewing a full PR (multiple commits).

---

## Step 4: Report

// turbo

1. Present findings using the `[review-pr]` output template:
   ```
   ## Code Review

   ### Summary
   <1-3 sentence overview>

   ### Risk Assessment
   - Overall risk: Low / Medium / High
   - Blast radius: X files impacted
   - Test coverage gaps: <list>

   ### Issues Found
   - <file:line> — <description> [CRITICAL/HIGH/MEDIUM/LOW]

   ### Recommendations
   1. <actionable suggestion>
   ```
2. **WAIT** for user to acknowledge findings.

---

## Quick Reference

| Step | Skill                      | Output                  |
|------|----------------------------|-------------------------|
| 1    | code-graph                 | Changed file list       |
| 2    | code-graph                 | Blast-radius + risk     |
| 3    | review-delta / review-pr   | File-by-file review     |
| 4    | review-pr                  | Structured report       |
