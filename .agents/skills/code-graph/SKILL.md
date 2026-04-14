---
name: code-graph
description: Analyzes codebase structure using blast-radius tracing and hub/bridge detection. Use when reviewing code changes, assessing refactoring impact, or understanding project architecture.
---

# Code Graph

Analyze codebase structure and change impact through import graph analysis.

## When to use this skill

- Reviewing a PR or recent code changes
- Assessing impact before refactoring
- Finding the most critical files in a codebase (hubs and bridges)
- Understanding which files are affected by a change

## Available scripts

Run with `--help` or no arguments to see usage:

- `scripts/blast-radius.sh` — Trace callers, dependents, and tests for changed files. Outputs risk classification (CRITICAL/HIGH/MEDIUM/LOW).
- `scripts/hub-detect.sh` — Find most-imported files (hubs) and cross-directory connectors (bridges).

## How to use it

### Reviewing changes

1. Run blast-radius analysis:
   ```bash
   bash scripts/blast-radius.sh [changed-files...]
   # With no args: auto-detects from git diff
   ```

2. Follow the risk level in the output:
   - **CRITICAL/HIGH** → read ALL files listed in the blast radius
   - **MEDIUM** → read changed files + direct callers
   - **LOW** → read changed files only

3. Check the "Affected Tests" section — flag gaps in test coverage.

### Understanding architecture

1. Run hub detection:
   ```bash
   bash scripts/hub-detect.sh [directory]
   ```

2. Interpret the results:
   - **Hubs** = most-imported files. Changes here affect many dependents.
   - **Bridges** = files connecting separate directories. Test these thoroughly.

### Optional: full Python engine

For deeper analysis (AST parsing, execution flows, community detection), install the original package:
```bash
pip install code-review-graph
```

See [commands.md](references/commands.md) for CLI usage and [features.md](references/features.md) for capabilities.

## References

| File | Use when |
|------|----------|
| [blast-radius.md](references/blast-radius.md) | Need risk scoring methodology details |
| [architecture.md](references/architecture.md) | Understanding the full graph engine design |
| [commands.md](references/commands.md) | Using the pip-installed CLI |
| [features.md](references/features.md) | Full feature list of the Python engine |
| [schema.md](references/schema.md) | SQLite database schema details |
