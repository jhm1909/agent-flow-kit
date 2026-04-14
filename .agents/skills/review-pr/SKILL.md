---
name: review-pr
description: Reviews a pull request using blast-radius analysis and risk scoring. Use when asked to review a PR, check code changes, or assess merge readiness.
---

# Review PR

Perform a structured code review of a pull request with blast-radius analysis.

## When to use this skill

- Asked to review a PR or branch diff
- Checking if changes are safe to merge
- Need a risk assessment of code changes

## How to use it

1. **Identify changed files**:
   ```bash
   git diff --name-only main...HEAD
   ```

2. **Run blast-radius analysis**:
   ```bash
   bash skills/code-graph/scripts/blast-radius.sh <changed-files>
   ```

3. **Review based on risk level**:
   - Read files in priority order: CHANGED → CALLER → TEST → TRANSITIVE
   - For high-risk functions, check who calls them and whether tests cover them
   - Look for: removed validation, broken public APIs, missing tests

4. **Report findings** using this structure:
   ```
   ## PR Review: <title>

   ### Summary
   <1-3 sentence overview>

   ### Risk Assessment
   - Overall risk: Low / Medium / High
   - Blast radius: X files impacted
   - Test coverage gaps: <list>

   ### Issues Found
   - <file:line> — <description>

   ### Recommendations
   1. <actionable suggestion>
   ```

## Tips

- Focus on highest-impact files first (most dependents in blast radius)
- Check if renamed/moved functions have updated all callers
- For large PRs (50+ files), warn user that review may be incomplete
