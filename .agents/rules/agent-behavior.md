---
type: always
---

# Agent Flow Kit Rules

These constraints apply to ALL skills and workflows in this toolkit.

## Match the user's language

Detect the language of the user's message and respond in that **same language**. This applies to ALL agent output: clarifying questions, multiple-choice options, progress updates, error messages, and final delivery summaries.

- User writes in Vietnamese → respond in Vietnamese
- User writes in English → respond in English
- User writes in Japanese → respond in Japanese
- Mixed languages → use the dominant language of the message
- Code, file paths, CLI commands, and technical terms (e.g., "flowchart", "architecture", "SVG") stay in English regardless of response language

## ⛔ Never write SVG directly

You are **FORBIDDEN** from generating SVG markup yourself. All SVG output **MUST** be produced by running one of these scripts:
- `svg-gen.py` — simple diagrams with auto-layout
- `generate-from-template.py` — complex diagrams with containers/routing

**Why**: AI-generated SVG consistently produces overlapping nodes, missing edges, broken layouts, and incorrect coordinates. The scripts have built-in layout engines (Sugiyama, orthogonal routing) that prevent these issues.

**What to do instead**: Build the JSON input → save to temp file → run the script → validate output.

If you catch yourself writing `<svg>`, `<rect>`, `<path>`, `<line>`, or any SVG tag directly — **STOP IMMEDIATELY** and use the scripts instead.

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

## ⛔ Ask before acting on vague requests (HARD GATE)

**BEFORE generating any diagram, code review, or visualization — STOP and evaluate:**

1. Did the user provide a clear **subject** with named components? If NO → **ASK**
2. Is the **type** explicit (flowchart, architecture, sequence)? If NO → **ASK**
3. Did the user name **≥3 specific components**? If NO → **ASK**
4. Is the **purpose** clear (docs, slides, README)? If NO → **ASK**

**If ANY answer is NO → you MUST ask the user before doing anything else.**

⛔ Do NOT infer missing information yourself. Do NOT fill in defaults silently. Do NOT assume you know what they want. The user's explicit input is the ONLY source of truth.

Combine all missing items into **ONE question**. After user responds, if partially missing → state assumptions explicitly and ask to confirm.

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
