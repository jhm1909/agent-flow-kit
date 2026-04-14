# Blast-Radius Analysis Reference

> Source: [code-graph](https://github.com/tirth8205/code-graph) — curated, MCP dependency removed.

## Core Concept

Instead of reading the entire codebase, trace the **blast radius** of changed files. This reduces token usage by 4-27x while maintaining recall on impacted files.

```
Changed File → Direct Callers → Transitive Dependents → Affected Tests
                    ↓
              "Blast Radius" = minimal set of files to review
```

## Tracing Steps

1. **Identify changed files** — `git diff --name-only` or user-specified
2. **Trace direct callers** — files that import/require the changed file
3. **Trace transitive dependents** — files that import the direct callers (1 level)
4. **Find affected tests** — test files that reference changed code
5. **Score risk** — combine blast radius + change type + test coverage

## Risk Scoring Model

| Factor | Weight | Scoring |
|--------|--------|---------|
| **Change type** | HIGH | Auth/crypto/validation = critical; Logic = medium; UI/docs = low |
| **Blast radius** | HIGH | 50+ callers = critical; 10-50 = medium; <10 = low |
| **Test coverage** | MEDIUM | No tests on changed code = elevated risk |
| **Hub score** | MEDIUM | Most-connected node changed = elevated risk |
| **Bridge score** | LOW | Chokepoint node changed = architectural concern |

### Risk Classification

```
CRITICAL = (change_type=HIGH) AND (blast_radius > 50 OR hub_score > 0.8)
HIGH     = (change_type=HIGH) OR (blast_radius > 50)
MEDIUM   = (change_type=MEDIUM) OR (blast_radius > 10)
LOW      = everything else
```

No test coverage elevates LOW → MEDIUM.

## Hub Nodes (Architectural Hotspots)

- Files with most import references from other files
- Changes to hubs affect many dependents → higher review priority
- Common hubs: utility modules, shared services, base classes, config files

## Bridge Nodes (Chokepoints)

- Files that connect otherwise separate code directories
- Changes to bridges can break cross-module contracts
- Common bridges: adapter layers, API clients, shared types

## Token-Efficient Review Strategy

1. Run `blast-radius.sh` → get prioritized file list
2. Agent reads files in priority order: CHANGED → CALLER → TEST → TRANSITIVE
3. Stop when risk is understood — don't read LOW-priority files unless needed
4. Target: agent reads ≤20 files per review, even in large codebases

## Cross-Community Surprise Detection

Flag unexpected connections:
- File in `src/auth/` imported by `src/ui/` → surprising cross-concern
- Test file importing production code from unrelated module
- Circular dependencies between directories
