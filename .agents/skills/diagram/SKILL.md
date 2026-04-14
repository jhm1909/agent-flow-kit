---
name: diagram
description: >
  Generate production-quality SVG/PNG diagrams from text descriptions.
  14 diagram types, 7 visual styles, 14+ semantic shapes, 6 arrow types.
  Includes SVG templates, JSON fixtures, container/swim-lane system, and port-based arrow routing.
metadata:
  version: "2.0.0"
  sources:
    - fireworks-tech-graph (full port: templates, fixtures, generator, styles, validation)
---

# Diagram Generator

Create production-quality SVG diagrams from natural language descriptions.

## Quick Start

```bash
# Method 1: Template-based (recommended — full features)
python3 scripts/generate-from-template.py architecture output.svg "$(cat resources/mem0-style1.json)"

# Method 2: JSON pipeline (lightweight)
echo '{"nodes":[...], "edges":[...]}' | python3 scripts/svg-gen.py -o diagram.svg --style flat-icon

# Validate
./scripts/validate-svg.sh output.svg

# Test all styles
./scripts/test-all-styles.sh
```

## Decision Tree

```
USER REQUEST?
├─ Describe a diagram
│  ├─ Classify type (see Diagram Types — 14 types supported)
│  ├─ Choose generation method:
│  │  ├─ Complex (containers, ports, routing) → generate-from-template.py + template + fixture
│  │  └─ Simple (nodes + edges) → svg-gen.py
│  ├─ Extract nodes, edges, containers, layers from description
│  ├─ Style specified?
│  │  ├─ Yes → use it
│  │  └─ No → Auto-detect (see style-diagram-matrix.md for best match):
│  │     ├─ README/docs → flat-icon (Style 1)
│  │     ├─ .github/ or dark theme → dark-terminal (Style 2)
│  │     ├─ "architecture"/"infra" → blueprint (Style 3)
│  │     ├─ "agent"/"LLM"/"AI" → claude-official (Style 6)
│  │     └─ default → flat-icon (Style 1)
│  │     └─ Confirm: "Using [style] because [reason]. OK?"
│  ├─ Build JSON fixture (see resources/ for examples)
│  ├─ Generate SVG
│  ├─ Validate: ./scripts/validate-svg.sh output.svg
│  └─ Deliver
├─ Fix/modify existing diagram
│  ├─ Edit JSON fixture → re-generate
│  └─ Or describe changes → rebuild
├─ Need a template
│  └─ Check resources/templates/ (10 SVG templates for each diagram type)
└─ Reference needed
   └─ Read specific style: references/style-N-*.md
   └─ Read layout rules: references/svg-layout-best-practices.md
   └─ Read style matrix: references/style-diagram-matrix.md
```

## Diagram Types (14)

| Type | Layout | Template |
|------|--------|----------|
| Architecture | Horizontal layers top→bottom | `resources/templates/architecture.svg` |
| Data Flow | Label every arrow with data type | `resources/templates/data-flow.svg` |
| Flowchart | Top-to-bottom, diamond=decision | `resources/templates/flowchart.svg` |
| Sequence | Vertical lifelines, horizontal messages | `resources/templates/sequence.svg` |
| Agent Architecture | 5-layer: Input/Agent/Memory/Tool/Output | `resources/templates/agent-architecture.svg` |
| State Machine | Rounded rect states, transitions | `resources/templates/state-machine.svg` |
| ER Diagram | Entity rects with PK/FK | `resources/templates/er-diagram.svg` |
| Comparison Matrix | Column=system, row=attribute | `resources/templates/comparison-matrix.svg` |
| Timeline/Gantt | Horizontal time axis | `resources/templates/timeline.svg` |
| Use Case (UML) | Actors + use cases | `resources/templates/use-case.svg` |
| UML Class | 3-compartment rect | via architecture template |
| UML Component | Interfaces + components | via architecture template |
| Mind Map | Radial from center | via data-flow template |
| Network Topology | Nodes + connections | via architecture template |

