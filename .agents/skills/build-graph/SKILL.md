---
name: build-graph
description: >-
  Builds or updates the code knowledge graph. Use before first-time code review,
  after major refactoring, or when analysis seems stale. With shell scripts,
  the graph is built implicitly on each run — no separate build step needed.
---

# Build Graph

Initialize or refresh the code analysis for a repository.

## When to use this skill

- First time analyzing a repository
- After major refactoring, branch switches, or large merges
- If blast-radius or hub-detect results seem stale
- Setting up analysis for a new team member

## How it works

### Shell scripts (default — zero dependency)

The shell scripts (`blast-radius.sh`, `hub-detect.sh`) scan the codebase fresh on each run. **No separate build step needed.** Just run the analysis:

```bash
# These build the graph implicitly
bash skills/code-graph/scripts/blast-radius.sh
bash skills/code-graph/scripts/hub-detect.sh
```

### Python engine (optional — deeper analysis)

If `code-review-graph` is installed (`pip install code-review-graph`):

```bash
# Full build (first time — parses entire codebase with tree-sitter)
code-review-graph build

# Incremental update (only re-parses changed files)
code-review-graph update

# Check current state
code-review-graph status
```

The Python engine stores a persistent SQLite graph at `.code-review-graph/graph.db`, enabling:
- 19-language AST parsing
- Execution flow tracing
- Community detection
- Incremental updates in <2 seconds

## When to rebuild

| Situation | Shell scripts | Python engine |
|-----------|--------------|---------------|
| Normal development | No action needed (auto-scan) | Auto-updates via hooks |
| Major refactoring | No action needed | `code-review-graph build` (full rebuild) |
| Branch switch | No action needed | `code-review-graph build` (re-index) |
| Stale results | Re-run the analysis script | `code-review-graph update` |
