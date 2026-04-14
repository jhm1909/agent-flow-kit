---
name: diagram
description: Generates production-quality SVG technical diagrams from text descriptions. Use when asked to create architecture diagrams, flowcharts, sequence diagrams, agent system visualizations, ER diagrams, or any technical illustration.
---

# Diagram

Generate SVG diagrams from natural language descriptions. Supports 14 diagram types, 7 visual styles, and semantic shapes for AI/agent systems.

## When to use this skill

- User asks to create, draw, or visualize a diagram
- Need to illustrate system architecture, data flow, or agent pipelines
- Converting text descriptions into visual technical diagrams
- Creating diagrams for documentation, presentations, or READMEs

## Available scripts

Run with `--help` first to see options:

- `scripts/generate-from-template.py` — Full-featured generator with containers, ports, routing
- `scripts/svg-gen.py` — Lightweight JSON-to-SVG pipeline
- `scripts/validate-svg.sh` — XML validation and structural checks
- `scripts/generate-diagram.sh` — End-to-end: generate + validate + export
- `scripts/test-all-styles.sh` — Regression test all 7 styles

## How to use it

1. **Classify the diagram type** from the user's description:
   - Architecture, Flowchart, Sequence, Agent Architecture, Data Flow, ER, State Machine, Timeline, Use Case, Comparison Matrix, Mind Map, UML Class, UML Component, Network Topology

2. **Choose a visual style** (or auto-detect):
   - Docs/slides → `flat-icon` (default)
   - GitHub/dark theme → `dark-terminal`
   - Engineering docs → `blueprint`
   - AI/agent topic → `claude-official`
   - See [style-diagram-matrix.md](references/style-diagram-matrix.md) for full recommendations
   - Confirm with user if auto-detected

3. **Build the JSON input** describing nodes, edges, and containers:
   - See `resources/` for 7 complete examples (one per style)
   - See [tech-diagram.md](references/tech-diagram.md) for shape vocabulary and arrow semantics

4. **Generate the SVG**:
   ```bash
   # Complex diagrams (containers, swim lanes, port routing)
   python3 scripts/generate-from-template.py <type> output.svg '<json>'

   # Simple diagrams (just nodes + edges)
   echo '<json>' | python3 scripts/svg-gen.py -o output.svg --style flat-icon
   ```

5. **Validate** before delivering:
   ```bash
   bash scripts/validate-svg.sh output.svg
   ```

## Resources

- `resources/` — 7 JSON fixture examples (one per style) + `templates/` (10 SVG templates)

## References

For detailed specifications, read on demand:

| File | Use when |
|------|----------|
| [tech-diagram.md](references/tech-diagram.md) | Need shape vocabulary, arrow semantics, AI domain patterns |
| [style-N-*.md](references/) | Need exact colors, fonts, effects for a specific style |
| [style-diagram-matrix.md](references/style-diagram-matrix.md) | Choosing which style fits which diagram type |
| [svg-layout-best-practices.md](references/svg-layout-best-practices.md) | Layout spacing, arrow routing, collision avoidance |
| [icons.md](references/icons.md) | Need product brand icons (40+ with hex colors) |
