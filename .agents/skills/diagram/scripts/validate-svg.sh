#!/bin/bash
# SVG Validation Script
# Checks SVG syntax and reports detailed errors

set -eo pipefail

# Use python or python3 (Windows: python3 is often a Store stub that doesn't work)
PYTHON="python"
if ! "$PYTHON" -c "import sys" 2>/dev/null; then
    PYTHON="python3"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]; then
    echo "Usage: $0 <svg-file>"
    exit 1
fi

SVG_FILE="$1"

if [ ! -f "$SVG_FILE" ]; then
    echo -e "${RED}Error: File not found: $SVG_FILE${NC}"
    exit 1
fi

echo "Validating SVG: $SVG_FILE"
echo "----------------------------------------"

FAILURES=0
WARNINGS=0

# Check 0: XML syntax
echo -n "Checking XML syntax... "
if command -v xmllint &> /dev/null; then
    if xmllint --noout "$SVG_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓ Pass${NC}"
    else
        echo -e "${RED}✗ Fail${NC}"
        xmllint --noout "$SVG_FILE" 2>&1 || true
        FAILURES=$((FAILURES + 1))
    fi
else
    echo -e "${YELLOW}⚠ Skipped${NC} (xmllint not found)"
fi

# Check 1: Tag balance
echo -n "Checking tag balance... "
OPEN_TAGS=$( { grep -o '<[A-Za-z][A-Za-z0-9:-]*' "$SVG_FILE" || true; } | { grep -v '</' || true; } | wc -l | tr -d ' ' )
SELF_CLOSING=$( { grep -o '/>' "$SVG_FILE" || true; } | wc -l | tr -d ' ' )
CLOSE_TAGS=$( { grep -o '</[A-Za-z][A-Za-z0-9:-]*>' "$SVG_FILE" || true; } | wc -l | tr -d ' ' )
TOTAL_CLOSE=$((SELF_CLOSING + CLOSE_TAGS))

if [ "$OPEN_TAGS" -eq "$TOTAL_CLOSE" ]; then
    echo -e "${GREEN}✓ Pass${NC} (${OPEN_TAGS} tags)"
else
    echo -e "${RED}✗ Fail${NC} (${OPEN_TAGS} open, ${TOTAL_CLOSE} close)"
    FAILURES=$((FAILURES + 1))
fi

# Check 2: Quote check (only inside XML tags, not text content)
echo -n "Checking attribute quotes... "
UNQUOTED=$($PYTHON - "$SVG_FILE" <<'PY'
import re, sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding='utf-8')
# Extract only content inside XML tags (between < and >)
tags = re.findall(r'<[^>]+>', text)
count = 0
for tag in tags:
    # Skip processing instructions and comments
    if tag.startswith('<?') or tag.startswith('<!'):
        continue
    # Find unquoted attributes: name=value where value doesn't start with " or '
    matches = re.findall(r'\s([a-z][a-z0-9-]*)=([^"\x27\s>])', tag)
    count += len(matches)
print(count)
PY
)
if [ "$UNQUOTED" -eq 0 ]; then
    echo -e "${GREEN}✓ Pass${NC}"
else
    echo -e "${RED}✗ Fail${NC} (${UNQUOTED} unquoted attributes)"
    FAILURES=$((FAILURES + 1))
fi

# Check 3: Unescaped entities in text
echo -n "Checking text entities... "
SPECIAL=$($PYTHON - "$SVG_FILE" <<'PY'
from pathlib import Path
import re
import sys

text = Path(sys.argv[1]).read_text(encoding='utf-8')
issues = 0
for chunk in re.findall(r'>([^<]*)<', text, flags=re.S):
    cleaned = re.sub(r'&(amp|lt|gt|quot|apos);', '', chunk)
    if '&' in cleaned:
        issues += 1
print(issues)
PY
)
if [ "$SPECIAL" -eq 0 ]; then
    echo -e "${GREEN}✓ Pass${NC}"
