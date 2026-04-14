---
description: Auto-generates architecture diagram from codebase analysis. Combines code-graph and diagram skills.
---

# Visualize Codebase Workflow

> **Execution context:** All script paths are relative to the `.agents/` root directory.

---

## Step 1: Analyze & Generate JSON

// turbo

1. **Invoke `[code-graph]` skill** — run hub detection with JSON output:
   ```bash
   mkdir -p .agents-output/visualize/tmp
   bash skills/code-graph/scripts/hub-detect.sh --json > .agents-output/visualize/tmp/arch-data.json
   ```
2. If output shows `"total_files": 0` → inform user and stop.
3. Review the JSON: check node count, hub/bridge distribution.

---

## Step 2: Generate Diagram

// turbo

1. **Invoke `[diagram]` skill** — pipe JSON directly to SVG generator:
   ```bash
   mkdir -p .agents-output/visualize/svg
   cat .agents-output/visualize/tmp/arch-data.json | python3 skills/diagram/scripts/svg-gen.py -o .agents-output/visualize/svg/architecture.svg --style blueprint
   ```
   Default style: `blueprint` (best for architecture diagrams per `style-diagram-matrix.md`).
2. Validate:
   ```bash
   bash skills/diagram/scripts/validate-svg.sh .agents-output/visualize/svg/architecture.svg
   ```
3. If the auto-generated diagram needs refinement, edit `.agents-output/visualize/tmp/arch-data.json` and regenerate.

---

## Step 3: Deliver

// turbo

1. Present architecture diagram file path.
2. Summarize: "Found N hubs, M bridges across K directories."
3. **WAIT** — ask user: "Want to dive deeper into any module?"

---

## Quick Reference

| Step | Skill                | Output                    |
|------|----------------------|---------------------------|
| 1    | code-graph           | arch-data.json (auto-generated) |
| 2    | diagram              | architecture.svg          |
| 3    | —                    | Summary + next steps      |
