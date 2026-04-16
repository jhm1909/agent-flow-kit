---
description: Orchestrates diagram generation from text description to validated SVG output. Guides the agent through classification, structure extraction, style selection, generation, and quality validation.
---

# Diagram Generation Workflow

> **Execution context:** All script paths are relative to the `.agents/` root directory.

---

## Step 0: Evaluate Request Completeness (HARD GATE)

// turbo

⛔ **MANDATORY. Do NOT skip. Do NOT jump to classification or JSON generation.**

⛔ **Do NOT fill in missing info yourself. Do NOT infer what the user didn't say. ASK THEM.**

Score the user's request — output this evaluation visibly:

```
Subject:    ✅ or ❌ — [what user said or didn't say]
Type:       ✅ or ❌ — [what user said or didn't say]
Components: ✅ or ❌ — [what user said or didn't say]
Purpose:    ✅ or ❌ — [what user said or didn't say]
→ Result:   PASS / ASK
```

| Dimension | ✅ PASS | ❌ FAIL (must ask) |
|-----------|---------|-------------------|
| **Subject** | Named system/process ("RAG pipeline", "OAuth flow") | Vague ("draw a diagram", "visualize auth") |
| **Type** | Explicit or unambiguous ("flowchart of X") | Generic ("diagram of...") |
| **Components** | ≥3 specific named nodes/services | 0-2 components or only generic terms |
| **Purpose** | User stated audience/use | No context |

### If ANY dimension is ❌ → STOP. Ask ONE combined question with multiple-choice options. Do NOT proceed.

For each missing dimension, provide **concrete options (A/B/C/D)** based on context clues from the user's request. Always include a free-form option (D).

**Example** — user says "draw a diagram of authentication":

> I need a bit more info to create a quality diagram:
>
> **1. Diagram type:**
> - A) Architecture — show how auth components connect
> - B) Flowchart — show the step-by-step login/signup process
> - C) Sequence — show message flow between client, server, and identity provider
> - D) Something else (please describe)
>
> **2. Key components:**
> - A) Basic: User → Login Form → Auth Server → Database
> - B) OAuth: User → App → OAuth Provider → Token → API
> - C) Full stack: Client → API Gateway → Auth Service → JWT → Session Store → Database
> - D) Custom (please list your components)
>
> **3. Purpose:**
> - A) Technical docs / README
> - B) Presentation / slides
> - C) Internal team reference
> - D) Other
>
> Pick a letter for each, or describe your own — e.g., "1B, 2C, 3A".

### Rules:
- **Options MUST be context-aware** — tailor to the user's topic, not generic
- **Number of options is flexible** — 2–6+ per question, as many as make sense. Don't force 4 if only 2 are meaningful.
- Order by complexity — simplest first, most detailed last. Always end with a free-form option.
- User can mix and modify: "1B, but add Redis for caching"
- **ONE round** of questions max — after user picks, proceed
- **Style** is the ONLY thing you may auto-detect

### Examples — be strict:
- ❌ "draw a diagram of authentication" → no type, no components, no purpose → ASK with options
- ❌ "draw backend architecture" → no components named → ASK with options
- ✅ "draw a login flowchart: user enters credentials → validate → 2FA → OTP → success" → all clear, proceed

**WAIT** for user response before proceeding.

**Output**: Complete understanding of what to generate

---

## Step 1: Understand & Classify

// turbo

1. **Invoke `[diagram]` skill** to classify the diagram type from the user's description.
2. If the description matches a known AI/agent pattern (RAG, Multi-Agent, Memory Layer, Tool Call), use that pattern as the structural foundation.
3. If the diagram type is ambiguous, present 2-3 options to the user.
4. **WAIT** for user confirmation if type was inferred (not explicitly stated).

**Output**: Diagram type + initial node/edge list (mental model)

---

## Step 2: Extract Structure

// turbo

1. **Invoke `[diagram]` skill** — read [tech-diagram.md](skills/diagram/references/tech-diagram.md) for shape vocabulary.
2. Decompose the description into:
   - **Nodes**: each component with semantic shape (LLM → `llm`, Agent → `hexagon`, DB → `cylinder`)
   - **Edges**: each relationship with arrow type (data → `primary`, control → `control`, memory → `read`/`write`)
   - **Containers**: logical groups if layers/swim-lanes are needed
