---
description: Generates production-quality SVG diagrams from text descriptions, with style auto-detection and validation.
---

# Diagram Generation Workflow

> **Execution context:** All script paths are relative to the `.agents/` root directory.

---

## Step 1: Understand Requirements

// turbo

1. **Invoke `[diagram]` skill** to classify the diagram type from user description:
   - Architecture, Flowchart, Sequence, Agent Architecture, Data Flow, ER, State Machine, Timeline, Use Case, Comparison Matrix, Mind Map, UML
2. Extract key elements: nodes, edges, containers, layers.
3. **WAIT** if diagram type is ambiguous — ask user to clarify.

---

## Step 2: Select Visual Style

// turbo

**Skip if**: User already specified a style.

1. **Invoke `[diagram]` skill** — read `references/style-diagram-matrix.md` to find best match:
   - Documentation/slides → `flat-icon`
   - GitHub/dark theme → `dark-terminal`
   - Engineering/infra → `blueprint`
   - AI/agent topic → `claude-official`
   - Default → `flat-icon`
2. Present choice to user: "Using [style] because [reason]. OK?"
3. **WAIT** for user confirmation.

---

## Step 3: Build JSON Structure

// turbo

1. **Invoke `[diagram]` skill** — read `references/tech-diagram.md` for:
   - Shape vocabulary (which `kind` for each concept)
   - Arrow semantics (which `flow` type for each relationship)
2. Use examples from `resources/` as reference for JSON format.
3. Build the JSON with nodes, edges, containers, and legend.

---

## Step 4: Generate SVG

// turbo

1. **Invoke `[diagram]` skill** — save JSON to temp, then generate:
   ```bash
   mkdir -p .agents-output/diagram/tmp .agents-output/diagram/svg
   ```
   - **Complex diagrams** (containers, ports, swim lanes):
     ```bash
     python3 skills/diagram/scripts/generate-from-template.py <type> .agents-output/diagram/svg/output.svg -i .agents-output/diagram/tmp/input.json
     ```
   - **Simple diagrams** (nodes + edges only):
     ```bash
     cat .agents-output/diagram/tmp/input.json | python3 skills/diagram/scripts/svg-gen.py -o .agents-output/diagram/svg/output.svg --style <style>
     ```
2. Check exit code — 0 = success.

---

## Step 5: Validate & Deliver

// turbo

1. **Invoke `[diagram]` skill** — validate the output:
   ```bash
   bash scripts/validate-svg.sh output.svg
   ```
2. If valid → deliver file path to user.
3. If invalid:
   - First failure → analyze error, fix JSON, regenerate (return to Step 4).
   - Second failure → **STOP**. Show raw SVG. Ask user for guidance.

---

## Quick Reference

| Step | Skill   | Output              |
|------|---------|---------------------|
| 1    | diagram | Diagram type + elements |
| 2    | diagram | Visual style choice |
| 3    | diagram | JSON structure       |
| 4    | diagram | SVG file            |
| 5    | diagram | Validated SVG       |
