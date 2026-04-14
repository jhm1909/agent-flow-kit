#!/usr/bin/env python3
"""
svg-gen.py — SVG diagram generator. Zero external dependencies (stdlib only).

Usage:
  echo '{"nodes":[...], "edges":[...]}' | python3 scripts/svg-gen.py -o output.svg
  python3 scripts/svg-gen.py -i input.json -o output.svg --style dark-terminal
  python3 scripts/svg-gen.py --validate-only -o existing.svg
"""

import argparse
import json
import io
import math
import os
import sys
import xml.etree.ElementTree as ET
from typing import Any

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ---------------------------------------------------------------------------
# Style definitions
# ---------------------------------------------------------------------------

STYLES: dict[str, dict[str, str]] = {
    "flat-icon": {
        "bg": "#ffffff",
        "node_fill": "#f8fafc",
        "node_stroke": "#475569",
        "text": "#1e293b",
        "edge": "#64748b",
        "font": "Inter, system-ui, sans-serif",
    },
    "dark-terminal": {
        "bg": "#0f0f1a",
        "node_fill": "#1e1e3f",
        "node_stroke": "#6366f1",
        "text": "#e0e0ff",
        "edge": "#818cf8",
        "font": "'JetBrains Mono', 'Fira Code', monospace",
    },
    "blueprint": {
        "bg": "#0a1628",
        "node_fill": "#0f2040",
        "node_stroke": "#3b82f6",
        "text": "#93c5fd",
        "edge": "#60a5fa",
        "font": "'IBM Plex Mono', 'Courier New', monospace",
    },
    "notion-clean": {
        "bg": "#ffffff",
        "node_fill": "#f9f9f9",
        "node_stroke": "#d1d5db",
        "text": "#374151",
        "edge": "#9ca3af",
        "font": "Inter, system-ui, sans-serif",
    },
    "glassmorphism": {
        "bg": "#0d1117",
        "node_fill": "rgba(30,41,59,0.6)",
        "node_stroke": "#3b82f6",
        "text": "#e2e8f0",
        "edge": "#60a5fa",
        "font": "Inter, system-ui, sans-serif",
    },
    "claude-official": {
        "bg": "#f8f6f3",
        "node_fill": "#fff8f0",
        "node_stroke": "#92400e",
        "text": "#44200c",
        "edge": "#b45309",
        "font": "Inter, system-ui, sans-serif",
    },
    "openai-official": {
        "bg": "#ffffff",
        "node_fill": "#f0fdf4",
        "node_stroke": "#10a37f",
        "text": "#064e3b",
        "edge": "#10a37f",
        "font": "Inter, system-ui, sans-serif",
    },
}

# ---------------------------------------------------------------------------
# Arrow / edge type definitions
# ---------------------------------------------------------------------------

EDGE_TYPES: dict[str, dict[str, Any]] = {
    "primary": {"color": "#2563eb", "width": 2,   "dash": None},
    "control":  {"color": "#ea580c", "width": 1.5, "dash": None},
    "read":     {"color": "#059669", "width": 1.5, "dash": None},
    "write":    {"color": "#059669", "width": 1.5, "dash": "5,3"},
    "async":    {"color": "#6b7280", "width": 1.5, "dash": "4,2"},
    "feedback": {"color": "#7c3aed", "width": 1.5, "dash": None},
}

GRID = 8
LAYER_V_SPACING = 120
MARGIN = 40
DEFAULT_W = 140
DEFAULT_H = 56


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def snap(v: float) -> int:
    """Snap a value to the 8-px grid."""
    return int(round(v / GRID) * GRID)


def compute_layout(nodes: list[dict]) -> dict[str, dict[str, int]]:
    """
    Assign (x, y, w, h) to every node using the `layer` field.
    Nodes in the same layer are centred horizontally with even spacing.
    Returns a mapping of node id -> {x, y, w, h}.
    """
    # Group nodes by layer
    layers: dict[int, list[dict]] = {}
    for n in nodes:
        layer = int(n.get("layer", 0))
        layers.setdefault(layer, []).append(n)

    # Determine canvas width: widest layer
    max_row_width = 0
    for layer_nodes in layers.values():
        row_w = sum(int(n.get("width", DEFAULT_W)) for n in layer_nodes)
        h_gap = 24 * (len(layer_nodes) - 1)
        max_row_width = max(max_row_width, row_w + h_gap)

    canvas_w = max_row_width + 2 * MARGIN

    positions: dict[str, dict[str, int]] = {}

    for layer_idx in sorted(layers.keys()):
        layer_nodes = layers[layer_idx]
        y_top = snap(MARGIN + layer_idx * LAYER_V_SPACING)

        row_total_w = sum(int(n.get("width", DEFAULT_W)) for n in layer_nodes)
        h_gaps = 24 * (len(layer_nodes) - 1)
        start_x = snap((canvas_w - row_total_w - h_gaps) / 2)

        cur_x = start_x
        for n in layer_nodes:
            w = snap(int(n.get("width", DEFAULT_W)))
            h = snap(int(n.get("height", DEFAULT_H)))
            positions[n["id"]] = {"x": cur_x, "y": y_top, "w": w, "h": h}
            cur_x = snap(cur_x + w + 24)

    return positions, canvas_w


