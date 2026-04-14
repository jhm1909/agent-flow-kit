# Diagram JSON Schema Reference

Complete field reference for diagram input JSON. Used by both `generate-from-template.py` and `svg-gen.py`.

## Top-Level Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `title` | string | No | — | Diagram title (rendered at top) |
| `subtitle` | string | No | — | Subtitle below title |
| `template_type` | string | No | `"architecture"` | Diagram type for generate-from-template.py |
| `style` | int (1-7) | No | `1` | Visual style number |
| `width` | number | No | `960` | Canvas width in pixels |
| `height` | number | No | `600` | Canvas height in pixels |
| `nodes` | array | **Yes** | — | List of node objects |
| `edges` / `arrows` | array | No | `[]` | List of edge objects (`edges` for svg-gen.py, `arrows` for generate-from-template.py) |
| `containers` | array | No | `[]` | Swim lane / grouping containers |
| `legend` | array | No | `[]` | Arrow type legend entries |

## Node Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | **Yes** | — | Unique identifier (used in edges `from`/`to`) |
| `label` | string | **Yes** | — | Display text |
| `kind` / `shape` | string | No | `"rect"` | Shape type (see table below) |
| `x` | number | No | auto | X position (omit for auto-layout) |
| `y` | number | No | auto | Y position (omit for auto-layout) |
| `width` | number | No | auto | Width in pixels (auto-calculated from label if omitted) |
| `height` | number | No | `56` | Height in pixels |
| `layer` | int | No | `0` | Layer index for svg-gen.py auto-layout (0=top) |
| `sublabel` | string | No | — | Secondary text below label |
| `fill` | string | No | from style | Background color override |
| `stroke` | string | No | from style | Border color override |
| `container` | string | No | — | Container ID this node belongs to |

### Shape/Kind Values

| Value | Visual | Use for |
|-------|--------|---------|
| `rect` | Rectangle | Generic component, tool, function |
| `double_rect` / `llm` | Double-border rounded rect | LLM, AI model |
| `hexagon` / `agent` | Hexagon | Agent, orchestrator, gateway |
| `cylinder` / `database` | Cylinder | Database, persistent storage |
| `memory` | Dashed rounded rect | Short-term memory, cache |
| `diamond` / `decision` | Diamond | Decision point (flowcharts) |
| `document` | Folded-corner rect | File, document |
| `terminal` | Rect with titlebar | Browser, UI, terminal |
| `user_avatar` | Stick figure | User, human actor |
| `circle_cluster` | 3 overlapping circles | Graph DB |
| `bot` | Bot icon | Bot, automated agent |
| `speech` | Speech bubble | Response, chat message |

## Edge/Arrow Fields

### For svg-gen.py (`edges` array)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `from` | string | **Yes** | — | Source node ID |
| `to` | string | **Yes** | — | Target node ID |
| `type` | string | No | `"primary"` | Arrow style (see table below) |
| `label` | string | No | — | Edge label text |

### For generate-from-template.py (`arrows` array)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `source` | string | **Yes** | — | Source node ID |
| `target` | string | **Yes** | — | Target node ID |
| `flow` | string | No | `"control"` | Arrow style |
| `label` | string | No | — | Edge label text |
| `source_port` | string | No | auto | Connection point: `top`, `bottom`, `left`, `right` |
| `target_port` | string | No | auto | Connection point |
| `dashed` | bool | No | `false` | Force dashed line |
| `label_dx` | number | No | `0` | Label X offset |
| `label_dy` | number | No | `0` | Label Y offset |
| `route_points` | array | No | — | Explicit waypoints: `[[x1,y1], [x2,y2]]` |
| `corridor_x` | array | No | — | Vertical corridor hints for routing |

### Arrow Type Values

| Value | Color | Visual | Use for |
|-------|-------|--------|---------|
| `primary` / `data` | Blue #2563eb | Solid | Main data flow, request/response |
| `control` | Orange #ea580c | Solid | Triggers, control signals |
| `read` | Green #059669 | Solid | Memory/DB read operations |
| `write` | Green #059669 | Dashed | Memory/DB write operations |
| `async` / `event` | Gray #6b7280 | Dashed | Async events, non-blocking |
| `feedback` | Purple #7c3aed | Solid | Feedback loops, iteration |

## Container Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | No | auto | Unique identifier |
| `label` | string | **Yes** | — | Container header text |
| `subtitle` | string | No | — | Secondary label |
| `x` | number | No | auto | X position (omit for auto-layout) |
| `y` | number | No | auto | Y position |
| `width` | number | No | auto | Width |
| `height` | number | No | auto | Height |
| `stroke` | string | No | from style | Border color |
| `fill` | string | No | `"none"` | Background color |

## Legend Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `flow` | string | **Yes** | Arrow type to illustrate |
| `label` | string | **Yes** | Legend entry text |

## Common Mistakes

| Mistake | Error | Fix |
|---------|-------|-----|
| Missing `id` on node | Script crash / silent skip | Every node MUST have unique `id` |
| `from`/`to` references nonexistent node ID | Edge silently ignored | Check IDs match exactly (case-sensitive) |
| Using `edges` with generate-from-template.py | Arrows not rendered | Use `arrows` array with `source`/`target` fields |
| Using `arrows` with svg-gen.py | Arrows not rendered | Use `edges` array with `from`/`to` fields |
| Setting `x`/`y` on some nodes but not all | Mixed layout | Either ALL nodes have positions, or NONE (auto-layout) |
| Label text too long (>40 chars) | Text overflows shape | Keep labels short or increase `width` |
| No `legend` with 2+ arrow types | Reader can't distinguish arrows | Add legend when using multiple arrow types |

## Minimal Example (svg-gen.py)

```json
{
  "title": "Simple Flow",
  "nodes": [
    {"id": "input", "label": "User Input", "shape": "rect"},
    {"id": "process", "label": "Process", "shape": "hexagon"},
    {"id": "output", "label": "Result", "shape": "rect"}
  ],
  "edges": [
    {"from": "input", "to": "process", "type": "primary", "label": "request"},
    {"from": "process", "to": "output", "type": "primary", "label": "response"}
  ]
}
```

## Full Example (generate-from-template.py)

```json
{
  "template_type": "architecture",
  "style": 3,
  "width": 960,
  "height": 600,
  "title": "System Architecture",
  "containers": [
    {"x": 30, "y": 80, "width": 900, "height": 200, "label": "Backend", "stroke": "#3b82f6"}
  ],
  "nodes": [
    {"id": "api", "label": "API Gateway", "kind": "hexagon", "x": 100, "y": 120, "width": 120, "height": 56},
    {"id": "service", "label": "Service", "kind": "rect", "x": 300, "y": 120, "width": 100, "height": 56},
    {"id": "db", "label": "PostgreSQL", "kind": "cylinder", "x": 500, "y": 120, "width": 100, "height": 56}
  ],
  "arrows": [
    {"source": "api", "target": "service", "flow": "control", "label": "request"},
    {"source": "service", "target": "db", "flow": "read", "label": "query"}
  ],
  "legend": [
    {"flow": "control", "label": "Control flow"},
    {"flow": "read", "label": "Read operation"}
  ]
}
```
