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

## Confirm before assuming

- Diagram style not specified → auto-detect + ask user to confirm
- Diagram type ambiguous → ask, don't guess
- Blast radius > 50 files → warn user: "Large scope, review may miss issues"
- Risk level HIGH/CRITICAL → alert user before deep review

## Error protocol (3-strike rule)

1. **First error**: analyze root cause, fix the specific issue, retry
2. **Second error**: switch method entirely (different script, different approach)
3. **Third error**: **STOP.** Report error to user. Do NOT retry blindly.

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
