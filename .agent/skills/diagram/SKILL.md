---
name: diagram
description: >
  Generate production-quality SVG/PNG diagrams from text descriptions.
  Supports architecture, flowchart, sequence, agent, UML, ER, and mind map diagrams.
  7 visual styles, 13 semantic shapes, 6 arrow types.
metadata:
  version: "1.0.0"
  sources:
    - fireworks-tech-graph (shape vocabulary, arrow semantics, visual styles)
---

# Diagram Generator

Create SVG diagrams from natural language descriptions.

## Quick Start

```bash
# Generate from JSON
echo '{"nodes":[...], "edges":[...]}' | python3 scripts/svg-gen.py -o diagram.svg --style flat-icon

# Validate existing SVG
python3 scripts/svg-gen.py --validate-only -o diagram.svg
```

## Decision Tree

```
USER REQUEST?
├─ Describe a diagram
│  ├─ Classify type (see Diagram Types below)
│  ├─ Extract nodes, edges, layers from description
│  ├─ Style specified?
│  │  ├─ Yes → use it
│  │  └─ No → Auto-detect:
│  │     ├─ README/docs context → flat-icon
│  │     ├─ .github/ or dark theme → dark-terminal
│  │     ├─ "architecture"/"infra" → blueprint
│  │     ├─ "agent"/"LLM"/"AI" → claude-official
│  │     └─ default → flat-icon
│  │     └─ Confirm with user: "Using [style] because [reason]. OK?"
│  ├─ Build JSON input
│  ├─ Run: python3 scripts/svg-gen.py -i input.json -o output.svg --style <style>
│  └─ Validate → deliver
├─ Fix/modify existing diagram
│  ├─ Read existing JSON or describe changes
│  └─ Re-generate with svg-gen.py
└─ Reference needed
   └─ Read: references/tech-diagram.md
```

## Diagram Types

| Type | Layout | Use When |
|------|--------|----------|
| Architecture | Horizontal layers top→bottom | System overview, service map |
| Flowchart | Top-to-bottom, diamond=decision | Process, logic flow |
| Sequence | Vertical lifelines, horizontal messages | API calls, request flow |
| Agent Architecture | 5-layer: Input/Agent/Memory/Tool/Output | AI agent systems |
| Data Flow | Label every arrow with data type | ETL, pipeline |
| Mind Map | Radial from center | Brainstorming, concept mapping |
| UML Class | 3-compartment rect | Object model |
| ER Diagram | Entity rects with PK/FK | Database schema |

## Shapes

| Concept | Shape | JSON `shape` value |
|---------|-------|--------------------|
| User/Human | Rectangle | `rect` |
| LLM/Model | Double-border rounded rect | `llm` |
| Agent/Orchestrator | Hexagon | `agent` |
| Database/Long-term memory | Cylinder | `database` |
| Short-term memory | Rounded rect | `rounded-rect` |
| Tool/Function | Rectangle | `rect` |
| API/Gateway | Hexagon | `hexagon` |
| Decision | Diamond | `decision` |

## Arrow Types

| Type | Color | Meaning | JSON `type` value |
|------|-------|---------|-------------------|
| Primary data | Blue `#2563eb` | Main request/response | `primary` |
| Control/trigger | Orange `#ea580c` | System triggers | `control` |
| Memory read | Green solid | Retrieve from store | `read` |
| Memory write | Green dashed | Write to store | `write` |
| Async/event | Gray dashed | Non-blocking | `async` |
| Feedback/loop | Purple | Iterative | `feedback` |

## Styles

| Style | Best For | `--style` value |
|-------|----------|-----------------|
| Flat Icon (default) | Blogs, slides, docs | `flat-icon` |
| Dark Terminal | GitHub README, dev articles | `dark-terminal` |
| Blueprint | Architecture docs | `blueprint` |
| Notion Clean | Notion, wikis | `notion-clean` |
| Glassmorphism | Product sites, keynotes | `glassmorphism` |
| Claude Official | Professional | `claude-official` |
| OpenAI Official | Clean modern | `openai-official` |

## JSON Input Format

```json
{
  "title": "My Diagram",
  "nodes": [
    {"id": "unique_id", "label": "Display Name", "shape": "rect", "layer": 0},
    {"id": "llm", "label": "GPT-4", "shape": "llm", "layer": 1, "width": 160, "height": 64}
  ],
  "edges": [
    {"from": "unique_id", "to": "llm", "type": "primary", "label": "query"}
  ]
}
```

Node fields: `id` (required), `label`, `shape`, `layer` (vertical position), `width`, `height`
Edge fields: `from`, `to` (required), `type`, `label`

## References

| Reference | Purpose |
|-----------|---------|
| `tech-diagram.md` | Full shape vocabulary, arrow semantics, layout rules, AI domain patterns |