else
    echo -e "${YELLOW}⚠ Warning${NC} (${SPECIAL} potential unescaped entities)"
fi

# Check 4: Marker references
echo -n "Checking marker references... "
MARKER_REFS=$( { grep -oE 'marker-end="url\(#[^)]+\)"' "$SVG_FILE" || true; } | { grep -oE '#[^)]+' || true; } | tr -d '#' | sort -u )
MARKER_DEFS=$( { grep -oE '<marker id="[^"]+"' "$SVG_FILE" || true; } | { sed 's/.*id="//; s/".*//' || true; } | sort -u )

MISSING=0
for ref in $MARKER_REFS; do
    if ! echo "$MARKER_DEFS" | grep -q "^${ref}$"; then
        echo -e "${RED}✗ Missing marker: $ref${NC}"
        MISSING=$((MISSING + 1))
    fi
done

if [ "$MISSING" -eq 0 ]; then
    echo -e "${GREEN}✓ Pass${NC}"
else
    echo -e "${RED}✗ Fail${NC} (${MISSING} missing markers)"
    FAILURES=$((FAILURES + 1))
fi

# Check 5: Arrow-component collision
echo -n "Checking arrow collisions... "
COLLISIONS=$($PYTHON - "$SVG_FILE" <<'PY'
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = {'svg': 'http://www.w3.org/2000/svg'}

def strip(tag):
    return tag.split('}', 1)[-1]

def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def is_container_rect(el):
    if el.get('stroke-dasharray'):
        return True
    width = to_float(el.get('width'))
    height = to_float(el.get('height'))
    if width > 700 or height > 500:
        return True
    if width < 70 or height < 30:
        return True
    return False

def shape_bounds(el):
    tag = strip(el.tag)
    if tag == 'rect':
        if is_container_rect(el):
            return None
        x = to_float(el.get('x'))
        y = to_float(el.get('y'))
        w = to_float(el.get('width'))
        h = to_float(el.get('height'))
        return (x, y, x + w, y + h)
    if tag == 'circle':
        r = to_float(el.get('r'))
        if r < 20:
            return None
        cx = to_float(el.get('cx'))
        cy = to_float(el.get('cy'))
        return (cx - r, cy - r, cx + r, cy + r)
    if tag == 'ellipse':
        rx = to_float(el.get('rx'))
        ry = to_float(el.get('ry'))
        if rx < 20 or ry < 20:
            return None
        cx = to_float(el.get('cx'))
        cy = to_float(el.get('cy'))
        return (cx - rx, cy - ry, cx + rx, cy + ry)
    return None

def parse_path_points(d):
    tokens = re.findall(r'[ML]|-?\d+(?:\.\d+)?', d or '')
    if not tokens:
        return []
    points = []
    command = None
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {'M', 'L'}:
            command = token
            index += 1
            continue
        if command not in {'M', 'L'} or index + 1 >= len(tokens):
            return []
        x = float(tokens[index])
        y = float(tokens[index + 1])
        points.append((x, y))
        index += 2
    return points

def segment_hits_bounds(p1, p2, bounds):
    x1, y1 = p1
    x2, y2 = p2
    left, top, right, bottom = bounds
    eps = 1e-6

    if abs(y1 - y2) < eps:
        y = y1
        if not (top + eps < y < bottom - eps):
            return False
        seg_left = min(x1, x2)
        seg_right = max(x1, x2)
        overlap_left = max(seg_left, left)
        overlap_right = min(seg_right, right)
        if overlap_right - overlap_left <= eps:
            return False
        if abs(overlap_left - x1) < eps or abs(overlap_right - x2) < eps:
            return False
        if abs(overlap_left - x2) < eps or abs(overlap_right - x1) < eps:
            return False
        return True

    if abs(x1 - x2) < eps:
        x = x1
        if not (left + eps < x < right - eps):
            return False
        seg_top = min(y1, y2)
        seg_bottom = max(y1, y2)
        overlap_top = max(seg_top, top)
        overlap_bottom = min(seg_bottom, bottom)
        if overlap_bottom - overlap_top <= eps:
            return False
        if abs(overlap_top - y1) < eps or abs(overlap_bottom - y2) < eps:
            return False
        if abs(overlap_top - y2) < eps or abs(overlap_bottom - y1) < eps:
            return False
        return True

    return False

try:
    root = ET.fromstring(Path(sys.argv[1]).read_text(encoding='utf-8'))
except ET.ParseError:
    print(0)  # Can't check collisions on malformed XML — tag balance check catches it
    sys.exit(0)
obstacles = [bounds for element in root.iter() if (bounds := shape_bounds(element)) is not None]

collisions = 0
for element in root.iter():
    tag = strip(element.tag)
    if tag == 'line' and element.get('marker-end'):
        points = [
            (to_float(element.get('x1')), to_float(element.get('y1'))),
            (to_float(element.get('x2')), to_float(element.get('y2'))),
        ]
    elif tag == 'path' and element.get('marker-end'):
        points = parse_path_points(element.get('d'))
    else:
        continue

    if len(points) < 2:
        continue
    start = points[0]
    end = points[-1]
    for p1, p2 in zip(points, points[1:]):
        for bounds in obstacles:
            left, top, right, bottom = bounds
            # Skip: obstacle contains the arrow's start or end point (source/target node)
            if (left <= start[0] <= right and top <= start[1] <= bottom):
                continue
            if (left <= end[0] <= right and top <= end[1] <= bottom):
                continue
            if segment_hits_bounds(p1, p2, bounds):
                collisions += 1
                break
        else:
            continue
        break

print(collisions)
PY
)
if [ "$COLLISIONS" -eq 0 ]; then
    echo -e "${GREEN}✓ Pass${NC}"
