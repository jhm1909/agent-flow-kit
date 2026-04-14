---
name: build-graph
description: Builds or updates the code knowledge graph for a repository. Use before running code reviews or architecture analysis for the first time.
---

# Build Graph

Initialize or update the code knowledge graph for this repository.

## When to use this skill

- First time analyzing a repository
- After major refactoring or branch switches
- If analysis results seem stale or incomplete

## How to use it

### With shell scripts (zero dependency)

The graph is implicitly built when you run analysis scripts:
```bash
bash skills/code-graph/scripts/blast-radius.sh
bash skills/code-graph/scripts/hub-detect.sh
```
These scripts scan the codebase on each run — no separate build step needed.

### With the Python engine (if installed)

```bash
# Full build (first time)
code-review-graph build

# Incremental update
code-review-graph update

# Check status
code-review-graph status
```

The graph is stored as SQLite at `.code-review-graph/graph.db`.
