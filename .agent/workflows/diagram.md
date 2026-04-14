---
description: Generate production-quality diagrams from text descriptions. Auto-detects style when not specified.
---

# Diagram Workflow

## Step 1: Classify & Extract

// turbo

1. **Read skill**: `.agent/skills/diagram/SKILL.md`
2. Classify diagram type from user description.
3. Extract nodes, edges, and layers.
4. Map concepts to semantic shapes (LLM → `llm`, Agent → `agent`, DB → `database`).

---

## Step 2: Select Style

// turbo

1. If user specified a style → use it.
2. If not → auto-detect:
   - README/docs context → `flat-icon`
   - `.github/` or dark theme → `dark-terminal`
   - "architecture"/"infra" keywords → `blueprint`
   - "agent"/"LLM"/"AI" keywords → `claude-official`
   - Default → `flat-icon`
3. **Confirm with user**: "Using [style] because [reason]. OK?"

---

## Step 3: Generate

// turbo

1. Build JSON input with nodes, edges, title.
2. Run: `python3 scripts/svg-gen.py -i input.json -o output.svg --style <style>`
3. Check exit code — 0 = success.

---

## Step 4: Validate & Deliver

// turbo

1. Run: `python3 scripts/svg-gen.py --validate-only -o output.svg`
2. If valid → deliver file path to user.
3. If invalid:
   - First failure → analyze error, fix JSON, regenerate.
   - Second failure → stop, show raw SVG, ask user for guidance.
