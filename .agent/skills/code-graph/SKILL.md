---
name: code-graph
description: >
  Full codebase graph analysis: AST parsing (19 languages), blast-radius tracing, risk scoring,
  hub/bridge detection, execution flow tracing, community detection, refactoring tools.
  Includes lightweight shell fallbacks and full Python engine (from code-review-graph).
metadata:
  version: "2.0.0"
  sources:
    - code-review-graph (full port: parser, graph store, analysis, flows, communities, search)
---

# Code Graph Analysis

Understand codebase structure and change impact through graph analysis.

## Two Modes

### Full Engine (Python — recommended for real projects)

Requires: `pip install tree-sitter` (optional dependencies in `pyproject.toml`)

```bash
# Build graph from codebase
python -m code_graph build

# Detect changes with risk scoring
python -m code_graph detect-changes

# Show architecture overview
python -m code_graph status

# Interactive D3.js visualization
python -m code_graph visualize

# Watch for changes (auto-update)
python -m code_graph watch
```

### Lightweight Fallback (Shell — zero dependency)

```bash
# Blast-radius via grep (fast, approximate)
./scripts/blast-radius.sh [files...]

# Hub detection via import counting
./scripts/hub-detect.sh [directory]
```

## Decision Tree

```
SITUATION?
├─ Reviewing a PR / changed files
│  ├─ Full engine available?
│  │  ├─ Yes → python -m code_graph detect-changes
│  │  │  ├─ Returns: risk-scored nodes, affected flows, test gaps
│  │  │  └─ Follow risk level → review strategy (see below)
│  │  └─ No → ./scripts/blast-radius.sh
│  └─ Check test coverage → flag gaps
├─ Understanding architecture
│  ├─ python -m code_graph status → overview stats
│  ├─ python -m code_graph visualize → D3.js interactive graph
│  ├─ Hubs = most-connected files (change carefully)
│  ├─ Bridges = cross-module connectors (test thoroughly)
│  └─ Communities = code clusters (cross-community changes = higher risk)
├─ Planning a refactor
│  ├─ python -m code_graph detect-changes → impact analysis
│  ├─ Check execution flows affected
│  ├─ If blast-radius > 50 → warn user, suggest incremental approach
│  └─ python -m code_graph find-dead-code → cleanup candidates
├─ Onboarding / exploration
│  ├─ python -m code_graph status → project overview
│  ├─ python -m code_graph visualize → interactive graph
│  └─ Read: references/architecture.md
└─ Reference needed
   └─ Read specific reference (see table below)
```

## Capabilities (Full Engine)

| Feature | Module | Description |
|---------|--------|-------------|
| **AST Parsing** | `parser.py` | 19 languages via tree-sitter (Python, JS/TS, Go, Java, Rust, C++, Ruby, PHP, Swift, Kotlin, Dart, Vue, Solidity...) |
| **Graph Store** | `graph.py` | SQLite with recursive CTEs, FTS5 search, WAL mode |
| **Blast Radius** | `changes.py` | Risk-scored per-node analysis with flow + community impact |
| **Hub/Bridge** | `analysis.py` | Degree centrality (hubs), betweenness centrality (bridges), knowledge gaps |
| **Execution Flows** | `flows.py` | Entry-point detection (18 framework patterns), BFS flow tracing, criticality scoring |
| **Communities** | `communities.py` | Leiden algorithm (igraph) or file-based fallback, cohesion metrics |
| **Search** | `search.py` | FTS5 + optional vector embeddings, BM25 ranking, RRF fusion |
| **Incremental** | `incremental.py` | Hash-based change detection, parallel parsing, watch mode, dependent expansion |
| **Visualization** | `visualization.py` | Self-contained D3.js HTML, multiple modes (file/community/full) |
| **Refactoring** | `refactor.py` | Rename preview, dead code detection, move suggestions |
| **Hints** | `hints.py` | Intent classification, next-step suggestions, session tracking |
| **Prompts** | `prompts.py` | 5 workflow templates (review, architecture, debug, onboard, pre-merge) |

## Risk Scoring (Full Engine)

Per-node risk score (0.0-1.0), 5 weighted factors:

| Factor | Weight | Scoring |
|--------|--------|---------|
| Flow participation | 0.30 | 0.05 per flow, capped 0.25, weighted by criticality |
| Cross-community callers | 0.15 | 0.05 per unique community, capped |
| Test coverage | 0.30 | 0.30 (untested) → 0.05 (5+ tests) |
| Security keywords | 0.20 | +0.20 if auth/crypto/sql/etc |
| Caller count | 0.10 | callers/20, capped |

## Risk Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **CRITICAL** | High-risk code + 50+ callers | Full review of entire blast radius |
| **HIGH** | High-risk code OR 50+ callers | Review changed + callers + tests |
| **MEDIUM** | Medium-risk OR 10+ callers OR no test coverage | Review changed + direct callers |
| **LOW** | Low-risk, small blast radius, has tests | Review changed files only |

## Prompt Templates (5 Workflows)

| Template | Use When |
|----------|----------|
| `review_changes` | Pre-commit review with risk escalation |
| `architecture_map` | Generate architecture docs with Mermaid |
| `debug_issue` | Guided debugging through graph traversal |
| `onboard_developer` | New dev orientation and codebase tour |
| `pre_merge_check` | PR readiness: risk + test gaps + dead code |

## References

| Reference | Purpose |
|-----------|---------|
| `blast-radius.md` | Core methodology: tracing, risk scoring, hub/bridge theory |
| `architecture.md` | System architecture of the code-graph engine |
| `schema.md` | SQLite database schema (nodes, edges, flows, communities) |
| `features.md` | Complete feature list |
| `commands.md` | CLI command reference |
| `usage.md` | Usage guide and examples |
| `claude-usage.md` | How AI agents should use this tool |
| `skills/` | Original skill definitions (build-graph, review-delta, review-pr) |