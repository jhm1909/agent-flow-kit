---
description: Auto-generates architecture diagram from codebase analysis. Combines code-graph and diagram skills.
---

# Visualize Codebase Workflow

---

## Step 1: Analyze Structure

// turbo

1. **Invoke `[code-graph]` skill** — run hub detection:
   ```bash
   bash scripts/hub-detect.sh
   ```
2. Capture: top hubs, bridge nodes, directory structure.
3. If no source files found → inform user and stop.

---

## Step 2: Build Graph Data

// turbo

1. **Invoke `[code-graph]` skill** to interpret the hub-detect output:
   - Identify top hub files (most imported)
   - Identify bridge files (cross-directory connectors)
   - Group files by directory into natural layers
2. **Invoke `[diagram]` skill** — read `references/tech-diagram.md` to map:
   - Each hub/bridge → a node (shape based on role: `cylinder` for data, `hexagon` for orchestrators, `rect` for modules)
   - Import relationships → edges (`primary` for direct, `async` for cross-directory)
3. Build JSON with title: "Architecture: <project name>"

---

## Step 3: Generate Diagram

// turbo

1. **Invoke `[diagram]` skill** — generate architecture diagram:
   ```bash
   echo '<json>' | python3 scripts/svg-gen.py -o architecture.svg --style blueprint
   ```
   Default style: `blueprint` (best for architecture diagrams per `style-diagram-matrix.md`).
2. Validate:
   ```bash
   bash scripts/validate-svg.sh architecture.svg
   ```

---

## Step 4: Deliver

// turbo

1. Present architecture diagram file path.
2. Summarize: "Found N hubs, M bridges across K directories."
3. **WAIT** — ask user: "Want to dive deeper into any module?"

---

## Quick Reference

| Step | Skill                | Output                    |
|------|----------------------|---------------------------|
| 1    | code-graph           | Hubs + bridges + dirs     |
| 2    | code-graph + diagram | JSON graph data           |
| 3    | diagram              | Architecture SVG          |
| 4    | —                    | Summary + next steps      |