# ---------------------------------------------------------------------------
# SVG shape drawing
# ---------------------------------------------------------------------------

def _hex_points(cx: float, cy: float, w: float, h: float) -> str:
    """Return SVG polygon points string for a hexagon fitting in (w x h)."""
    rx = w / 2
    ry = h / 2
    # flat-top hexagon: 6 points
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + rx * math.cos(angle)
        py = cy + ry * math.sin(angle)
        pts.append(f"{px:.2f},{py:.2f}")
    return " ".join(pts)


def _cylinder_path(x: float, y: float, w: float, h: float) -> str:
    """Return SVG path for a cylinder (database) shape."""
    ry = max(8, h * 0.12)          # ellipse y-radius for top/bottom caps
    rx_e = w / 2                   # ellipse x-radius
    cx = x + w / 2
    top_y = y + ry
    bot_y = y + h - ry

    # Body: left side down, bottom ellipse arc, right side up, top ellipse arc
    d = (
        f"M {x} {top_y} "
        f"L {x} {bot_y} "
        f"A {rx_e} {ry} 0 0 0 {x + w} {bot_y} "
        f"L {x + w} {top_y} "
        f"A {rx_e} {ry} 0 0 1 {x} {top_y} "
        f"Z"
    )
    top_ellipse = (
        f"M {x} {top_y} "
        f"A {rx_e} {ry} 0 0 0 {x + w} {top_y} "
        f"A {rx_e} {ry} 0 0 0 {x} {top_y} "
        f"Z"
    )
    return d, top_ellipse, ry


def draw_node(
    parent: ET.Element,
    node: dict,
    pos: dict[str, int],
    style: dict[str, str],
) -> None:
    x, y, w, h = pos["x"], pos["y"], pos["w"], pos["h"]
    shape = node.get("shape", "rect")
    label = node.get("label", node["id"])

    fill = node.get("fill", style["node_fill"])
    stroke = node.get("stroke", style["node_stroke"])
    text_color = node.get("text_color", style["text"])

    cx = x + w / 2
    cy = y + h / 2

    g = ET.SubElement(parent, "g", {"class": f"node node-{node['id']}"})

    if shape == "rect":
        ET.SubElement(g, "rect", {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h),
            "rx": "8", "ry": "8",
            "fill": fill, "stroke": stroke, "stroke-width": "1.5",
        })

    elif shape == "rounded-rect":
        ET.SubElement(g, "rect", {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h),
            "rx": "16", "ry": "16",
            "fill": fill, "stroke": stroke, "stroke-width": "1.5",
        })

    elif shape == "llm":
        # Outer rounded rect
        ET.SubElement(g, "rect", {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h),
            "rx": "16", "ry": "16",
            "fill": fill, "stroke": stroke, "stroke-width": "2",
        })
        # Inner double-border rect (4px inset)
        ET.SubElement(g, "rect", {
            "x": str(x + 4), "y": str(y + 4),
            "width": str(w - 8), "height": str(h - 8),
            "rx": "12", "ry": "12",
            "fill": "none", "stroke": stroke, "stroke-width": "1",
            "opacity": "0.5",
        })

    elif shape in ("agent", "hexagon"):
        ET.SubElement(g, "polygon", {
            "points": _hex_points(cx, cy, w, h),
            "fill": fill, "stroke": stroke, "stroke-width": "1.5",
        })

    elif shape in ("database", "cylinder", "memory"):
        body_d, top_d, _ry = _cylinder_path(x, y, w, h)
        ET.SubElement(g, "path", {
            "d": body_d,
            "fill": fill, "stroke": stroke, "stroke-width": "1.5",
        })
        ET.SubElement(g, "path", {
            "d": top_d,
            "fill": stroke, "opacity": "0.25", "stroke": stroke,
            "stroke-width": "1",
        })

    elif shape in ("decision", "diamond"):
        pts = (
            f"{cx},{y} "
            f"{x + w},{cy} "
            f"{cx},{y + h} "
            f"{x},{cy}"
        )
        ET.SubElement(g, "polygon", {
            "points": pts,
            "fill": fill, "stroke": stroke, "stroke-width": "1.5",
        })

    else:
        # fallback: plain rect
        ET.SubElement(g, "rect", {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h),
            "rx": "8", "ry": "8",
            "fill": fill, "stroke": stroke, "stroke-width": "1.5",
        })

    # Label text (centred)
    txt = ET.SubElement(g, "text", {
        "x": str(cx),
        "y": str(cy),
        "text-anchor": "middle",
        "dominant-baseline": "central",
        "fill": text_color,
        "font-family": style["font"],
        "font-size": "13",
        "font-weight": "500",
    })
    txt.text = label


