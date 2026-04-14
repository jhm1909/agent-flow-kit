---
description: Auto-generate architecture diagram from codebase analysis. Combines code-graph and diagram skills.
---

# Visualize Code Workflow

## Step 1: Analyze Structure

// turbo

1. Run: `./.agent/scripts/hub-detect.sh`
2. Capture: top hubs, bridge nodes, directory structure.
3. If no source files found → inform user, stop.

---

## Step 2: Build Graph Data

// turbo

1. Convert hub-detect output to diagram JSON:
   - Each hub/bridge → a node (shape based on role: `database` for data files, `agent` for orchestrators, `rect` for modules).
   - Import relationships → edges (type: `primary` for direct, `async` for cross-directory).
   - Group by directory → layers.
2. Add title: "Architecture: <project name>"

---

## Step 3: Generate Diagram

// turbo

1. Select style: `blueprint` (default for architecture diagrams).
2. Run: `python3 .agent/scripts/svg-gen.py -i arch.json -o architecture.svg --style blueprint`
3. Validate output.

---

## Step 4: Deliver

// turbo

1. Present architecture diagram file path.
2. Summarize: "Found N hubs, M bridges across K directories."
3. Ask user: "Want to dive deeper into any module?"