## Shapes (14+ semantic kinds)

| Concept | Shape | JSON `kind` value |
|---------|-------|--------------------|
| User/Human | Stick figure | `user_avatar` |
| LLM/Model | Double-border rounded rect | `double_rect` |
| Agent/Orchestrator | Hexagon | `hexagon` |
| Database/Long-term memory | Cylinder | `cylinder` |
| Vector Store | Cylinder with inner rings | `cylinder` (+ inner lines) |
| Graph DB | 3 overlapping circles | `circle_cluster` |
| Short-term memory | Dashed rounded rect | `memory` |
| Tool/Function | Rect with gear icon | `rect` |
| API/Gateway | Hexagon single border | `hexagon` |
| Decision | Diamond | `diamond` |
| Document/File | Folded-corner rect | `document` |
| Browser/UI | Rect with titlebar | `terminal` |
| Bot/Agent variant | Bot icon | `bot` |
| Speech/Response | Speech bubble | `speech` |

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

## JSON Fixture Format (Full-Featured)

See `resources/` for complete examples. Structure:

```json
{
  "containers": [
    {"x": 30, "y": 84, "width": 1020, "height": 74, "label": "Input Layer", "stroke": "#dbeafe", "fill": "#f0fdf4"}
  ],
  "nodes": [
    {"id": "user", "label": "User", "kind": "user_avatar", "x": 80, "y": 100, "width": 60, "height": 48}
  ],
  "arrows": [
    {"from": "user", "to": "agent", "flow": "control", "label": "query", "source_port": "bottom", "target_port": "top"}
  ],
  "legend": {
    "x": 30, "y": 550, "items": [
      {"flow": "control", "label": "Control flow"},
      {"flow": "data", "label": "Data flow"}
    ]
  }
}
```

**Container fields**: `x`, `y`, `width`, `height`, `label`, `subtitle`, `stroke`, `fill`
**Node fields**: `id`, `label`, `kind`, `x`, `y`, `width`, `height`, `header_fill`
**Arrow fields**: `from`, `to`, `flow`, `label`, `source_port`, `target_port`, `corridor_x`, `route_points`, `dashed`
**Ports**: `top`, `bottom`, `left`, `right` — smart connection points

## JSON Input Format (Lightweight svg-gen.py)

```json
{
  "title": "My Diagram",
  "nodes": [
    {"id": "unique_id", "label": "Display", "shape": "rect", "layer": 0}
  ],
  "edges": [
    {"from": "unique_id", "to": "llm", "type": "primary", "label": "query"}
  ]
}
```

## Fixtures (Regression Tests)

| Fixture | Style | Diagram Type |
|---------|-------|-------------|
| `mem0-style1.json` | Flat Icon | Memory architecture |
| `tool-call-style2.json` | Dark Terminal | Agent tool execution |
| `microservices-style3.json` | Blueprint | Microservices |
| `agent-memory-types-style4.json` | Notion Clean | Agent memory |
| `multi-agent-style5.json` | Glassmorphism | Multi-agent system |
| `system-architecture-style6.json` | Claude Official | System architecture |
| `api-flow-style7.json` | OpenAI Official | API integration |

## References

| Reference | Purpose |
|-----------|---------|
| `tech-diagram.md` | Shape vocabulary, arrow semantics, layout rules, AI domain patterns |
| `style-1-flat-icon.md` | Style 1 complete spec (colors, fonts, effects) |
| `style-2-dark-terminal.md` | Style 2 complete spec |
| `style-3-blueprint.md` | Style 3 complete spec |
| `style-4-notion-clean.md` | Style 4 complete spec |
| `style-5-glassmorphism.md` | Style 5 complete spec |
| `style-6-claude-official.md` | Style 6 complete spec |
| `style-7-openai.md` | Style 7 complete spec |
| `style-diagram-matrix.md` | Which style works best for which diagram type |
| `svg-layout-best-practices.md` | Spacing, routing, collision avoidance, z-order |
| `icons.md` | 40+ product icons with brand colors |
