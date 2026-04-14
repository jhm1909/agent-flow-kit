# Visualize Codebase

Auto-generate an architecture diagram from codebase analysis. Combines code-graph analysis with diagram generation.

## Steps

1. Run hub detection to understand the codebase structure:
   ```bash
   bash skills/code-graph/scripts/hub-detect.sh
   ```
   If no source files are found, inform the user and stop.

2. From the output, identify:
   - Top hub files (most imported)
   - Bridge files (cross-directory connectors)
   - Directory groupings (natural layers)

3. Convert the analysis into a diagram JSON:
   - Each hub/bridge becomes a node (shape based on role)
   - Import relationships become edges
   - Group by directory into layers
   - Title: "Architecture: <project name>"

4. Generate the architecture diagram:
   ```bash
   echo '<json>' | python3 skills/diagram/scripts/svg-gen.py -o architecture.svg --style blueprint
   ```

5. Validate and deliver:
   ```bash
   bash skills/diagram/scripts/validate-svg.sh architecture.svg
   ```

6. Summarize: "Found N hubs, M bridges across K directories." Ask if the user wants to explore any module deeper.