# ---------------------------------------------------------------------------
# Edge drawing
# ---------------------------------------------------------------------------

def _marker_id(edge_type: str) -> str:
    return f"arrow-{edge_type}"


def add_defs(svg: ET.Element, used_types: set[str]) -> None:
    defs = ET.SubElement(svg, "defs")
    for etype in used_types:
        cfg = EDGE_TYPES.get(etype, EDGE_TYPES["primary"])
        marker = ET.SubElement(defs, "marker", {
            "id": _marker_id(etype),
            "markerWidth": "10",
            "markerHeight": "7",
            "refX": "9",
            "refY": "3.5",
            "orient": "auto",
        })
        ET.SubElement(marker, "polygon", {
            "points": "0 0, 10 3.5, 0 7",
            "fill": cfg["color"],
        })


def _node_bottom_center(pos: dict[str, int]) -> tuple[float, float]:
    return pos["x"] + pos["w"] / 2, pos["y"] + pos["h"]


def _node_top_center(pos: dict[str, int]) -> tuple[float, float]:
    return pos["x"] + pos["w"] / 2, pos["y"]


def draw_edge(
    parent: ET.Element,
    edge: dict,
    positions: dict[str, dict[str, int]],
    style: dict[str, str],
) -> None:
    from_id = edge["from"]
    to_id = edge["to"]

    if from_id not in positions or to_id not in positions:
        return  # skip unknown nodes

    src = positions[from_id]
    dst = positions[to_id]

    etype = edge.get("type", "primary")
    cfg = EDGE_TYPES.get(etype, EDGE_TYPES["primary"])

    x1, y1 = _node_bottom_center(src)
    x2, y2 = _node_top_center(dst)

    # Cubic bezier control points (vertical flow)
    cp_offset = max(40, abs(y2 - y1) * 0.45)
    cp1_x, cp1_y = x1, y1 + cp_offset
    cp2_x, cp2_y = x2, y2 - cp_offset

    path_d = (
        f"M {x1:.1f} {y1:.1f} "
        f"C {cp1_x:.1f} {cp1_y:.1f}, {cp2_x:.1f} {cp2_y:.1f}, {x2:.1f} {y2:.1f}"
    )

    attrs: dict[str, str] = {
        "d": path_d,
        "fill": "none",
        "stroke": cfg["color"],
        "stroke-width": str(cfg["width"]),
        "marker-end": f"url(#{_marker_id(etype)})",
    }
    if cfg["dash"]:
        attrs["stroke-dasharray"] = cfg["dash"]

    ET.SubElement(parent, "path", attrs)

    # Optional label
    label = edge.get("label")
    if label:
        lx = (x1 + x2) / 2
        ly = (y1 + y2) / 2
        # Background pill
        pad_x, pad_y = 6, 3
        char_w = 7.5
        lw = len(label) * char_w + pad_x * 2
        lh = 18

        ET.SubElement(parent, "rect", {
            "x": str(lx - lw / 2),
            "y": str(ly - lh / 2),
            "width": str(lw),
            "height": str(lh),
            "rx": "4",
            "fill": style["bg"],
            "stroke": cfg["color"],
            "stroke-width": "0.75",
            "opacity": "0.92",
        })
        ET.SubElement(parent, "text", {
            "x": str(lx),
            "y": str(ly),
            "text-anchor": "middle",
            "dominant-baseline": "central",
            "fill": cfg["color"],
            "font-family": style["font"],
            "font-size": "11",
            "font-weight": "500",
        }).text = label


# ---------------------------------------------------------------------------
# Main SVG builder
# ---------------------------------------------------------------------------

