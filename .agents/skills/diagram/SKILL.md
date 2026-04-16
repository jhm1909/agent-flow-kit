---
name: diagram
description: >-
  Generates production-quality SVG technical diagrams from text descriptions.
  Use when asked to create, draw, visualize, or illustrate any technical diagram —
  architecture, flowchart, sequence, agent system, data flow, ER, UML, mind map,
  network topology, or comparison matrix.
---

# Diagram

> **Execution context:** Script paths are relative to this skill directory (`.agents/skills/diagram/`).

Generate production-quality SVG diagrams from natural language descriptions.

## When to use this skill

- User says "draw", "diagram", "visualize", "illustrate", "architecture diagram"
- Need to show system architecture, data flow, agent pipelines, or process flows
- Converting text descriptions into technical diagrams for docs, slides, or READMEs
- User describes a system and wants a visual representation

## Mandatory Workflow (Always Follow This Order)

```
0. EVALUATE  → Is the request complete enough to produce a quality diagram?
1. CLASSIFY  → What type of diagram?
2. EXTRACT   → Identify layers, nodes, edges, flows, groups
3. MAP       → Assign semantic shapes + arrow types
4. STYLE     → Choose visual style (or auto-detect + confirm)
5. GENERATE  → Build JSON → run script → SVG
6. VALIDATE  → Check quality (not just XML validity)
7. DELIVER   → File path + summary
```

**Pre-generation checklist** — MUST pass before calling any script:
- [ ] Did Step 0 pass? (user provided sufficient info, or answered clarifying questions)
- [ ] Can I write the COMPLETE JSON using ONLY what the user told me?
- [ ] Do I have ALL nodes, edges, and containers identified FROM USER INPUT?
- [ ] Have I mapped each concept to the correct shape?
**If ANY is NO → STOP. Go back to Step 0 or prepare first. Do NOT generate with self-inferred data.**

---

## Step 0: Evaluate Request Completeness (HARD GATE)

⛔ **THIS STEP IS MANDATORY. You are FORBIDDEN from skipping to Step 1 without completing this evaluation.**

⛔ **DO NOT fill in missing information yourself. DO NOT infer components the user didn't mention. DO NOT assume you know what they want. ASK THEM.**

Before any work — before classifying, before thinking about JSON, before touching any script — you MUST score the request:

| Dimension | ✅ PASS (user explicitly provided) | ❌ FAIL (must ask user) |
|-----------|-----------|------------------------|
| **Subject** | Named system/process ("RAG pipeline", "OAuth login flow") | Vague ("draw a diagram", "visualize auth", "diagram for my project") |
| **Type** | Explicit type or unambiguous ("flowchart of X", "sequence diagram for Y") | Generic ("diagram of...", "visualize...") |
| **Components** | ≥3 specific named nodes/services/actors by the user | User named 0-2 components, or only generic terms ("frontend", "backend") |
| **Purpose** | User stated where/how it will be used | No context |

### Scoring — output this table before proceeding:

```
Subject:    ✅ or ❌ — [reason]
Type:       ✅ or ❌ — [reason]
Components: ✅ or ❌ — [reason]
Purpose:    ✅ or ❌ — [reason]
→ Result:   PASS / ASK
```

### Decision:

- **All ✅** → proceed to Step 1
- **Any ❌** → you MUST ask the user. **STOP HERE. Do not proceed.**

Combine all ❌ items into **ONE message** with **multiple-choice options** for each gap.

### How to ask — multiple-choice format

For each missing dimension, provide **concrete options (A/B/C/D)** based on context clues from the user's request. Always include a free-form option so the user can specify something different.

**Example** — user says "draw a diagram of authentication":

> I need a bit more info to create a quality diagram:
>
> **1. Diagram type:**
> - A) Architecture — show how auth components connect
> - B) Flowchart — show the step-by-step login/signup process
> - C) Sequence — show message flow between client, server, and identity provider
> - D) Something else (please describe)
>
> **2. Key components** — which ones should be in the diagram?
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
> Pick a letter for each, or describe your own. You can mix — e.g., "1B, 2C, 3A".

### Rules for crafting options:
- **Options MUST be context-aware** — infer from the user's topic, not generic. If user says "payment system", suggest payment-related components, not auth components.
- **Number of options is flexible** — use as many or as few as make sense (2–6+). Don't force exactly 4 if only 2 are meaningful, and don't limit to 4 if 6 good options exist.
- **Order by complexity** — simplest first, most detailed last
- **Always include one free-form option** as the last choice ("Something else / Custom")
- User can **mix and modify**: "1B, but add Redis for session caching"
- After user picks, if minor gaps remain → state assumptions and proceed (no second round of questions)
- **Style** is the ONLY dimension you may auto-detect without asking

### What counts as "sufficient" — be strict:
- ❌ "draw a diagram of authentication" → no type, no components, no purpose → ASK with options
- ❌ "diagram for my system" → everything missing → ASK with options
- ❌ "draw backend architecture" → has type, but no components named → ASK with options
- ✅ "draw a login flowchart: user enters credentials → validate → check 2FA → OTP → success" → all clear, proceed

