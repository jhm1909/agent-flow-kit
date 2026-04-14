---
name: code-graph
description: >-
  Analyzes codebase structure using blast-radius tracing, hub/bridge detection,
  and risk scoring. Use when reviewing code changes, assessing refactoring impact,
  understanding project architecture, or preparing for code review.
---

# Code Graph

> **Execution context:** Script paths are relative to this skill directory (`.agents/skills/code-graph/`).

Analyze codebase structure and change impact through import graph analysis.

## When to use this skill

- Reviewing a PR or recent code changes → blast-radius analysis
- Assessing impact before refactoring → hub/bridge detection
- Understanding which files are most critical → hub detection
- Preparing for code review → risk scoring
- Generating architecture diagrams → hub-detect --json + diagram skill

## Methodology: Blast-Radius Analysis

The core principle: **don't read the entire codebase.** Trace only the impact of changes.

```
Changed File → Direct Callers → Transitive Dependents → Affected Tests
                    ↓
              "Blast Radius" = minimal set of files to review
```

### Risk classification (automated by script)

| Level | Condition | Review Strategy |
|-------|-----------|-----------------|
| **CRITICAL** | High-risk code AND 50+ callers | Read ALL files in blast radius |
| **HIGH** | High-risk code OR 50+ callers | Read changed + callers + tests |
| **MEDIUM** | 10+ callers OR no test coverage | Read changed + direct callers |
| **LOW** | Small radius, tests exist | Read changed files only |

**High-risk patterns** (auto-detected): `auth`, `crypto`, `password`, `token`, `secret`, `validation`, `permission`, `access`

**No test coverage** elevates LOW → MEDIUM automatically.

## Methodology: Hub & Bridge Detection

- **Hubs** = most-imported files. Changes here ripple widely → review carefully, test thoroughly.
- **Bridges** = files connecting separate directories. Changes here break cross-module contracts.
- **Critical Hubs** (20+ importers) = architectural hotspots. Never change without full blast-radius review.

## Available Scripts

| Script | Purpose | Key flags |
|--------|---------|-----------|
| `scripts/blast-radius.sh` | Trace callers + dependents + tests, risk classification | `--json` for structured output |
| `scripts/hub-detect.sh` | Find hubs, bridges, directory structure | `--json` for diagram-compatible output |

Both scripts support `--help` for full usage.

### `--json` flag

Use `--json` when:
- Feeding data to the diagram skill: `hub-detect.sh --json | svg-gen.py`
- Parsing results programmatically in workflows
- Need structured data instead of human-readable text

## How to use it

### Reviewing changes (escalation pattern)

1. **Quick assessment** — run with no args (auto-detects from git diff):
   ```bash
   bash scripts/blast-radius.sh
   ```

2. **Read the risk level** in the output header.

3. **Escalate based on risk**:
   - **LOW**: Skim changed files only. You're done.
   - **MEDIUM**: Read changed files + every file listed under "Direct Callers". Check test section for gaps.
   - **HIGH/CRITICAL**: Read EVERY file in the output. Flag test coverage gaps. Consider running the full review workflow (`/code-review`).

4. **If blast radius > 50 files** → warn user: "Large scope — review may miss issues. Consider splitting the change."

### Understanding architecture

1. **Run hub detection**:
   ```bash
   bash scripts/hub-detect.sh
   ```

2. **Interpret results**:
   - Top hubs = files to understand first when onboarding
   - Bridges = files that connect otherwise separate modules
   - If no hubs found = codebase has low coupling (good) or is too small

3. **Generate architecture diagram** (chain with diagram skill):
   ```bash
   bash scripts/hub-detect.sh --json | python3 ../diagram/scripts/svg-gen.py -o arch.svg --style blueprint --output-dir .agents-output/visualize/svg
   ```

### Optional: full Python engine

For deeper analysis (AST parsing, execution flows, community detection), install:
```bash
pip install code-review-graph
```

## References

| File | Load when |
|------|-----------|
| [blast-radius.md](references/blast-radius.md) | Need risk scoring methodology details, tracing algorithm |
| [security-checklist.md](references/security-checklist.md) | During code review — red flags, language-specific checks |
| [architecture.md](references/architecture.md) | Understanding the full graph engine design (Python package) |