else
    echo -e "${YELLOW}⚠ Warning${NC} (${COLLISIONS} arrow path collision(s) — consider rerouting)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 6: Geometric validation (overlap, missing edges, layout spread)
echo -n "Checking geometric quality... "
GEO_RESULT=$(PYTHONIOENCODING=utf-8 $PYTHON - "$SVG_FILE" <<'PY'
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

def strip(tag):
    return tag.split('}', 1)[-1]

def to_float(v, d=0.0):
    try: return float(v)
    except: return d

def is_component_rect(el):
    if el.get('stroke-dasharray'):
        return False
    # Skip inner double-border rects (llm shape) — fill="none" with small inset
    if el.get('fill') == 'none' and el.get('stroke-width') == '1' and to_float(el.get('opacity', '1')) < 1:
        return False
    w = to_float(el.get('width'))
    h = to_float(el.get('height'))
    if w > 700 or h > 500 or w < 40 or h < 20:
        return False
    return True

try:
    root = ET.fromstring(Path(sys.argv[1]).read_text(encoding='utf-8'))
except ET.ParseError:
    print("OK")  # Tag balance check already caught malformed XML
    sys.exit(0)
vb = root.get('viewBox', '0 0 960 700').split()
canvas_w, canvas_h = float(vb[2]), float(vb[3])

# Collect component bounding boxes
nodes = []
for el in root.iter():
    tag = strip(el.tag)
    if tag == 'rect' and is_component_rect(el):
        x, y = to_float(el.get('x')), to_float(el.get('y'))
        w, h = to_float(el.get('width')), to_float(el.get('height'))
        nodes.append((x, y, x + w, y + h))
    elif tag == 'ellipse':
        rx, ry = to_float(el.get('rx')), to_float(el.get('ry'))
        if rx >= 20 and ry >= 15:
            cx, cy = to_float(el.get('cx')), to_float(el.get('cy'))
            nodes.append((cx - rx, cy - ry, cx + rx, cy + ry))
    elif tag == 'circle':
        r = to_float(el.get('r'))
        if r >= 20:
            cx, cy = to_float(el.get('cx')), to_float(el.get('cy'))
            nodes.append((cx - r, cy - r, cx + r, cy + r))

# Count edges (lines/paths with markers)
edge_count = 0
for el in root.iter():
    tag = strip(el.tag)
    if tag in ('line', 'path', 'polyline') and el.get('marker-end'):
        edge_count += 1

failures = []

# Check A: Node overlap — any two nodes intersect by more than 10px
for i in range(len(nodes)):
    for j in range(i + 1, len(nodes)):
        a, b = nodes[i], nodes[j]
        ox = max(0, min(a[2], b[2]) - max(a[0], b[0]))
        oy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
        if ox > 10 and oy > 10:
            failures.append(f"OVERLAP: nodes at ({a[0]:.0f},{a[1]:.0f}) and ({b[0]:.0f},{b[1]:.0f}) overlap by {ox:.0f}x{oy:.0f}px")

# Check B: Missing edges — diagram has nodes but no connections
if len(nodes) >= 2 and edge_count == 0:
    failures.append(f"NO_EDGES: {len(nodes)} nodes found but 0 edges - diagram has no connections")

# Check C: Layout spread — all nodes crammed into small area
if len(nodes) >= 3:
    all_x = [n[0] for n in nodes] + [n[2] for n in nodes]
    all_y = [n[1] for n in nodes] + [n[3] for n in nodes]
    spread_w = max(all_x) - min(all_x)
    spread_h = max(all_y) - min(all_y)
    usage = (spread_w * spread_h) / (canvas_w * canvas_h) if canvas_w * canvas_h > 0 else 0
    if usage < 0.08:
        failures.append(f"CRAMPED: nodes use only {usage*100:.1f}% of canvas ({spread_w:.0f}x{spread_h:.0f}px in {canvas_w:.0f}x{canvas_h:.0f}px)")

if failures:
    for f in failures:
        print(f"FAIL: {f}")
    print(f"TOTAL:{len(failures)}")
else:
    print("OK")
PY
)

