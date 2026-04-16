---
type: always
---

# Agent Flow Kit Rules

These constraints apply to ALL skills and workflows in this toolkit.

## Think before acting

- **Classify first**: identify the diagram type or review scope BEFORE generating anything.
- **Pre-generation checklist**: Can I write the complete JSON/command? Do I have all data? If NO → prepare first, do NOT call a script empty.
- **Choose the right tool**: complex diagrams → `generate-from-template.py`; simple → `svg-gen.py`; quick review → `blast-radius.sh`; deep review → full workflow.

## Validate before delivering

### Diagrams
- **Level 1**: XML validity — run `validate-svg.sh`
- **Level 2**: Visual correctness — no overlap, text fits, arrows connect, legend present
- **Level 3**: Semantic — consistent shapes, clear flow direction, meaningful labels

### Code reviews
- **Risk drives depth**: LOW → skim changed files; MEDIUM → read callers; HIGH → read blast radius
- **Always check**: test coverage gaps, security patterns removed, breaking API changes

## Ask before acting on vague requests

Before generating any diagram, evaluate if the request has enough information:
- **Subject** clear with named components? If not → ask
- **Diagram type** explicit or unambiguously inferable? If not → ask
- **Components** — at least 3 named nodes/services? If not → ask
- **Purpose** — who will see this, where will it be used? If not → ask

Combine all missing items into **ONE question** — never chain multiple rounds. If the user answers partially, fill in reasonable defaults and confirm.

**NEVER proceed to generation with insufficient information.** Low-quality input = low-quality output.

## Confirm before assuming

- Diagram style not specified → auto-detect + ask user to confirm
- Diagram type ambiguous → ask, don't guess
- Blast radius > 50 files → warn user: "Large scope, review may miss issues"
- Risk level HIGH/CRITICAL → alert user before deep review

## Error protocol (3-strike rule)

1. **First error**: analyze root cause, fix the specific issue, retry
2. **Second error**: switch method entirely (different script, different approach)
3. **Third error**: **STOP.** Report error to user. Do NOT retry blindly.

## Name output files descriptively

- **Diagrams**: name after diagram content — `auth-flow.svg`, `rag-pipeline.svg`, `payment-sequence.svg`
- **Architecture**: name after project or scope — `myapp-architecture.svg`, `backend-modules.svg`
- **Reports**: name after analysis type — `blast-radius-auth.json`, `hub-detect-api.json`
- **Never** use generic names like `output.svg`, `diagram.svg`, `result.json`
- Scripts auto-append counters (`_1`, `_2`, ...) if a file with the same name exists — previous outputs are never overwritten

## Output to .agents-output/

**Never** write output files inside `.agents/`. This directory is configuration only.

```
.agents-output/
├── diagram/
│   ├── svg/        ← SVG output
│   ├── png/        ← PNG export
│   └── tmp/        ← JSON input files
├── code-graph/
│   ├── reports/    ← blast-radius, hub-detect JSON output
│   └── tmp/        ← temporary data
└── visualize/
    ├── svg/        ← architecture diagrams
    └── tmp/        ← intermediate JSON
```

Create subdirectories with `mkdir -p` before writing. If user specifies an absolute path, respect it.

## Keep output concise

- Deliver: file path + one-line summary
- Reports: structured format with severity levels
- Clean up temporary files after use
