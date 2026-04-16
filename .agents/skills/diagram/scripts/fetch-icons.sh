#!/bin/bash
# fetch-icons.sh — Download Lucide icon library for svg-gen.py
#
# Downloads icon-nodes.json (1695 icons, ~679KB) and tags.json (~221KB)
# from the Lucide CDN. Run once — svg-gen.py auto-detects the files.
#
# Usage:
#   bash scripts/fetch-icons.sh
#   bash scripts/fetch-icons.sh --force   # re-download even if exists
#
# Files are saved to .agents/skills/diagram/scripts/lucide/
# License: MIT (https://github.com/lucide-icons/lucide/blob/main/LICENSE)

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LUCIDE_DIR="$SCRIPT_DIR/lucide"
CDN="https://cdn.jsdelivr.net/npm/lucide-static@latest"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

FORCE=false
if [ "$1" = "--force" ]; then
    FORCE=true
fi

# Check if already downloaded
if [ -f "$LUCIDE_DIR/icon-nodes.json" ] && [ "$FORCE" = false ]; then
    ICON_COUNT=$(python -c "import json; print(len(json.load(open('$LUCIDE_DIR/icon-nodes.json'))))" 2>/dev/null || echo "0")
    echo -e "${GREEN}Lucide icons already downloaded${NC} ($ICON_COUNT icons in $LUCIDE_DIR/)"
    echo "Use --force to re-download."
    exit 0
fi

mkdir -p "$LUCIDE_DIR"

echo -e "${CYAN}Downloading Lucide icon library...${NC}"

# Download icon-nodes.json (all icon SVG elements)
echo -n "  icon-nodes.json... "
if curl -sL "$CDN/icon-nodes.json" -o "$LUCIDE_DIR/icon-nodes.json"; then
    SIZE=$(wc -c < "$LUCIDE_DIR/icon-nodes.json" | tr -d ' ')
    ICON_COUNT=$(python -c "import json; print(len(json.load(open('$LUCIDE_DIR/icon-nodes.json'))))" 2>/dev/null || echo "?")
    echo -e "${GREEN}OK${NC} (${ICON_COUNT} icons, ${SIZE} bytes)"
else
    echo -e "${RED}FAILED${NC}"
    exit 1
fi

# Download tags.json (icon categories/keywords)
echo -n "  tags.json... "
if curl -sL "$CDN/tags.json" -o "$LUCIDE_DIR/tags.json"; then
    SIZE=$(wc -c < "$LUCIDE_DIR/tags.json" | tr -d ' ')
    echo -e "${GREEN}OK${NC} (${SIZE} bytes)"
else
    echo -e "${RED}FAILED${NC} (optional — auto-detect will still work)"
fi

echo ""
echo -e "${GREEN}Done!${NC} Lucide icons available at: $LUCIDE_DIR/"
echo "svg-gen.py will auto-detect and use these icons."
echo "Use any icon by name: {\"icon\": \"rocket\"} or {\"icon\": \"github\"}"
