---
type: always
---

# Agent Flow Kit Rules

These constraints apply to all skills and workflows in this toolkit.

## Validate before delivering

- SVG output must pass validation before claiming success.
- Scripts must exit 0 before using their output.
- Never deliver unvalidated output without warning the user.

## Confirm before assuming

- If the user didn't specify a diagram style, auto-detect and ask to confirm.
- If blast-radius exceeds 50 files, warn that the review may be incomplete.
- If the diagram type is ambiguous, ask instead of guessing.

## Fail gracefully

- If SVG validation fails once, analyze the error and retry.
- If it fails twice, stop and show the raw SVG to the user.
- If a script fails, show the error output and suggest a fix. Don't retry blindly.
- Never silently swallow errors.

## Output to .agents-output/

- **Never** write output files inside `.agents/`. This directory is for configuration only.
- All output goes to `.agents-output/` at project root with this structure:
  ```
  .agents-output/
  ├── diagram/
  │   ├── svg/        ← SVG output
  │   ├── png/        ← PNG export
  │   └── tmp/        ← JSON input files
  ├── code-graph/
  │   ├── reports/    ← blast-radius, hub-detect output
  │   └── tmp/        ← temporary data
  └── visualize/
      ├── svg/        ← architecture diagrams
      └── tmp/        ← intermediate JSON
  ```
- Create subdirectories with `mkdir -p` before writing.
- If user specifies an absolute path, respect it.

## Keep output concise

- Deliver file paths and one-line summaries, not walls of text.
- Clean up temporary files after use.