3. Verify: same concept → same shape throughout. If 2+ arrow types → plan a legend.
4. **WAIT** if structure is complex (6+ nodes) — present the node/edge list to user for confirmation.

**Output**: Complete JSON structure (nodes, edges, containers)

---

## Step 3: Select Visual Style

// turbo

**Skip if**: User already specified a style.

1. **Invoke `[diagram]` skill** — read [style-diagram-matrix.md](skills/diagram/references/style-diagram-matrix.md) for best match.
2. Auto-detect based on context:
   - Documentation/slides → `flat-icon`
   - GitHub/dark theme → `dark-terminal`
   - Engineering/architecture → `blueprint`
   - AI/agent topic → `claude-official`
   - Default → `flat-icon`
3. Present to user: "I'll use **[style name]** because [reason]. OK?"
4. **WAIT** for user confirmation before proceeding.

**Output**: Confirmed style name

---

## Step 4: Generate SVG

// turbo

⛔ **NEVER write SVG markup directly. ALWAYS use the Python scripts.** AI-generated SVG has broken layouts. The scripts have layout engines that handle positioning, routing, and spacing correctly.

1. **Choose a descriptive base name** based on diagram content (e.g., `auth-flow`, `rag-pipeline`, `payment-sequence`). Use this same name for both JSON and SVG files. Never use generic names like `input`, `output`, or `diagram`.

2. **Save JSON to temp file**:
   ```bash
   mkdir -p .agents-output/diagram/tmp .agents-output/diagram/svg
   # Write JSON to .agents-output/diagram/tmp/<descriptive-name>.json
   ```

3. Choose generator based on complexity:
   - **6+ nodes, containers, swim lanes** → use `generate-from-template.py`:
     ```bash
     python3 skills/diagram/scripts/generate-from-template.py <type> <descriptive-name>.svg -i .agents-output/diagram/tmp/<descriptive-name>.json
     ```
   - **≤5 nodes, simple structure** → use `svg-gen.py`:
     ```bash
     cat .agents-output/diagram/tmp/<descriptive-name>.json | python3 skills/diagram/scripts/svg-gen.py -o <descriptive-name>.svg --style <style>
     ```

4. Check exit code — 0 = success.

**Output**: SVG file in `.agents-output/diagram/svg/`

> **Note**: Scripts automatically append a counter (`_1`, `_2`, ...) if a file with the same name already exists — previous diagrams are never overwritten.

---

## Step 5: Validate Quality

// turbo

1. **Level 1 — XML validity**:
   ```bash
   bash skills/diagram/scripts/validate-svg.sh .agents-output/diagram/svg/<descriptive-name>.svg
   ```

2. **Level 2 — Visual correctness** (check the generated SVG):
   - No node overlap (80px+ gaps)
   - Text fits inside shapes
   - Arrows connect to node edges (not floating)
   - Arrow labels have background rects
   - Legend present if 2+ arrow types

3. **If validation fails**:
   - First failure → analyze error, fix JSON, regenerate (return to Step 4)
   - Second failure → switch generator (svg-gen.py ↔ generate-from-template.py)
   - Third failure → **STOP.** Show error to user. Do NOT retry blindly.

**Output**: Validated SVG

---

## Step 6: Deliver

// turbo

1. Present the SVG file path to user.
2. Summarize: "Created a [type] diagram with [N] nodes in [style] style."
3. **WAIT** — ask: "Want to adjust anything? (layout, style, labels, add nodes)"

---

## Quick Reference

| Step | Skill | Output |
|------|-------|--------|
| 0 | — | Evaluate request completeness, ask if needed |
| 1 | diagram | Diagram type classification |
| 2 | diagram | JSON structure (nodes, edges, containers) |
| 3 | diagram | Confirmed visual style |
| 4 | diagram | SVG file |
| 5 | diagram | Validated SVG |
| 6 | — | Delivery + iteration offer |
