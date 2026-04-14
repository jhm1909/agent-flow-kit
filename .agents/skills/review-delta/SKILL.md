---
name: review-delta
description: Reviews only changes since last commit using blast-radius detection. Token-efficient delta review. Use for quick reviews of recent changes.
---

# Review Delta

Focused review of only the most recent changes and their impact.

## When to use this skill

- Quick review of changes since last commit
- Want a lighter review than full PR review
- Checking if recent edits broke anything

## How to use it

1. **Get changed files**:
   ```bash
   git diff --name-only HEAD~1..HEAD
   ```

2. **Run blast-radius analysis**:
   ```bash
   bash skills/code-graph/scripts/blast-radius.sh
   # No args = auto-detects from git diff
   ```

3. **Focus review** on the blast radius output:
   - Review changed code for correctness and style
   - Check if callers/dependents need updates
   - Flag untested changed functions

4. **Report findings**:
   - **Summary**: One-line overview
   - **Risk level**: Based on blast radius size
   - **Issues**: Bugs, style, missing tests
   - **Blast radius**: Impacted files/functions

## Advantages over full review

- Only examines changed + impacted code (fewer tokens)
- Automatically identifies blast radius
- Fast iteration cycle for active development
