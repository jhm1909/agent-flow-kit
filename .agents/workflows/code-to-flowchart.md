---
description: Generates a flowchart diagram from a code snippet. Reads the code's control flow (branches, loops, calls, returns) and produces a validated SVG via the diagram skill.
---

# Code to Flowchart Workflow

> **Execution context:** All script paths are relative to the `.agents/` root directory.

---

## Step 0: Receive Code

// turbo

1. User provides code — either pasted inline, a file path, or a function name in the codebase.
2. If file path → read the file. If function name → search and extract the function.
3. If the code is longer than ~80 lines, suggest focusing on a specific function or section.

**Output**: The code snippet to analyze

---

## Step 1: Trace Control Flow

// turbo

Read the code carefully and extract every control flow element in execution order:

| Code construct | → Flowchart element |
|----------------|---------------------|
| Function signature / entry point | **Start** node (circle/rounded-rect) |
| Simple statement (assignment, print, call) | **Process** node (rect) |
| `if` / `elif` / `else` / ternary | **Decision** node (diamond) with Yes/No branches |
| `for` / `while` loop | **Decision** node (diamond) + feedback edge back to loop start |
| `try` / `except` / `finally` | **Process** node with branching: normal path + exception path |
| `return` / `yield` / `raise` | **End** node (circle/rounded-rect) |
| Function call (important ones) | **Process** node (hexagon if external service/API) |
| `break` / `continue` | Edge to loop exit or loop start |

### Rules:
- **Simplify**: group sequential simple statements into ONE node (e.g., 3 assignments → one "Initialize variables" node)
- **Keep decisions explicit**: every `if` must be a diamond with labeled Yes/No edges
- **Label edges**: use the condition as the label (e.g., `"x > 0"` on the Yes branch)
- **Max ~15 nodes** — if the code produces more, group related statements together

**Output**: Mental model of nodes and edges

---

## Step 2: Build Flowchart JSON

// turbo

Map the traced flow into JSON for `svg-gen.py`:

### Shape mapping

| Flowchart element | JSON `shape` | `layer` |
|-------------------|-------------|---------|
| Start | `rounded-rect` | 0 |
| Process / Statement | `rect` | incremental |
| Decision (if/while/for) | `diamond` | incremental |
| End / Return | `rounded-rect` | last |
| External call / API | `hexagon` | incremental |

### Edge type mapping

| Flow type | JSON `type` |
|-----------|------------|
| Normal flow (next step) | `primary` |
| Yes / True branch | `primary` (label: condition) |
| No / False branch | `control` (label: "else" or negated condition) |
| Loop back | `feedback` |
| Exception path | `async` |

### Layer assignment rules:
- Start = layer 0
- Each sequential step increments layer by 1
- Branches (if/else) go on the **same layer**
- Merge point after branches increments layer
- Loop-back edges use `feedback` type (rendered as purple arc)

### JSON structure:
```json
{
  "title": "Function: <function_name>",
  "nodes": [
    {"id": "start", "label": "Start", "shape": "rounded-rect", "layer": 0},
    {"id": "step1", "label": "Initialize x, y", "shape": "rect", "layer": 1},
    {"id": "check", "label": "x > 0?", "shape": "diamond", "layer": 2},
    ...
  ],
  "edges": [
    {"from": "start", "to": "step1", "type": "primary"},
    {"from": "step1", "to": "check", "type": "primary"},
    {"from": "check", "to": "yes_path", "type": "primary", "label": "Yes"},
    {"from": "check", "to": "no_path", "type": "control", "label": "No"},
    ...
  ]
}
```

**WAIT** if the flowchart has 10+ nodes — present the node list to user for confirmation before generating.

**Output**: Complete JSON file

---

## Step 3: Generate SVG

// turbo

1. **Choose a descriptive base name** from the function/code name (e.g., `login-flow`, `parse-csv`, `retry-logic`).

2. **Save JSON**:
   ```bash
   mkdir -p .agents-output/diagram/tmp .agents-output/diagram/svg
   # Write JSON to .agents-output/diagram/tmp/<descriptive-name>.json
   ```

3. **Generate** — always use `svg-gen.py` (flowcharts are simple diagrams with auto-layout):
   ```bash
   cat .agents-output/diagram/tmp/<descriptive-name>.json | python3 skills/diagram/scripts/svg-gen.py -o <descriptive-name>.svg --style <style>
   ```

4. Default style: `flat-icon`. If user specified a style, use that.

5. **Validate**:
   ```bash
   bash skills/diagram/scripts/validate-svg.sh .agents-output/diagram/svg/<descriptive-name>.svg
   ```

**Output**: Validated SVG file

---

## Step 4: Deliver

// turbo

1. Present the SVG file path.
2. Summarize: "Flowchart for `<function_name>`: [N] steps, [M] decisions, [K] branches."
3. **WAIT** — ask: "Want to adjust? (simplify, add detail, change style, highlight a specific path)"

---

## Quick Reference

| Step | Action | Output |
|------|--------|--------|
| 0 | Receive code snippet | Code to analyze |
| 1 | Trace control flow | Mental model of nodes/edges |
| 2 | Build flowchart JSON | JSON file |
| 3 | Generate + validate SVG | SVG file |
| 4 | Deliver + iterate | File path + summary |
