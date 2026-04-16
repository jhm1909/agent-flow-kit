---
description: Auto-generates architecture diagram from codebase analysis. Chains code-graph hub detection with diagram generation for visual project understanding.
---

# Visualize Codebase Workflow

> **Execution context:** All script paths are relative to the `.agents/` root directory.

---

## Step 1: Analyze Codebase Structure

// turbo

1. **Invoke `[code-graph]` skill** — run hub detection with JSON output:
   ```bash
   mkdir -p .agents-output/visualize/tmp
   bash skills/code-graph/scripts/hub-detect.sh --json > .agents-output/visualize/tmp/arch-data.json
   ```
2. Read the JSON output. Check `summary.total_files`:
   - If `0` → inform user: "No source files found in this directory." Stop.
   - If `< 3` → inform user: "Very small codebase. Architecture diagram may not be meaningful." Offer to proceed or skip.
3. Note key findings: top hubs, bridges, directory groupings.

**Output**: `arch-data.json` with nodes, edges, and summary

---

## Step 2: Enrich the Graph (Optional)

// turbo

**Skip if**: User wants a quick diagram, or codebase has < 10 files.

1. Review the auto-generated JSON. The hub-detect script creates a basic graph, but you can enrich it:
   - **Relabel nodes** for clarity (e.g., `utils.py (25)` → `Core Utilities (25 dependents)`)
   - **Assign semantic shapes**: data files → `cylinder`, orchestrators → `hexagon`, libraries → `rect`
   - **Add containers**: group files by directory into swim lanes
   - **Add edge labels**: describe what flows between components

2. **Invoke `[diagram]` skill** — read [tech-diagram.md](skills/diagram/references/tech-diagram.md) for shape/arrow vocabulary.

3. Save enriched JSON back to `.agents-output/visualize/tmp/arch-data.json`.

4. **WAIT** — present the enriched structure to user: "Here's the architecture I found: [N] hubs, [M] bridges, [K] modules. I'll generate a diagram. OK?"

**Output**: Enriched JSON with semantic shapes and labels

---

## Step 3: Generate Architecture Diagram

// turbo

1. **Choose a descriptive filename** based on the project or scope (e.g., `myapp-architecture.svg`, `backend-modules.svg`). Never use generic names like `output.svg`.

2. **Invoke `[diagram]` skill** — generate SVG:
   ```bash
   cat .agents-output/visualize/tmp/arch-data.json | python3 skills/diagram/scripts/svg-gen.py -o <descriptive-name>.svg --style blueprint --output-dir .agents-output/visualize/svg
   ```
   Default style: `blueprint` (best for architecture diagrams per style-diagram-matrix).

   > Scripts automatically append a counter (`_1`, `_2`, ...) if a file with the same name already exists.

3. **Validate**:
   ```bash
   bash skills/diagram/scripts/validate-svg.sh .agents-output/visualize/svg/<descriptive-name>.svg
   ```

4. If validation fails → fix and regenerate (follow diagram skill's 3-strike protocol).

**Output**: Architecture SVG in `.agents-output/visualize/svg/`

---

## Step 4: Deliver & Explore

// turbo

1. Present the diagram file path.
2. Summarize: "Architecture: **[N] hubs**, **[M] bridges** across **[K] directories**."
3. Highlight key findings:
   - "**[filename]** is the most-connected file (X dependents) — changes here affect many modules."
   - "**[filename]** bridges [dir-A] and [dir-B] — this is a cross-module connector."
4. **WAIT** — ask: "Want to dive deeper into any module, or generate a different diagram type for a subsystem?"

**Output**: Diagram + architecture summary + exploration offer

---

## Quick Reference

| Step | Skill | Output |
|------|-------|--------|
| 1 | code-graph | arch-data.json (auto-generated) |
| 2 | diagram (optional) | Enriched JSON with shapes/labels |
| 3 | diagram | Architecture SVG |
| 4 | — | Summary + exploration offer |
