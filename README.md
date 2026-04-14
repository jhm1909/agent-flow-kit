# agent-flow-kit

Lightweight toolkit that gives AI coding assistants two capabilities:

1. **Diagram generation** — create SVG/PNG diagrams from text descriptions
2. **Code graph review** — analyze codebase blast-radius and risk scoring

## Requirements

- bash, git, python3 (pre-installed on most dev machines)

**Optional dependencies** (for validation and PNG export):
- `xmllint` — SVG validation (`brew install libxml2` / `apt install libxml2-utils`)
- `rsvg-convert` — PNG export (`brew install librsvg` / `apt install librsvg2-bin`)

## Usage

Clone into your project or copy the `.agent/` directory:

```bash
git clone https://github.com/jhm1909/agent-flow-kit.git
cp -r agent-flow-kit/.agent/ your-project/.agent/
cp -r agent-flow-kit/.agent/ your-project/.agent/
```

## Skills

| Skill | Purpose |
|-------|---------|
| `diagram` | Generate architecture, flowchart, sequence, agent, UML diagrams |
| `code-graph` | Blast-radius analysis, risk scoring, hub/bridge detection |

## Workflows

| Workflow | Flow |
|----------|------|
| `diagram` | text → classify → style detect → SVG → validate → PNG |
| `code-review` | git diff → blast-radius → risk score → focused review |
| `visualize-code` | hub-detect → nodes/edges → auto architecture diagram |

## Sources

Built on techniques from:
- [antigravity-kit](https://github.com/jhm1909/antigravity-kit) — skill/workflow structure
- [fireworks-tech-graph](https://github.com/yizhiyanhua-ai/fireworks-tech-graph) — diagram methodology
- [code-graph](https://github.com/tirth8205/code-graph) — graph analysis methodology

## License

MIT
