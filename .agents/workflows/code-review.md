# Review Code Changes

Analyze recent code changes using blast-radius tracing and risk scoring.

## Steps

1. Identify the changed files:
   ```bash
   git diff --name-only HEAD~1..HEAD
   ```
   If no changes found, inform the user and stop.

2. Run blast-radius analysis:
   ```bash
   bash skills/code-graph/scripts/blast-radius.sh
   ```

3. Read the risk assessment from the output. Follow the review strategy based on risk level:
   - **CRITICAL/HIGH**: Read all files in the blast radius.
   - **MEDIUM**: Read changed files and direct callers.
   - **LOW**: Read changed files only.

4. For each file reviewed, check for:
   - Security-sensitive code changes (auth, validation, access control)
   - Breaking changes to public APIs
   - Missing test coverage for changed functions

5. Present findings with file:line references. Classify each issue as CRITICAL, HIGH, MEDIUM, or LOW. Suggest specific fixes where applicable.
