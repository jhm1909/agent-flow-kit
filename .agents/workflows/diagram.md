---
description: Orchestrates diagram generation from text description to validated SVG output. Guides the agent through classification, structure extraction, style selection, generation, and quality validation.
---

# Diagram Generation Workflow

> **Execution context:** All script paths are relative to the `.agents/` root directory.

---

## Step 0: Evaluate Request Completeness

// turbo

Before doing any work, score the user's request against these 4 dimensions:

| Dimension | Sufficient | Insufficient (must ask) |
|-----------|-----------|------------------------|
| **Subject** | Clear topic with named components ("RAG pipeline with Pinecone and GPT-4") | Vague topic ("draw a diagram", "visualize authentication") |
| **Type** | Explicit or unambiguously inferable ("flowchart of login process") | Ambiguous — could be multiple types ("diagram of our system") |
| **Components** | At least 3 named nodes/actors/services | No components mentioned, or only 1-2 generic ones |
| **Purpose** | Stated or inferable audience/use (docs, slides, README, internal) | No context for who will see this or where it will be used |

**Style** is optional — auto-detect works well. Only ask if the user seems to care about visual presentation.

### Decision logic

- **All 4 sufficient** → proceed to Step 1
- **1-2 insufficient** → ask ONE combined question covering all gaps. Example:

  > "Để tạo diagram chất lượng tốt, tôi cần thêm thông tin:
  > 1. **Loại diagram**: bạn muốn kiến trúc tổng thể hay flowchart quy trình?
  > 2. **Thành phần chính**: những service/component nào cần có trong diagram?
  >
  > (Style tôi sẽ tự chọn phù hợp, bạn có thể điều chỉnh sau.)"

- **3-4 insufficient** → the request is too vague. Ask an open-ended question:

  > "Bạn có thể mô tả thêm hệ thống bạn muốn vẽ không? Ví dụ: gồm những thành phần gì, dữ liệu chạy từ đâu đến đâu, và diagram này dùng cho mục đích gì (docs, slides, README)?"

**Rules**:
- Ask **at most ONE round** of questions — never chain 3-4 rounds of back-and-forth
- Combine all missing items into a single, clear message
- If the user answers partially, fill in reasonable defaults for the rest and confirm
- **NEVER** proceed to generation with insufficient information — low-quality input = low-quality output

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

1. **Invoke `[diagram]` skill** — save JSON to temp file:
   ```bash
   mkdir -p .agents-output/diagram/tmp .agents-output/diagram/svg
   # Write JSON to .agents-output/diagram/tmp/input.json
   ```

2. **Choose a descriptive filename** based on diagram content (e.g., `auth-flow.svg`, `rag-pipeline.svg`, `payment-sequence.svg`). Never use generic names like `output.svg` or `diagram.svg`.

3. Choose generator based on complexity:
   - **6+ nodes, containers, swim lanes** → use `generate-from-template.py`:
     ```bash
     python3 skills/diagram/scripts/generate-from-template.py <type> <descriptive-name>.svg -i .agents-output/diagram/tmp/input.json
     ```
   - **≤5 nodes, simple structure** → use `svg-gen.py`:
     ```bash
     cat .agents-output/diagram/tmp/input.json | python3 skills/diagram/scripts/svg-gen.py -o <descriptive-name>.svg --style <style>
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
