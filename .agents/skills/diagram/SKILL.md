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
1. CLASSIFY → What type of diagram?
2. EXTRACT  → Identify layers, nodes, edges, flows, groups
3. MAP      → Assign semantic shapes + arrow types
4. STYLE    → Choose visual style (or auto-detect + confirm)
5. GENERATE → Build JSON → run script → SVG
6. VALIDATE → Check quality (not just XML validity)
7. DELIVER  → File path + summary
```

**Pre-generation checklist** — MUST pass before calling any script:
- [ ] Can I write the COMPLETE JSON right now?
- [ ] Do I have ALL nodes, edges, and containers identified?
- [ ] Have I mapped each concept to the correct shape?
**If ANY is NO → STOP. Prepare first. Do NOT call a script with incomplete data.**

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

2. **Run the script**:
   ```bash
   # Complex diagrams
   python3 scripts/generate-from-template.py <type> output.svg -i .agents-output/diagram/tmp/input.json

   # Simple diagrams (auto-layout)
   cat .agents-output/diagram/tmp/input.json | python3 scripts/svg-gen.py -o output.svg --style <style>
   ```

3. Output goes to `.agents-output/diagram/svg/` automatically.

### JSON format

See `resources/` for 7 complete examples. Key fields:

**Nodes**: `id`, `label`, `kind`/`shape`, `x`, `y` (optional — auto-layout if omitted), `width`, `height`
**Edges**: `from`/`source`, `to`/`target`, `type`/`flow`, `label`
**Containers**: `id`, `label`, `x`, `y`, `width`, `height`, `stroke`, `fill`

---

## Step 6: Validate Quality

### Level 1: XML validity
```bash
bash scripts/validate-svg.sh .agents-output/diagram/svg/output.svg
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

## Resources & References

| Resource | Load when |
|----------|-----------|
| `resources/*.json` | Need JSON format examples (7 fixtures, one per style) |
| `resources/templates/*.svg` | Need SVG template skeletons (10 diagram types) |
| [tech-diagram.md](references/tech-diagram.md) | Need full shape vocabulary, arrow semantics, AI domain patterns |
| [style-diagram-matrix.md](references/style-diagram-matrix.md) | Choosing which style fits which diagram type |
| [style-N-*.md](references/) | Need exact colors, fonts, effects for a specific style |
| [svg-layout-best-practices.md](references/svg-layout-best-practices.md) | Layout spacing rules, arrow routing, collision avoidance |
| [icons.md](references/icons.md) | Need product brand icons (40+ with hex colors) |