---

## Step 1: Classify Diagram Type

Match user description to the closest type:

| If user describes... | → Diagram Type |
|---|---|
| Microservices, API gateways, layers of services | **Architecture** |
| Data transformations, queries, embeddings, ETL | **Data Flow** |
| Steps, decisions, if/then, sequential processes | **Flowchart** |
| LLM reasoning, tools, memory, agent loops | **Agent Architecture** |
| Memory tiers, retrieval, storage (Mem0, MemGPT) | **Memory Architecture** |
| Time-ordered messages, API calls between systems | **Sequence** |
| Comparing systems/features side-by-side | **Comparison Matrix** |
| Phases, milestones, project timeline | **Timeline** |
| Central concept with radiating branches | **Mind Map** |
| Classes, attributes, inheritance, interfaces | **UML Class** |
| Users, system boundary, use cases | **UML Use Case** |
| States, transitions, lifecycle | **State Machine** |
| Tables, keys, relationships (DB schema) | **ER Diagram** |
| Routers, servers, firewalls, network zones | **Network Topology** |

**If ambiguous → ASK the user.** Do not guess.

---

## Step 2: Extract Structure

From the user's description, identify:

1. **Nodes** — each distinct component, service, or concept
2. **Edges** — relationships, data flows, control signals between nodes
3. **Containers** — logical groups (layers, modules, swim lanes)
4. **Direction** — top-down (most common), left-right, or radial

**AI/Agent domain patterns** — recognize and apply automatically:

```
RAG Pipeline       → Query → Embed → VectorSearch → Retrieve → LLM → Response
Agentic RAG        → adds Agent loop + Tool use around RAG
Agentic Search     → Query → Planner → [Search/Calc/Code] → Synthesizer
Memory Layer       → Input → Memory Manager → [VectorDB + GraphDB] → Context
Agent Memory Types → Sensory → Working → Episodic → Semantic → Procedural
Multi-Agent        → Orchestrator → [SubAgent×N] → Aggregator → Output
Tool Call Flow     → LLM → Tool Selector → Execution → Parser → LLM (loop)
```

When user describes one of these patterns, use the canonical structure above as a starting point.

---

## Step 3: Map to Shapes and Arrows

### Shapes (semantic mapping — MUST be consistent)

| Concept | Shape | JSON kind/shape |
|---------|-------|-----------------|
| User / Human | Stick figure or rect | `user_avatar` / `rect` |
| LLM / Model | Double-border rounded rect | `double_rect` / `llm` |
| Agent / Orchestrator | Hexagon | `hexagon` / `agent` |
| Database / Persistent storage | Cylinder | `cylinder` / `database` |
| Vector Store | Cylinder with inner lines | `cylinder` |
| Short-term memory | Dashed rounded rect | `memory` |
| Tool / Function | Rectangle with gear | `rect` |
| API / Gateway | Hexagon | `hexagon` |
| Decision point | Diamond | `diamond` / `decision` |
| Document / File | Folded-corner rect | `document` |

**Rule**: Same concept MUST use same shape throughout the diagram.

### Arrow types (semantic — MUST match the relationship)

| Relationship | Arrow type | Color |
|---|---|---|
| Main data flow (request/response) | `primary` | Blue |
| Control signal (triggers action) | `control` | Orange |
| Memory read (retrieve) | `read` | Green solid |
| Memory write (store) | `write` | Green dashed |
| Async / event / non-blocking | `async` | Gray dashed |
| Feedback / iterative loop | `feedback` | Purple |

**Rule**: If 2+ arrow types exist → MUST include a legend.

For full shape/arrow reference: [tech-diagram.md](references/tech-diagram.md)

---

## Step 4: Choose Visual Style

**If user specified a style** → use it.

**If not** → auto-detect based on context, then **confirm with user**:

| Context | → Style | `--style` value |
|---|---|---|
| Documentation, blog, slides | Flat Icon | `flat-icon` |
| GitHub README, dark theme | Dark Terminal | `dark-terminal` |
| Engineering/infra docs | Blueprint | `blueprint` |
| Notion, wiki, minimal | Notion Clean | `notion-clean` |
| Product site, keynote | Glassmorphism | `glassmorphism` |
| AI/agent topic, professional | Claude Official | `claude-official` |
| Clean modern, minimalist | OpenAI Official | `openai-official` |

**Always confirm**: "I'll use [style] because [reason]. OK?"

For style-to-diagram-type best matches: [style-diagram-matrix.md](references/style-diagram-matrix.md)
For exact style specs (colors, fonts, effects): `references/style-N-*.md`

---

## Step 5: Generate SVG

### Choose the right script

| Diagram complexity | Script | Why |
|---|---|---|
| **Complex**: containers, swim lanes, port routing, 6+ nodes | `generate-from-template.py` | Full routing, collision avoidance |
| **Simple**: just nodes + edges, ≤5 nodes | `svg-gen.py` | Fast, auto-layout via Sugiyama |

