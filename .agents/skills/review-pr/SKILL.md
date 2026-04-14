---
name: review-pr
description: >-
  Performs full PR review with blast-radius analysis and structured output.
  Use when reviewing a complete pull request, checking merge readiness,
  or assessing multi-commit changes against a base branch.
---

# Review PR

Full structural code review of a pull request or branch diff.

## When to use this skill

- Reviewing a complete PR (multiple commits)
- Checking if a branch is safe to merge
- Need blast-radius across ALL commits (not just last one)
- User says "review this PR" or "is this ready to merge?"

**For quick single-commit reviews** → use `[review-delta]` instead.

## How to use it

### 1. Identify the changes

```bash
git diff --name-only main...HEAD
```

### 2. Run blast-radius on ALL changed files

```bash
bash skills/code-graph/scripts/blast-radius.sh $(git diff --name-only main...HEAD)
```

### 3. Review based on risk level

Follow the escalation pattern from `[code-graph]` skill:
- **LOW** → skim changed files
- **MEDIUM** → read changed + direct callers
- **HIGH/CRITICAL** → read entire blast radius + run hub detection

### 4. For each reviewed file, check

- **Security**: auth/validation removed? access control weakened?
- **API contracts**: public interfaces changed? breaking changes?
- **Test coverage**: changed functions have tests? new code untested?
- **Dependencies**: new imports? removed dependencies still used elsewhere?

### 5. Generate structured report

```
## PR Review: <title>

### Summary
<1-3 sentence overview>

### Risk Assessment
- **Overall risk**: Low / Medium / High / Critical
- **Blast radius**: X files, Y direct callers impacted
- **Test coverage**: N changed functions covered / M total

### File-by-File Review
#### <file_path>
- **Changes**: <what changed>
- **Impact**: <who depends on this>
- **Issues**: <bugs, concerns>

### Test Coverage Gaps
- <function> in <file> — no test coverage found

### Recommendations
1. <specific, actionable>
2. <specific, actionable>
```

## Tips

- Focus on highest-impact files first (most dependents from blast radius)
- Check if renamed/moved functions updated all callers
- For large PRs (50+ files) → warn user review may be incomplete
- Run hub detection to see if changed files are architectural hotspots
