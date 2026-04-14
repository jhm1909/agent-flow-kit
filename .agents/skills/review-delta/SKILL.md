---
name: review-delta
description: >-
  Quick review of only changes since last commit using blast-radius detection.
  Token-efficient delta review. Use for fast iteration reviews during development,
  checking if recent edits broke anything, or reviewing a single commit.
---

# Review Delta

> **Execution context:** Cross-skill script paths use `../` relative references.

Focused, token-efficient review of the most recent changes and their impact.

## When to use this skill

```
User request → Which review skill?
├─ "check my changes" / "did I break anything?" → review-delta (this skill)
├─ "quick review" / single commit → review-delta
├─ Risk is LOW/MEDIUM (from code-review workflow) → review-delta
├─ Risk is HIGH → escalate to review-pr or /code-review workflow
├─ "review this PR" / merge readiness → review-pr
└─ Multiple commits against base branch → review-pr
```

- Quick review during active development (after each commit)
- Checking if recent edits introduced bugs
- Want a lighter review than full PR review
- Reviewing a single commit (not multi-commit PR)

**For full PR reviews** (multiple commits, merge readiness) → use `[review-pr]` instead.

## How to use it

### 1. Get recent changes (auto-detect)

```bash
bash ../code-graph/scripts/blast-radius.sh
# No args = auto-detects from git diff HEAD~1..HEAD
```

### 2. Read the risk level and follow escalation

- **LOW**: Skim changed files only. Check for obvious issues. Done.
- **MEDIUM**: Read changed files + direct callers. Check test gaps.
- **HIGH**: Escalate — recommend using `/code-review` workflow instead.

### 3. Focus review on blast-radius output

For each changed file:
- Correctness: does the code do what it should?
- Style: follows project conventions?
- Callers: do upstream consumers need updates?
- Tests: does changed behavior have test coverage?

### 4. Report findings

```
## Delta Review

- **Summary**: <one line>
- **Risk level**: <from blast-radius>
- **Issues**: <list with file:line>
- **Test gaps**: <untested changed functions>
- **Blast radius**: <N files impacted>
```

## Advantages over full PR review

- Examines only changed + impacted code (5-10x fewer tokens)
- Auto-detects changes from git diff (no args needed)
- Fast iteration: run after each commit during development
- Naturally escalates to full review when risk is HIGH