### Generation process

1. **Save JSON to file** (avoids shell escaping issues on Windows):
   ```bash
   mkdir -p .agents-output/diagram/tmp
   # Write your JSON to:
   .agents-output/diagram/tmp/input.json
   ```

2. **Choose a descriptive filename** based on diagram content (e.g., `auth-flow.svg`, `rag-pipeline.svg`). Never use generic names like `output.svg`.

3. **Run the script**:
   ```bash
   # Complex diagrams
   python3 scripts/generate-from-template.py <type> <descriptive-name>.svg -i .agents-output/diagram/tmp/input.json

   # Simple diagrams (auto-layout)
   cat .agents-output/diagram/tmp/input.json | python3 scripts/svg-gen.py -o <descriptive-name>.svg --style <style>
   ```

4. Output goes to `.agents-output/diagram/svg/` automatically. If a file with the same name exists, a counter is appended (`_1`, `_2`, ...) — previous diagrams are never overwritten.

### JSON format

See `resources/` for 7 complete examples. Key fields:

**Nodes**: `id`, `label`, `kind`/`shape`, `x`, `y` (optional — auto-layout if omitted), `width`, `height`
**Edges**: `from`/`source`, `to`/`target`, `type`/`flow`, `label`
**Containers**: `id`, `label`, `x`, `y`, `width`, `height`, `stroke`, `fill`

---

## Step 6: Validate Quality

### Level 1: XML validity
```bash
bash scripts/validate-svg.sh .agents-output/diagram/svg/<descriptive-name>.svg
```

### Level 2: Visual correctness (check manually)

- [ ] **No node overlap** — all nodes clearly separated (80px+ gaps)
- [ ] **No text overflow** — labels fit inside shapes (text length × 7px ≤ shape width - 16px)
- [ ] **Arrows connect to edges** — endpoints touch node boundaries, not floating
- [ ] **Arrow labels readable** — each label has background rect, not overlapping
- [ ] **Consistent shapes** — same concept uses same shape everywhere
- [ ] **Legend present** — if 2+ arrow types used, legend exists
- [ ] **Containers enclose** — swim lanes contain their nodes, no escapees

### Level 3: Semantic check

- [ ] **Flow direction clear** — reader can follow the flow top→bottom or left→right
- [ ] **No orphan nodes** — every node has at least 1 connection (unless intentional)
- [ ] **Meaningful labels** — no "Node 1", "Process 2"; use real names

---

## Step 7: Error Handling

- **First error**: Analyze root cause, fix the specific issue (missing tag, wrong attribute), regenerate
- **Second error**: Switch method (if using svg-gen.py → switch to generate-from-template.py, or vice versa)
- **Third error**: **STOP.** Report to user with the error message. Do NOT retry blindly.

---

## Available Scripts

| Script | Purpose | Run with `--help` |
|--------|---------|-------------------|
| `scripts/generate-from-template.py` | Full-featured: containers, ports, routing | `python3 scripts/generate-from-template.py --help` |
| `scripts/svg-gen.py` | Lightweight: auto-layout via Sugiyama engine | `python3 scripts/svg-gen.py --help` |
| `scripts/validate-svg.sh` | XML validation + structural checks | `bash scripts/validate-svg.sh --help` |
| `scripts/generate-diagram.sh` | End-to-end: generate + validate + export | `bash scripts/generate-diagram.sh --help` |
| `scripts/test-all-styles.sh` | Regression test all 7 styles | `bash scripts/test-all-styles.sh` |

## Unsupported Requests

If user asks for something not supported, respond honestly:

| Request | Response |
|---------|----------|
| Gantt chart | "Timeline diagram is the closest. Want me to use that?" |
| Pie chart / bar chart | "This toolkit generates structural diagrams, not data charts. Use matplotlib/d3.js instead." |
| Interactive diagram | "SVG is static. For interactive, consider D3.js or Mermaid.js." |
| Photo-realistic | "This generates vector diagrams with flat/clean styles, not photorealistic images." |

## Resources & References

| Resource | Load when |
|----------|-----------|
| [json-schema.md](references/json-schema.md) | **FIRST**: complete field reference, required/optional, common mistakes |
| `resources/*.json` | Need JSON format examples (7 fixtures, one per style) |
| `resources/templates/*.svg` | Need SVG template skeletons (10 diagram types) |
| [tech-diagram.md](references/tech-diagram.md) | Need full shape vocabulary, arrow semantics, AI domain patterns |
| [style-diagram-matrix.md](references/style-diagram-matrix.md) | Choosing which style fits which diagram type |
| [style-N-*.md](references/) | Need exact colors, fonts, effects for a specific style |
| [svg-layout-best-practices.md](references/svg-layout-best-practices.md) | Layout spacing rules, arrow routing, collision avoidance |
| [icons.md](references/icons.md) | Need product brand icons (40+ with hex colors) |
