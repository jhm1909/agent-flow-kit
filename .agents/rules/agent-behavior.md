---
description: Guardrails for all agent-flow-kit skills and workflows.
---

# Agent Behavior Rules

These rules apply to ALL skills and workflows in this toolkit.

## 1. Validate Before Deliver

- SVG output MUST pass XML validation before claiming success.
- Scripts MUST exit 0 before using their output.
- Never deliver unvalidated output without explicit warning.

## 2. Confirm Before Assume

- Style not specified → auto-detect + ask user to confirm.
- Blast-radius > 50 files → warn: "Large scope, review may be incomplete."
- Ambiguous diagram type → ask, don't guess.

## 3. Token-Efficient

- Code-graph: read ONLY files within blast-radius, not entire codebase.
- Diagram: build JSON first, render second — makes debugging possible.
- Review: stop reading when risk is understood, don't read LOW-priority files unnecessarily.

## 4. Fail Gracefully

- SVG validation fails once → analyze error, fix, retry.
- SVG validation fails twice → STOP. Show raw SVG. Ask user.
- Script fails → show stderr output. Suggest fix. Don't retry blindly.
- Never silently swallow errors.

## 5. Keep It Simple

- Zero external dependencies — bash, git, python3 only.
- No orphan temp files — clean up after yourself.
- Output = file path + one-line summary. No walls of text.
