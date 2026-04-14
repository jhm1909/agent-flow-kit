# Technical Diagram Reference

> Source: [fireworks-tech-graph](https://github.com/yizhiyanhua-ai/fireworks-tech-graph) — curated and improved.

## Shape Vocabulary

| Concept | Shape | Visual | Notes |
|---------|-------|--------|-------|
| User/Human | Circle + body path | Stick figure | Entry point |
| LLM/Model | Rounded rect, double border | Accent | Core AI component |
| Agent/Orchestrator | Hexagon | — | Active controller |
| Memory (short-term) | Rounded rect, dashed | — | Ephemeral |
| Memory (long-term) | Cylinder | — | Persistent |
| Vector Store | Cylinder with inner rings | 3 horizontal lines | Embedding storage |
| Graph DB | 3 overlapping circles | Cluster | Knowledge graph |
| Tool/Function | Rect with gear icon | — | Callable action |
| API/Gateway | Hexagon, single border | — | External interface |
| Queue/Stream | Horizontal pipe | Tube | Message passing |
| Document/File | Folded-corner rect | — | Static content |
| Browser/UI | Rect with 3-dot titlebar | — | User interface |
| Decision | Diamond | — | Flowcharts only |

## Arrow Semantics

| Flow | Color | Stroke | Dash | Meaning |
|------|-------|--------|------|---------|
| Primary data | `#2563eb` | 2px solid | — | Main request/response |
| Control/trigger | `#ea580c` | 1.5px solid | — | System A triggers B |
| Memory read | `#059669` | 1.5px solid | — | Retrieve from store |
| Memory write | `#059669` | 1.5px | `5,3` | Write/store operation |
| Async/event | `#6b7280` | 1.5px | `4,2` | Non-blocking |
| Feedback/loop | `#7c3aed` | 1.5px curved | — | Iterative reasoning |

**Rule**: Include a legend when 2+ arrow types are used.

## Layout Rules

- **Spacing**: 80px horizontal same-layer, 120px vertical between layers
- **Margins**: 40px minimum canvas margin
- **Grid snap**: 8px grid, 120px intervals
- **Arrow labels**: MUST have background rect with 4px padding
- **Arrow routing**: Prefer orthogonal (L-shaped) paths
- **Jump-over arcs**: 5px radius semicircle for unavoidable crossings

## AI/Agent Domain Patterns

Recognize these common architectures and use appropriate shapes:

```
RAG Pipeline       → Query → Embed → VectorSearch → Retrieve → LLM → Response
Agentic RAG        → adds Agent loop + Tool use around RAG
Agentic Search     → Query → Planner → [Search/Calc/Code] → Synthesizer
Memory Layer       → Input → Memory Manager → [VectorDB + GraphDB] → Context
Agent Memory Types → Sensory → Working → Episodic → Semantic → Procedural
Multi-Agent        → Orchestrator → [SubAgent×N] → Aggregator → Output
Tool Call Flow     → LLM → Tool Selector → Execution → Parser → LLM (loop)
```

## 7 Visual Styles

| # | Name | Background | Best For |
|---|------|-----------|----------|
| 1 | Flat Icon (default) | `#ffffff` | Blogs, slides, docs |
| 2 | Dark Terminal | `#0f0f1a` | GitHub README, dev articles |
| 3 | Blueprint | `#0a1628` | Architecture docs |
| 4 | Notion Clean | `#ffffff` minimal | Notion, wikis |
| 5 | Glassmorphism | `#0d1117` gradient | Product sites, keynotes |
| 6 | Claude Official | `#f8f6f3` | Professional |
| 7 | OpenAI Official | `#ffffff` | Clean modern minimalist |

## ViewBox Defaults

| Diagram Type | ViewBox |
|-------------|---------|
| Architecture | `0 0 960 600` |
| Agent Architecture | `0 0 960 700` |
| Memory Architecture | `0 0 960 700` |
| Sequence | Height = `80 + (N × 50)` |
| Comparison Matrix | `0 0 960 400` |
| Mind Map | `0 0 960 560` |