if echo "$GEO_RESULT" | grep -q "^OK$"; then
    echo -e "${GREEN}✓ Pass${NC}"
else
    FAIL_COUNT=$(echo "$GEO_RESULT" | grep "^TOTAL:" | sed 's/TOTAL://')
    echo -e "${RED}✗ Fail${NC} (${FAIL_COUNT} geometric issue(s))"
    echo "$GEO_RESULT" | grep "^FAIL:" | sed 's/^FAIL: /  /'
    FAILURES=$((FAILURES + FAIL_COUNT))
fi

# Check 7: Closing </svg> tag
echo -n "Checking closing tag... "
if grep -q '</svg>' "$SVG_FILE"; then
    echo -e "${GREEN}✓ Pass${NC}"
else
    echo -e "${RED}✗ Fail${NC} (missing </svg>)"
    FAILURES=$((FAILURES + 1))
fi

# Check 8: rsvg-convert validation
echo -n "Running rsvg-convert validation... "
if command -v rsvg-convert &> /dev/null; then
    if rsvg-convert "$SVG_FILE" -o /tmp/test-output.png 2>/dev/null; then
        echo -e "${GREEN}✓ Pass${NC}"
        rm -f /tmp/test-output.png
    else
        echo -e "${RED}✗ Fail${NC}"
        echo "rsvg-convert error:"
        rsvg-convert "$SVG_FILE" -o /tmp/test-output.png 2>&1 || true
        FAILURES=$((FAILURES + 1))
    fi
else
    echo -e "${YELLOW}⚠ Skipped${NC} (rsvg-convert not found)"
fi

echo "----------------------------------------"
if [ "$FAILURES" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}Validation passed${NC}"
    exit 0
elif [ "$FAILURES" -eq 0 ]; then
    echo -e "${YELLOW}Validation passed with ${WARNINGS} warning(s)${NC}"
    exit 0
else
    echo -e "${RED}Validation failed (${FAILURES} error(s), ${WARNINGS} warning(s))${NC}"
    exit 1
fi
