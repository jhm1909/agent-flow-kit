---
name: code-graph
description: >
  Analyze codebase structure using blast-radius tracing, risk scoring, and hub/bridge detection.
  Use for PR review, refactoring impact analysis, and architecture understanding.
metadata:
  version: "1.0.0"
  sources:
    - code-review-graph (blast-radius, risk scoring, hub/bridge detection)
---

# Code Graph Analysis

Understand codebase structure and change impact through graph analysis.

## Quick Start

```bash
# Blast-radius of recent changes
./scripts/blast-radius.sh

# Blast-radius of specific files
./scripts/blast-radius.sh src/auth.py src/middleware.py

# Find hub and bridge nodes
./scripts/hub-detect.sh
./scripts/hub-detect.sh src/
```

## Decision Tree

```
SITUATION?
├─ Reviewing a PR / changed files
│  ├─ Run: ./scripts/blast-radius.sh
│  ├─ Check RISK LEVEL in output
│  │  ├─ CRITICAL/HIGH → read ALL files in blast radius
│  │  ├─ MEDIUM → read changed files + direct callers
│  │  └─ LOW → read changed files only
│  └─ Check test coverage → flag gaps
├─ Understanding architecture
│  ├─ Run: ./scripts/hub-detect.sh
│  ├─ Hubs = most important files (change carefully)
│  ├─ Bridges = cross-module connectors (test thoroughly)
│  └─ Use with visualize-code workflow for auto-diagram
├─ Planning a refactor
│  ├─ Run hub-detect.sh → identify files you'll affect
│  ├─ Run blast-radius.sh on files you plan to change
│  └─ If blast-radius > 50 → warn user, suggest incremental approach
└─ Reference needed
   └─ Read: references/blast-radius.md
```

## Risk Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **CRITICAL** | High-risk code + 50+ callers | Full review of entire blast radius |
| **HIGH** | High-risk code OR 50+ callers | Review changed + callers + tests |
| **MEDIUM** | Medium-risk OR 10+ callers OR no test coverage | Review changed + direct callers |
| **LOW** | Low-risk, small blast radius, has tests | Review changed files only |

## High-Risk Patterns

These file paths/content patterns elevate risk automatically:
`auth`, `crypto`, `password`, `token`, `secret`, `validation`, `permission`, `access`

## References

| Reference | Purpose |
|-----------|---------|
| `blast-radius.md` | Full methodology: tracing, risk scoring, hub/bridge theory |
```