def build_svg(data: dict, style_name: str = "flat-icon") -> str:
    style = STYLES.get(style_name, STYLES["flat-icon"])

    nodes: list[dict] = data.get("nodes", [])
    edges: list[dict] = data.get("edges", [])
    title: str | None = data.get("title")

    if not nodes:
        raise ValueError("No nodes provided in input JSON.")

    positions, canvas_w = compute_layout(nodes)

    # Canvas height: max layer + height of tallest node in that layer + margin
    max_y = max(p["y"] + p["h"] for p in positions.values())
    canvas_h = max_y + MARGIN + (32 if title else 0)

    title_offset = 32 if title else 0
    if title:
        # Shift all nodes down to make room for title
        for nid in positions:
            positions[nid]["y"] += title_offset
        canvas_h += title_offset  # we already added title_offset once above; don't double

    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "width": str(canvas_w),
        "height": str(canvas_h),
        "viewBox": f"0 0 {canvas_w} {canvas_h}",
    })

    # Background
    ET.SubElement(svg, "rect", {
        "width": "100%", "height": "100%",
        "fill": style["bg"],
    })

    # Title
    if title:
        ET.SubElement(svg, "text", {
            "x": str(canvas_w / 2),
            "y": str(MARGIN),
            "text-anchor": "middle",
            "dominant-baseline": "central",
            "fill": style["text"],
            "font-family": style["font"],
            "font-size": "16",
            "font-weight": "700",
        }).text = title

    # Arrow markers
    used_types = {e.get("type", "primary") for e in edges}
    add_defs(svg, used_types)

    # Edges (drawn before nodes so they appear behind)
    edge_group = ET.SubElement(svg, "g", {"class": "edges"})
    for edge in edges:
        draw_edge(edge_group, edge, positions, style)

    # Nodes
    node_group = ET.SubElement(svg, "g", {"class": "nodes"})
    node_map = {n["id"]: n for n in nodes}
    for nid, pos in positions.items():
        draw_node(node_group, node_map[nid], pos, style)

    return ET.tostring(svg, encoding="unicode", xml_declaration=False)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_svg(svg_content: str) -> bool:
    """Return True if SVG is valid XML, False otherwise."""
    try:
        ET.fromstring(svg_content)
        return True
    except ET.ParseError as exc:
        print(f"SVG validation error: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate SVG diagrams from JSON node/edge definitions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-i", "--input",
        metavar="FILE",
        help="Input JSON file (default: read from stdin)",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        required=True,
        help="Output SVG file path",
    )
    parser.add_argument(
        "--style",
        default="flat-icon",
        choices=list(STYLES.keys()),
        help="Visual style (default: flat-icon)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate an existing SVG file and exit (no generation)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # --validate-only mode
    if args.validate_only:
        try:
            with open(args.output, "r", encoding="utf-8") as fh:
                content = fh.read()
        except FileNotFoundError:
            print(f"File not found: {args.output}", file=sys.stderr)
            return 1
        ok = validate_svg(content)
        if ok:
            print(f"Valid SVG: {args.output}")
            return 0
        else:
            return 1

    # Read JSON input
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except FileNotFoundError:
            print(f"Input file not found: {args.input}", file=sys.stderr)
            return 1
    else:
        raw = sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}", file=sys.stderr)
        return 1

    # Warn if input has features this script doesn't support
    if "containers" in data:
        print("Warning: svg-gen.py ignores 'containers'. For container/swim-lane support, use generate-from-template.py instead.", file=sys.stderr)
    if any("x" in n and "y" in n for n in data.get("nodes", [])):
        print("Warning: svg-gen.py ignores absolute x/y positions. It uses auto-layout based on 'layer' field.", file=sys.stderr)

    # Redirect output to .agents-output/diagram/svg/ (never inside .agents/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
    abs_out = os.path.abspath(args.output)
    agents_dir = os.path.join(project_root, ".agents")
    if abs_out.startswith(agents_dir) or not os.path.isabs(args.output):
        out_dir = os.path.join(project_root, ".agents-output", "diagram", "svg")
        os.makedirs(out_dir, exist_ok=True)
        args.output = os.path.join(out_dir, os.path.basename(args.output))
        print(f"Output: {args.output}", file=sys.stderr)

    # Generate SVG
    try:
        svg_content = build_svg(data, style_name=args.style)
    except Exception as exc:
        print(f"Error generating SVG: {exc}", file=sys.stderr)
        return 1

    # Write output (always, even if validation fails — useful for debugging)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fh.write(svg_content)
        fh.write("\n")

    # Validate
    ok = validate_svg(svg_content)
    if ok:
        print(f"Generated: {args.output}  (style={args.style})")
    else:
        print(f"Written (invalid SVG): {args.output}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
