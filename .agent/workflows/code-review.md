---
description: Analyze changed files using blast-radius tracing and risk scoring for focused code review.
---

# Code Review Workflow

## Step 1: Identify Changes

// turbo

1. Run: `git diff --name-only HEAD~1..HEAD` (or user-specified range).
2. If no changes → inform user, stop.
3. List changed files for context.

---

## Step 2: Blast-Radius Analysis

// turbo

1. Run: `./.agent/scripts/blast-radius.sh <changed files>`
2. Capture output: callers, dependents, tests, risk level.
3. If blast-radius > 50 files → warn user: "Large scope, review may be incomplete."

---

## Step 3: Focused Review

// turbo

1. Read files in priority order based on risk level:
   - **CRITICAL/HIGH**: All files in blast radius.
   - **MEDIUM**: Changed files + direct callers.
   - **LOW**: Changed files only.
2. Check for:
   - Security patterns removed (auth, validation, access control).
   - Breaking changes to public APIs.
   - Missing test coverage for changed code.
3. **Read skill**: `.agent/skills/code-graph/SKILL.md` for methodology.

---

## Step 4: Report

// turbo

1. Present findings with evidence (file:line references).
2. Classify each finding: CRITICAL / HIGH / MEDIUM / LOW.
3. Suggest specific fixes where applicable.
