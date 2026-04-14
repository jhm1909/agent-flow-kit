# Create Diagram

Generate a production-quality SVG diagram from a text description.

## Steps

1. Ask the user what they want to visualize. Identify the diagram type (architecture, flowchart, sequence, agent system, ER, etc.).

2. Ask about visual style preference. If none specified, auto-detect:
   - Documentation → flat-icon
   - GitHub/dark theme → dark-terminal
   - Engineering → blueprint
   - AI/agent topic → claude-official
   - Confirm your choice with the user before proceeding.

3. Build a JSON structure describing nodes, edges, and containers. Use examples from `skills/diagram/resources/` as reference for the JSON format.

4. Generate the SVG using the diagram skill's scripts:
   ```bash
   # For complex diagrams with containers and routing
   python3 skills/diagram/scripts/generate-from-template.py <type> output.svg '<json>'

   # For simple node-and-edge diagrams
   echo '<json>' | python3 skills/diagram/scripts/svg-gen.py -o output.svg --style <style>
   ```

5. Validate the output:
   ```bash
   bash skills/diagram/scripts/validate-svg.sh output.svg
   ```

6. If validation fails, fix the JSON and regenerate. If it fails twice, show the raw SVG and ask the user for guidance.

7. Deliver the file path to the user.
