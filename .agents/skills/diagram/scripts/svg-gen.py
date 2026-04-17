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

# Icon system
try:
    from icons import ICONS, detect_icon
except ImportError:
    ICONS = {}
    def detect_icon(node: dict) -> str | None:  # type: ignore
        return None

# Ensure UTF-8 I/O on Windows (default is cp949/cp1252 which breaks CJK/Vietnamese)
if sys.stdin.encoding != "utf-8":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
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
# Arrow / edge type definitions (default fallback)
# ---------------------------------------------------------------------------

EDGE_TYPES: dict[str, dict[str, Any]] = {
    "primary": {"color": "#2563eb", "width": 2,   "dash": None},
    "control":  {"color": "#ea580c", "width": 1.5, "dash": None},
    "read":     {"color": "#059669", "width": 1.5, "dash": None},
    "write":    {"color": "#059669", "width": 1.5, "dash": "5,3"},
    "async":    {"color": "#6b7280", "width": 1.5, "dash": "4,2"},
    "feedback": {"color": "#7c3aed", "width": 1.5, "dash": None},
}

# Per-style edge colors (matched from generate-from-template.py palettes)
STYLE_EDGE_COLORS: dict[str, dict[str, str]] = {
    "flat-icon": {
        "primary": "#2563eb", "control": "#7c3aed", "read": "#2563eb",
        "write": "#10b981", "async": "#7c3aed", "feedback": "#ef4444",
    },
    "dark-terminal": {
        "primary": "#38bdf8", "control": "#a855f7", "read": "#38bdf8",
        "write": "#22c55e", "async": "#f59e0b", "feedback": "#f97316",
    },
    "blueprint": {
        "primary": "#38bdf8", "control": "#67e8f9", "read": "#38bdf8",
        "write": "#22d3ee", "async": "#c084fc", "feedback": "#fb7185",
    },
    "notion-clean": {
        "primary": "#3b82f6", "control": "#3b82f6", "read": "#3b82f6",
        "write": "#3b82f6", "async": "#9ca3af", "feedback": "#9ca3af",
    },
    "glassmorphism": {
        "primary": "#60a5fa", "control": "#c084fc", "read": "#60a5fa",
        "write": "#34d399", "async": "#f472b6", "feedback": "#f59e0b",
    },
    "claude-official": {
        "primary": "#b45309", "control": "#d97757", "read": "#8c6f5a",
        "write": "#7b8b5c", "async": "#9a6fb0", "feedback": "#d97757",
    },
    "openai-official": {
        "primary": "#10a37f", "control": "#10a37f", "read": "#0891b2",
        "write": "#0f766e", "async": "#64748b", "feedback": "#10a37f",
    },
}


def _get_edge_cfg(etype: str, style_name: str) -> dict[str, Any]:
    """Get edge config with style-specific color override."""
    cfg = dict(EDGE_TYPES.get(etype, EDGE_TYPES["primary"]))
    colors = STYLE_EDGE_COLORS.get(style_name, {})
    if etype in colors:
        cfg["color"] = colors[etype]
    return cfg

GRID = 8
BASE_V_SPACING = 120     # base vertical spacing between layers
H_SPACE = 80
MARGIN = 40
CHAR_W_LATIN = 7.5
CHAR_W_CJK = 13.0   # CJK (Korean, Chinese, Japanese) chars are ~1.7x wider
PAD_X = 24
MIN_W = 100
MAX_W = 360          # Wider max for CJK text
LINE_H = 18
PAD_Y = 20


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def snap(v: float) -> int:
    """Snap a value to the 8-px grid."""
    return int(round(v / GRID) * GRID)


def _is_wide_char(ch: str) -> bool:
    """Return True if character is CJK/fullwidth (needs ~2x width)."""
    cp = ord(ch)
    return (
        0x2E80 <= cp <= 0x9FFF       # CJK Unified, Radicals, Kangxi
        or 0xAC00 <= cp <= 0xD7AF    # Hangul Syllables (Korean)
        or 0xF900 <= cp <= 0xFAFF    # CJK Compatibility
        or 0xFE30 <= cp <= 0xFE4F    # CJK Compatibility Forms
        or 0xFF00 <= cp <= 0xFF60    # Fullwidth Forms
        or 0x1F000 <= cp <= 0x1FFFF  # Emoji
        or 0x20000 <= cp <= 0x2FA1F  # CJK Extension B-F
        or 0x3000 <= cp <= 0x303F    # CJK Symbols
        or 0x3040 <= cp <= 0x30FF    # Hiragana + Katakana
        or 0x31F0 <= cp <= 0x31FF    # Katakana Extensions
    )


def _text_width(text: str) -> float:
    """Estimate pixel width of a text string, accounting for CJK/wide chars."""
    w = 0.0
    for ch in text:
        w += CHAR_W_CJK if _is_wide_char(ch) else CHAR_W_LATIN
    return w


def _label_lines(label: str) -> list[str]:
    """Split label into lines on \\n."""
    return label.split("\n") if label else [""]


def _auto_size(node: dict) -> tuple[int, int]:
    """Compute (width, height) from label text. Respects explicit width/height if set."""
    if "width" in node and "height" in node:
        return int(node["width"]), int(node["height"])
    label = node.get("label", node.get("id", ""))
    lines = _label_lines(label)
    longest_w = max((_text_width(line) for line in lines), default=0)

    # Shape-aware padding: non-rectangular shapes have less usable text area
    shape = node.get("shape", "rect")
    if shape in ("diamond", "decision"):
        # Diamond: usable text width ≈ 50% of bounding box
        text_area_w = longest_w / 0.5 + PAD_X
    elif shape in ("hexagon", "agent"):
        # Hexagon: usable text width ≈ 70% of bounding box
        text_area_w = longest_w / 0.7 + PAD_X
    else:
        # Rectangular shapes: full width minus padding
        text_area_w = longest_w + PAD_X * 2

    # Account for sublabel in width and height
    sublabel = node.get("sublabel", "")
    if sublabel:
        sub_w = _text_width(sublabel) + PAD_X * 2
        text_area_w = max(text_area_w, sub_w)

    w = snap(max(MIN_W, min(MAX_W, text_area_w)))
    extra_h = 16 if sublabel else 0  # extra space for sublabel
    h = snap(max(PAD_Y * 2, len(lines) * LINE_H + PAD_Y + extra_h))
    if node.get("width"):
        w = int(node["width"])
    if node.get("height"):
        h = int(node["height"])
    return w, h


def compute_layout(
    nodes: list[dict],
    edges: list[dict] | None = None,
    containers: list[dict] | None = None,
) -> tuple[dict[str, dict[str, int]], int, list[dict], dict[tuple[str, str], list[tuple[int, int]]]]:
    """
    Assign (x, y, w, h) to every node using Sugiyama hierarchical layout.
    Returns (positions, canvas_w, positioned_containers, edge_routes).
    edge_routes maps (from_id, to_id) -> list of (x,y) waypoints for orthogonal routing.
    """
    positioned_containers: list[dict] = []
    edge_routes: dict[tuple[str, str], list[tuple[int, int]]] = {}

    try:
        from layout.engine import compute_layout as _engine_layout
        data = {"nodes": nodes, "edges": edges or []}
        if containers:
            data["containers"] = containers
        result = _engine_layout(data)
        positions: dict[str, dict[str, int]] = {}
        for n in result.get("nodes", []):
            positions[n["id"]] = {"x": n["x"], "y": n["y"], "w": n["width"], "h": n["height"]}
        canvas_w = result.get("_canvas_width", 960)
        positioned_containers = result.get("containers", [])
        # Extract orthogonal routes from engine
        for e in result.get("edges", []):
            src = e.get("from") or e.get("source", "")
            tgt = e.get("to") or e.get("target", "")
            route = e.get("_route")
            if src and tgt and route and len(route) >= 2:
                edge_routes[(src, tgt)] = route
        return positions, canvas_w, positioned_containers, edge_routes
    except ImportError:
        pass

    edges = edges or []

    # Pre-compute sizes for all nodes
    sizes: dict[str, tuple[int, int]] = {}
    for n in nodes:
        sizes[n["id"]] = _auto_size(n)

    # Assign layers
    layers: dict[int, list[dict]] = {}
    for n in nodes:
        layer = int(n.get("layer", 0))
        layers.setdefault(layer, []).append(n)

    # Edge-crossing minimization: barycenter heuristic
    # Build adjacency for barycenter computation
    node_layer: dict[str, int] = {n["id"]: int(n.get("layer", 0)) for n in nodes}
    adj_down: dict[str, list[str]] = {}  # node -> children in next layer
    adj_up: dict[str, list[str]] = {}    # node -> parents in prev layer
    for e in edges:
        src = e.get("from") or e.get("source", "")
        tgt = e.get("to") or e.get("target", "")
        adj_down.setdefault(src, []).append(tgt)
        adj_up.setdefault(tgt, []).append(src)

    # Initial ordering: by JSON order
    layer_order: dict[int, list[str]] = {}
    for li in sorted(layers.keys()):
        layer_order[li] = [n["id"] for n in layers[li]]

    # Barycenter sweep (2 passes: down then up)
    for _sweep in range(4):
        for li in sorted(layers.keys()):
            if li == 0:
                continue
            prev_pos = {nid: idx for idx, nid in enumerate(layer_order[li - 1])}
            bary: dict[str, float] = {}
            for nid in layer_order[li]:
                parents = [p for p in adj_up.get(nid, []) if p in prev_pos]
                if parents:
                    bary[nid] = sum(prev_pos[p] for p in parents) / len(parents)
                else:
                    bary[nid] = layer_order[li].index(nid)
            layer_order[li] = sorted(layer_order[li], key=lambda nid: bary.get(nid, 0))

        for li in sorted(layers.keys(), reverse=True):
            if li == max(layers.keys()):
                continue
            next_pos = {nid: idx for idx, nid in enumerate(layer_order[li + 1])}
            bary = {}
            for nid in layer_order[li]:
                children = [c for c in adj_down.get(nid, []) if c in next_pos]
                if children:
                    bary[nid] = sum(next_pos[c] for c in children) / len(children)
                else:
                    bary[nid] = layer_order[li].index(nid)
            layer_order[li] = sorted(layer_order[li], key=lambda nid: bary.get(nid, 0))

    # Adaptive vertical spacing: reduce for tall diagrams
    num_layers = len(layer_order)
    if num_layers <= 4:
        v_spacing = BASE_V_SPACING
    elif num_layers <= 8:
        v_spacing = max(88, BASE_V_SPACING - (num_layers - 4) * 8)
    else:
        v_spacing = max(72, BASE_V_SPACING - 32 - (num_layers - 8) * 4)

    # Compute canvas width from widest row
    max_row_width = 0
    for li, nids in layer_order.items():
        row_w = sum(sizes[nid][0] for nid in nids) + H_SPACE * max(0, len(nids) - 1)
        max_row_width = max(max_row_width, row_w)

    canvas_w = max(max_row_width + 2 * MARGIN, 400)
    positions = {}

    for li in sorted(layer_order.keys()):
        nids = layer_order[li]
        layer_h = max((sizes[nid][1] for nid in nids), default=56)
        y_top = snap(MARGIN + li * v_spacing)

        row_total_w = sum(sizes[nid][0] for nid in nids)
        h_gaps = H_SPACE * max(0, len(nids) - 1)
        start_x = snap((canvas_w - row_total_w - h_gaps) / 2)

        cur_x = start_x
        for nid in nids:
            w, h = sizes[nid]
            y_offset = (layer_h - h) // 2
            positions[nid] = {"x": cur_x, "y": y_top + y_offset, "w": w, "h": h}
            cur_x = snap(cur_x + w + H_SPACE)

    return positions, canvas_w, [], {}  # no containers or routes in fallback layout


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

    elif shape == "memory":
        # Short-term memory: dashed rounded rect (per icons.md spec)
        ET.SubElement(g, "rect", {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h),
            "rx": "10", "ry": "10",
            "fill": fill, "stroke": stroke, "stroke-width": "1.5",
            "stroke-dasharray": "6,3",
        })

    elif shape in ("database", "cylinder"):
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

    elif shape in ("document", "doc"):
        # Folded-corner rectangle (document shape)
        fold = min(16, w * 0.12)
        d = (
            f"M {x} {y} "
            f"L {x + w - fold} {y} "
            f"L {x + w} {y + fold} "
            f"L {x + w} {y + h} "
            f"L {x} {y + h} Z"
        )
        ET.SubElement(g, "path", {
            "d": d,
            "fill": fill, "stroke": stroke, "stroke-width": "1.5",
        })
        # Fold triangle
        fold_d = (
            f"M {x + w - fold} {y} "
            f"L {x + w - fold} {y + fold} "
            f"L {x + w} {y + fold}"
        )
        ET.SubElement(g, "path", {
            "d": fold_d,
            "fill": stroke, "opacity": "0.2", "stroke": stroke, "stroke-width": "1",
        })

    elif shape in ("user_avatar", "user", "person"):
        # Stick figure: circle head + body lines
        head_r = min(12, h * 0.18)
        head_cy = y + head_r + 4
        body_top = head_cy + head_r + 2
        body_mid = y + h * 0.55
        body_bot = y + h - 6
        arm_y = body_top + (body_mid - body_top) * 0.3
        # Background rounded rect (clickable area)
        ET.SubElement(g, "rect", {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h),
            "rx": "12", "ry": "12",
            "fill": fill, "stroke": stroke, "stroke-width": "1.5",
        })
        # Head
        ET.SubElement(g, "circle", {
            "cx": str(cx), "cy": str(head_cy), "r": str(head_r),
            "fill": "none", "stroke": stroke, "stroke-width": "1.5",
        })
        # Body
        ET.SubElement(g, "line", {
            "x1": str(cx), "y1": str(body_top),
            "x2": str(cx), "y2": str(body_mid),
            "stroke": stroke, "stroke-width": "1.5",
        })
        # Arms
        ET.SubElement(g, "line", {
            "x1": str(cx - w * 0.2), "y1": str(arm_y),
            "x2": str(cx + w * 0.2), "y2": str(arm_y),
            "stroke": stroke, "stroke-width": "1.5",
        })
        # Legs
        ET.SubElement(g, "line", {
            "x1": str(cx), "y1": str(body_mid),
            "x2": str(cx - w * 0.15), "y2": str(body_bot),
            "stroke": stroke, "stroke-width": "1.5",
        })
        ET.SubElement(g, "line", {
            "x1": str(cx), "y1": str(body_mid),
            "x2": str(cx + w * 0.15), "y2": str(body_bot),
            "stroke": stroke, "stroke-width": "1.5",
        })

    elif shape in ("terminal", "browser"):
        # Rectangle with 3-dot titlebar
        ET.SubElement(g, "rect", {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h),
            "rx": "8", "ry": "8",
            "fill": fill, "stroke": stroke, "stroke-width": "1.5",
        })
        # Titlebar line
        bar_y = y + 14
        ET.SubElement(g, "line", {
            "x1": str(x), "y1": str(bar_y),
            "x2": str(x + w), "y2": str(bar_y),
            "stroke": stroke, "stroke-width": "1", "opacity": "0.4",
        })
        # 3 dots
        for i, color in enumerate(["#ef4444", "#f59e0b", "#22c55e"]):
            ET.SubElement(g, "circle", {
                "cx": str(x + 12 + i * 10), "cy": str(y + 7),
                "r": "2.5", "fill": color,
            })

    else:
        # fallback: plain rect
        ET.SubElement(g, "rect", {
            "x": str(x), "y": str(y), "width": str(w), "height": str(h),
            "rx": "8", "ry": "8",
            "fill": fill, "stroke": stroke, "stroke-width": "1.5",
        })

    # Label text (centred, with multiline support)
    sublabel = node.get("sublabel")
    lines = _label_lines(label)
    # Adjust vertical center if sublabel present
    label_cy = cy - (6 if sublabel else 0)

    if len(lines) == 1:
        txt = ET.SubElement(g, "text", {
            "x": str(cx),
            "y": str(label_cy),
            "text-anchor": "middle",
            "dominant-baseline": "central",
            "fill": text_color,
            "font-family": style["font"],
            "font-size": "13",
            "font-weight": "500",
        })
        txt.text = label
    else:
        total_h = len(lines) * LINE_H
        start_y = label_cy - total_h / 2 + LINE_H / 2
        txt = ET.SubElement(g, "text", {
            "x": str(cx),
            "text-anchor": "middle",
            "fill": text_color,
            "font-family": style["font"],
            "font-size": "13",
            "font-weight": "500",
        })
        for i, line in enumerate(lines):
            tspan = ET.SubElement(txt, "tspan", {
                "x": str(cx),
                "y": str(start_y + i * LINE_H),
            })
            tspan.text = line

    # Sublabel (smaller, muted text below main label)
    if sublabel:
        sub_y = label_cy + (len(lines) * LINE_H / 2 if len(lines) > 1 else 0) + 14
        ET.SubElement(g, "text", {
            "x": str(cx),
            "y": str(sub_y),
            "text-anchor": "middle",
            "dominant-baseline": "central",
            "fill": text_color,
            "font-family": style["font"],
            "font-size": "10",
            "font-weight": "400",
            "opacity": "0.6",
        }).text = sublabel

    # Icon badge (top-right corner, 16x16)
    icon_name = detect_icon(node)
    if icon_name and icon_name in ICONS:
        icon_size = 14
        icon_scale = icon_size / 24  # Lucide icons are 24x24
        # Position: top-right corner with padding
        icon_x = x + w - icon_size - 5
        icon_y = y + 4
        icon_g = ET.SubElement(g, "g", {
            "transform": f"translate({icon_x},{icon_y}) scale({icon_scale:.4f})",
            "fill": "none",
            "stroke": stroke,
            "stroke-width": "2",
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "opacity": "0.5",
        })
        for svg_el_str in ICONS[icon_name]:
            try:
                el = ET.fromstring(f"<svg xmlns='http://www.w3.org/2000/svg'>{svg_el_str}</svg>")
                for child in el:
                    # Strip namespace
                    child.tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    icon_g.append(child)
            except ET.ParseError:
                pass  # Skip malformed icon elements


# ---------------------------------------------------------------------------
# Edge drawing
# ---------------------------------------------------------------------------

def _marker_id(edge_type: str) -> str:
    return f"arrow-{edge_type}"


def add_defs(svg: ET.Element, used_types: set[str], style_name: str = "flat-icon") -> None:
    defs = ET.SubElement(svg, "defs")

    # Shadow filters per style
    STYLE_SHADOWS: dict[str, dict[str, str]] = {
        "glassmorphism": {"dx": "0", "dy": "4", "stdDeviation": "8", "color": "#00000040"},
        "claude-official": {"dx": "0", "dy": "2", "stdDeviation": "6", "color": "#00000012"},
        "openai-official": {"dx": "0", "dy": "1", "stdDeviation": "4", "color": "#00000010"},
        "dark-terminal": {"dx": "0", "dy": "0", "stdDeviation": "10", "color": "#6366f120"},
    }
    shadow_cfg = STYLE_SHADOWS.get(style_name)
    if shadow_cfg:
        filt = ET.SubElement(defs, "filter", {
            "id": "nodeShadow", "x": "-10%", "y": "-10%",
            "width": "120%", "height": "130%",
        })
        ET.SubElement(filt, "feDropShadow", {
            "dx": shadow_cfg["dx"], "dy": shadow_cfg["dy"],
            "stdDeviation": shadow_cfg["stdDeviation"],
            "flood-color": shadow_cfg["color"],
        })

    for etype in used_types:
        cfg = _get_edge_cfg(etype, style_name)
        # Proportional markers: thinner edges get smaller arrowheads
        edge_w = cfg["width"]
        scale = max(0.7, min(1.2, edge_w / 2))
        mw = round(10 * scale, 1)
        mh = round(7 * scale, 1)
        ref_x = round(9 * scale, 1)
        ref_y = round(3.5 * scale, 1)
        marker = ET.SubElement(defs, "marker", {
            "id": _marker_id(etype),
            "markerWidth": str(mw),
            "markerHeight": str(mh),
            "refX": str(ref_x),
            "refY": str(ref_y),
            "orient": "auto",
        })
        ET.SubElement(marker, "polygon", {
            "points": f"0 0, {mw} {ref_y}, 0 {mh}",
            "fill": cfg["color"],
        })


def _port(pos: dict[str, int], side: str, offset: float = 0) -> tuple[float, float]:
    """Return (x, y) for a connection port on a node.
    offset: horizontal shift for top/bottom ports, vertical for left/right (for port spreading).
    """
    x, y, w, h = pos["x"], pos["y"], pos["w"], pos["h"]
    cx, cy = x + w / 2, y + h / 2
    if side == "top":
        return cx + offset, y
    elif side == "bottom":
        return cx + offset, y + h
    elif side == "left":
        return x, cy + offset
    elif side == "right":
        return x + w, cy + offset
    return cx + offset, y + h  # default: bottom


# Track port usage for spreading
_port_usage: dict[tuple[str, str], int] = {}  # (node_id, side) -> count


def _get_port_offset(node_id: str, side: str, node_w: float) -> float:
    """Get offset for port spreading when multiple edges connect to same port."""
    key = (node_id, side)
    count = _port_usage.get(key, 0)
    _port_usage[key] = count + 1
    if count == 0:
        return 0
    # Spread ports: alternate left/right of center, max ±40% of node width
    max_offset = node_w * 0.35
    direction = 1 if count % 2 == 1 else -1
    magnitude = ((count + 1) // 2) * 16
    return direction * min(magnitude, max_offset)


def _detect_direction(
    src: dict[str, int], dst: dict[str, int], is_feedback: bool = False
) -> tuple[str, str]:
    """Auto-detect best source/target ports based on relative positions."""
    scx = src["x"] + src["w"] / 2
    scy = src["y"] + src["h"] / 2
    dcx = dst["x"] + dst["w"] / 2
    dcy = dst["y"] + dst["h"] / 2

    dx = dcx - scx
    dy = dcy - scy

    # Feedback/backward edges: always route around the right side
    if is_feedback or dy < -30:
        return "right", "right"

    # Same layer (horizontal) — use left/right
    if abs(dy) < 30:
        if dx > 0:
            return "right", "left"
        else:
            return "left", "right"

    # Forward (down) — use bottom/top
    if dy > 0:
        if abs(dx) > abs(dy) * 1.5:
            return ("right", "left") if dx > 0 else ("left", "right")
        return "bottom", "top"

    return "bottom", "top"


def _build_orthogonal_path(waypoints: list[tuple[int, int]], corner_radius: float = 8) -> str:
    """Build SVG path from orthogonal waypoints with rounded corners.

    waypoints: [(x0,y0), (x1,y1), ..., (xn,yn)] — alternating horizontal/vertical segments.
    corner_radius: radius for smoothing corners between segments.
    """
    if len(waypoints) < 2:
        return ""
    if len(waypoints) == 2:
        return f"M {waypoints[0][0]} {waypoints[0][1]} L {waypoints[1][0]} {waypoints[1][1]}"

    parts: list[str] = [f"M {waypoints[0][0]} {waypoints[0][1]}"]
    for i in range(1, len(waypoints) - 1):
        px, py = waypoints[i - 1]
        cx, cy = waypoints[i]
        nx, ny = waypoints[i + 1]

        # Vector from prev to corner, and corner to next
        dx1 = cx - px
        dy1 = cy - py
        dx2 = nx - cx
        dy2 = ny - cy
        len1 = (dx1 * dx1 + dy1 * dy1) ** 0.5 or 1
        len2 = (dx2 * dx2 + dy2 * dy2) ** 0.5 or 1

        # Clamp radius to half of each segment length
        r = min(corner_radius, len1 / 2, len2 / 2)

        # Start of corner: back off from (cx,cy) along prev direction
        sx = cx - dx1 / len1 * r
        sy = cy - dy1 / len1 * r
        # End of corner: forward from (cx,cy) along next direction
        ex = cx + dx2 / len2 * r
        ey = cy + dy2 / len2 * r

        parts.append(f"L {sx:.1f} {sy:.1f}")
        parts.append(f"Q {cx} {cy} {ex:.1f} {ey:.1f}")

    # Final segment to last waypoint
    parts.append(f"L {waypoints[-1][0]} {waypoints[-1][1]}")
    return " ".join(parts)


def _build_path(x1: float, y1: float, x2: float, y2: float,
                src_port: str, dst_port: str, is_feedback: bool = False) -> str:
    """Build a smooth cubic bezier path based on port directions."""

    # Feedback loops: clean arc around the right side
    if is_feedback and src_port == "right" and dst_port == "right":
        # Route: source right → loop right → target right
        loop_x = max(x1, x2) + 60  # go 60px to the right of rightmost point
        mid_y = (y1 + y2) / 2
        return (f"M {x1:.1f} {y1:.1f} "
                f"C {loop_x:.1f} {y1:.1f}, "
                f"{loop_x:.1f} {y2:.1f}, "
                f"{x2:.1f} {y2:.1f}")

    vertical_src = src_port in ("top", "bottom")
    vertical_dst = dst_port in ("top", "bottom")

    if vertical_src and vertical_dst:
        # Normal top-to-bottom or bottom-to-top flow
        cp_offset = max(40, abs(y2 - y1) * 0.4)
        sign_s = 1 if src_port == "bottom" else -1
        sign_d = -1 if dst_port == "top" else 1
        return (f"M {x1:.1f} {y1:.1f} "
                f"C {x1:.1f} {y1 + sign_s * cp_offset:.1f}, "
                f"{x2:.1f} {y2 + sign_d * cp_offset:.1f}, "
                f"{x2:.1f} {y2:.1f}")

    if not vertical_src and not vertical_dst:
        # Horizontal — left/right to left/right (non-feedback)
        cp_offset = max(40, abs(x2 - x1) * 0.4)
        sign_s = 1 if src_port == "right" else -1
        sign_d = -1 if dst_port == "left" else 1
        return (f"M {x1:.1f} {y1:.1f} "
                f"C {x1 + sign_s * cp_offset:.1f} {y1:.1f}, "
                f"{x2 + sign_d * cp_offset:.1f} {y2:.1f}, "
                f"{x2:.1f} {y2:.1f}")

    # Mixed: one vertical, one horizontal — smooth L-shaped curve
    if vertical_src:
        sign_s = 1 if src_port == "bottom" else -1
        mid_y = y1 + sign_s * max(40, abs(y2 - y1) * 0.5)
        return (f"M {x1:.1f} {y1:.1f} "
                f"C {x1:.1f} {mid_y:.1f}, "
                f"{x1:.1f} {y2:.1f}, "
                f"{x2:.1f} {y2:.1f}")
    else:
        sign_d = -1 if dst_port == "top" else 1
        mid_x = x1 + (1 if src_port == "right" else -1) * max(40, abs(x2 - x1) * 0.5)
        return (f"M {x1:.1f} {y1:.1f} "
                f"C {mid_x:.1f} {y1:.1f}, "
                f"{x2:.1f} {y1:.1f}, "
                f"{x2:.1f} {y2:.1f}")


# Track placed label positions to avoid label-to-label collisions
_placed_labels: list[tuple[float, float, float, float]] = []


def _label_position(x1: float, y1: float, x2: float, y2: float,
                    positions: dict[str, dict[str, int]], edge: dict) -> tuple[float, float]:
    """Find a label position that avoids overlapping nodes AND other labels."""
    lx = (x1 + x2) / 2
    ly = (y1 + y2) / 2

    # Check if midpoint overlaps any node
    for nid, pos in positions.items():
        from_id = edge.get("from") or edge.get("source")
        to_id = edge.get("to") or edge.get("target")
        if nid in (from_id, to_id):
            continue
        nx, ny = pos["x"] - 10, pos["y"] - 10
        nr, nb = pos["x"] + pos["w"] + 10, pos["y"] + pos["h"] + 10
        if nx < lx < nr and ny < ly < nb:
            ncx = pos["x"] + pos["w"] / 2
            if lx < ncx:
                lx = nx - 30
            else:
                lx = nr + 30
            break

    # Check label-to-label collision: shift vertically if overlap
    label_text = edge.get("label", "")
    lw = _text_width(label_text) + 12
    lh = 18
    for attempt in range(5):
        collision = False
        for (px, py, pw, ph) in _placed_labels:
            ox = max(0, min(lx + lw / 2, px + pw / 2) - max(lx - lw / 2, px - pw / 2))
            oy = max(0, min(ly + lh / 2, py + ph / 2) - max(ly - lh / 2, py - ph / 2))
            if ox > 0 and oy > 0:
                collision = True
                ly += 20  # shift down by 20px
                break
        if not collision:
            break

    _placed_labels.append((lx, ly, lw, lh))
    return lx, ly


def draw_edge(
    parent: ET.Element,
    edge: dict,
    positions: dict[str, dict[str, int]],
    style: dict[str, str],
    style_name: str = "flat-icon",
    edge_routes: dict[tuple[str, str], list[tuple[int, int]]] | None = None,
) -> None:
    from_id = edge.get("from") or edge.get("source")
    to_id = edge.get("to") or edge.get("target")

    if from_id not in positions or to_id not in positions:
        return

    src = positions[from_id]
    dst = positions[to_id]

    etype = edge.get("type", "primary")
    cfg = _get_edge_cfg(etype, style_name)
    is_feedback = etype == "feedback"

    # Try orthogonal routing from engine first
    route = None
    if edge_routes:
        route = edge_routes.get((from_id, to_id))

    if route and len(route) >= 2 and not is_feedback:
        # Use orthogonal waypoints from engine
        path_d = _build_orthogonal_path(route, corner_radius=10)
        x1, y1 = route[0]
        x2, y2 = route[-1]
    else:
        # Fallback: bezier routing (for feedback or when engine unavailable)
        src_port, dst_port = _detect_direction(src, dst, is_feedback)
        src_offset = _get_port_offset(from_id, src_port, src["w"])
        dst_offset = _get_port_offset(to_id, dst_port, dst["w"])
        x1, y1 = _port(src, src_port, src_offset)
        x2, y2 = _port(dst, dst_port, dst_offset)
        path_d = _build_path(x1, y1, x2, y2, src_port, dst_port, is_feedback)

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

    # Optional label with smart placement
    label = edge.get("label")
    if label:
        # For orthogonal routes: place label on midpoint of longest segment
        # (avoids placing label on bends or very short segments)
        if route and len(route) >= 3:
            longest_len = 0
            longest_mid = ((x1 + x2) / 2, (y1 + y2) / 2)
            for i in range(len(route) - 1):
                p1, p2 = route[i], route[i + 1]
                seg_len = abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])  # Manhattan
                if seg_len > longest_len:
                    longest_len = seg_len
                    longest_mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            lx, ly = longest_mid
            # Still check node/label collisions
            lx, ly = _label_position(lx, ly, lx, ly, positions, edge)
        else:
            lx, ly = _label_position(x1, y1, x2, y2, positions, edge)
        pad_x = 6
        lw = _text_width(label) + pad_x * 2
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

def _auto_assign_layers(nodes: list[dict], edges: list[dict]) -> None:
    """Auto-assign layers via topological sort when nodes lack 'layer' field."""
    if all("layer" in n for n in nodes):
        return  # All have explicit layers

    # Build adjacency
    children: dict[str, list[str]] = {}
    parents: dict[str, list[str]] = {}
    node_ids = {n["id"] for n in nodes}
    for e in edges:
        src = e.get("from") or e.get("source", "")
        tgt = e.get("to") or e.get("target", "")
        if src in node_ids and tgt in node_ids and e.get("type") != "feedback":
            children.setdefault(src, []).append(tgt)
            parents.setdefault(tgt, []).append(src)

    # Find roots (no parents)
    all_ids = {n["id"] for n in nodes}
    roots = all_ids - set(parents.keys())
    if not roots:
        # Pure cycle: pick first node as root (breaks the cycle for BFS)
        roots = {nodes[0]["id"]}

    # BFS layer assignment — each node visited at most once (cycle-safe)
    layers: dict[str, int] = {}
    queue = list(roots)
    for r in roots:
        layers[r] = 0
    visited = set(roots)
    while queue:
        nid = queue.pop(0)
        for child in children.get(nid, []):
            if child not in visited:
                visited.add(child)
                layers[child] = layers[nid] + 1
                queue.append(child)

    # Apply to nodes
    node_map = {n["id"]: n for n in nodes}
    for nid, layer in layers.items():
        if nid in node_map and "layer" not in node_map[nid]:
            node_map[nid]["layer"] = layer

    # Assign layer 0 to any remaining unassigned nodes
    for n in nodes:
        if "layer" not in n:
            n["layer"] = 0


def build_svg(data: dict, style_name: str = "flat-icon") -> str:
    global _placed_labels, _port_usage
    _placed_labels = []  # Reset label collision tracker
    _port_usage = {}     # Reset port spreading tracker

    style = STYLES.get(style_name, STYLES["flat-icon"])

    nodes: list[dict] = data.get("nodes", [])
    edges: list[dict] = data.get("edges", [])
    containers: list[dict] = data.get("containers", [])
    title: str | None = data.get("title")

    if not nodes:
        raise ValueError("No nodes provided in input JSON.")

    # Auto-assign layers if not provided (topological sort from edges)
    _auto_assign_layers(nodes, edges)

    positions, canvas_w, positioned_containers, edge_routes = compute_layout(nodes, edges, containers)

    title_offset = 36 if title else 0
    if title:
        for nid in positions:
            positions[nid]["y"] += title_offset
        # Also offset containers
        for c in positioned_containers:
            c["y"] = c.get("y", 0) + title_offset
        # Also offset edge route waypoints
        if edge_routes:
            shifted_routes: dict[tuple[str, str], list[tuple[int, int]]] = {}
            for key, wps in edge_routes.items():
                shifted_routes[key] = [(x, y + title_offset) for x, y in wps]
            edge_routes = shifted_routes

    # Canvas sizing from actual content bounds
    max_x = max(p["x"] + p["w"] for p in positions.values())
    max_y = max(p["y"] + p["h"] for p in positions.values())
    canvas_w = max(canvas_w, snap(max_x + MARGIN * 2))
    canvas_h = snap(max_y + MARGIN * 2)

    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "width": str(canvas_w),
        "height": str(canvas_h),
        "viewBox": f"0 0 {canvas_w} {canvas_h}",
    })

    # Background (enhanced for glassmorphism with gradient + glow)
    if style_name == "glassmorphism":
        bg_defs = svg.find("defs") or ET.SubElement(svg, "defs")
        # Diagonal gradient
        grad = ET.SubElement(bg_defs, "linearGradient", {
            "id": "bgGrad", "x1": "0%", "y1": "0%", "x2": "100%", "y2": "100%",
        })
        ET.SubElement(grad, "stop", {"offset": "0%", "stop-color": "#0d1117"})
        ET.SubElement(grad, "stop", {"offset": "50%", "stop-color": "#161b22"})
        ET.SubElement(grad, "stop", {"offset": "100%", "stop-color": "#0d1117"})
        ET.SubElement(svg, "rect", {"width": "100%", "height": "100%", "fill": "url(#bgGrad)"})
        # Ambient glow spots
        for gid, cx_pct, cy_pct, color in [
            ("glowBlue", "30%", "35%", "rgba(88,166,255,0.12)"),
            ("glowPurple", "70%", "65%", "rgba(188,140,255,0.10)"),
        ]:
            rg = ET.SubElement(bg_defs, "radialGradient", {
                "id": gid, "cx": cx_pct, "cy": cy_pct, "r": "40%",
            })
            ET.SubElement(rg, "stop", {"offset": "0%", "stop-color": color})
            ET.SubElement(rg, "stop", {"offset": "100%", "stop-color": "rgba(0,0,0,0)"})
            ET.SubElement(svg, "rect", {"width": "100%", "height": "100%", "fill": f"url(#{gid})"})
    else:
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

    # Arrow markers + shadow defs
    used_types = {e.get("type", "primary") for e in edges}
    add_defs(svg, used_types, style_name)

    # Check if shadow filter was added
    has_shadow = style_name in ("glassmorphism", "claude-official", "openai-official", "dark-terminal")

    # Containers (drawn first — background layer, behind edges and nodes)
    if positioned_containers:
        container_group = ET.SubElement(svg, "g", {"class": "containers"})
        for c in positioned_containers:
            cx = c.get("x", 0)
            cy = c.get("y", 0)
            cw = c.get("width", 200)
            ch = c.get("height", 100)
            clabel = c.get("label", "")
            cstroke = c.get("stroke", style["node_stroke"])
            cfill = c.get("fill", "none")

            # Container background rect (dashed border)
            ET.SubElement(container_group, "rect", {
                "x": str(cx), "y": str(cy),
                "width": str(cw), "height": str(ch),
                "rx": "8", "ry": "8",
                "fill": cfill if cfill != "none" else (style["bg"] if style["bg"] != "#ffffff" else "none"),
                "fill-opacity": "0.06" if cfill == "none" else "1",
                "stroke": cstroke,
                "stroke-width": "1",
                "stroke-dasharray": "6,4",
            })

            # Container label (top-left, uppercase, small)
            if clabel:
                ET.SubElement(container_group, "text", {
                    "x": str(cx + 12),
                    "y": str(cy + 18),
                    "fill": cstroke,
                    "font-family": style["font"],
                    "font-size": "10",
                    "font-weight": "600",
                    "letter-spacing": "0.06em",
                }).text = clabel.upper()

    # Edges (drawn before nodes so they appear behind)
    edge_group = ET.SubElement(svg, "g", {"class": "edges"})
    for edge in edges:
        draw_edge(edge_group, edge, positions, style, style_name, edge_routes)

    # Nodes (with shadow filter if available)
    node_attrs: dict[str, str] = {"class": "nodes"}
    if has_shadow:
        node_attrs["filter"] = "url(#nodeShadow)"
    node_group = ET.SubElement(svg, "g", node_attrs)
    node_map = {n["id"]: n for n in nodes}
    for nid, pos in positions.items():
        draw_node(node_group, node_map[nid], pos, style)

    # Auto-legend when 2+ arrow types are used (rule: tech-diagram.md)
    if len(used_types) >= 2:
        LEGEND_LABELS = {
            "primary": "Data flow",
            "control": "Control",
            "read": "Read",
            "write": "Write",
            "async": "Async",
            "feedback": "Feedback",
        }

        # Calculate legend dimensions first
        sorted_types = sorted(used_types)
        item_widths = []
        for etype in sorted_types:
            label = LEGEND_LABELS.get(etype, etype.capitalize())
            item_widths.append(36 + _text_width(label) + 20)  # line(36) + text + gap
        total_items_w = sum(item_widths)
        legend_box_w = total_items_w + 80  # padding + "Legend" label
        legend_box_h = 36

        # Extend canvas if legend is wider than current canvas
        required_canvas_w = legend_box_w + 24 + 2 * MARGIN
        if required_canvas_w > canvas_w:
            canvas_w = snap(required_canvas_w)

        legend_x = max(MARGIN, (canvas_w - legend_box_w) / 2)  # center horizontally
        legend_y = canvas_h + 8  # below content with gap
        canvas_h += legend_box_h + 24  # extend canvas

        lg = ET.SubElement(svg, "g", {"class": "legend"})

        # Background box
        ET.SubElement(lg, "rect", {
            "x": str(legend_x - 12),
            "y": str(legend_y - 4),
            "width": str(legend_box_w + 24),
            "height": str(legend_box_h),
            "rx": "6",
            "fill": style["bg"],
            "stroke": style["node_stroke"],
            "stroke-width": "0.75",
            "opacity": "0.9",
        })

        # "Legend" title
        ET.SubElement(lg, "text", {
            "x": str(legend_x), "y": str(legend_y + 15),
            "fill": style["text"], "font-family": style["font"],
            "font-size": "10", "font-weight": "700",
            "opacity": "0.7",
        }).text = "Legend"

        cur_x = legend_x + 52
        for etype in sorted_types:
            cfg = _get_edge_cfg(etype, style_name)
            label = LEGEND_LABELS.get(etype, etype.capitalize())
            line_y = legend_y + 15

            # Line sample (longer: 32px, with arrowhead marker)
            line_attrs: dict[str, str] = {
                "x1": str(cur_x), "y1": str(line_y),
                "x2": str(cur_x + 32), "y2": str(line_y),
                "stroke": cfg["color"], "stroke-width": str(max(2, cfg["width"])),
                "stroke-linecap": "round",
            }
            if cfg["dash"]:
                line_attrs["stroke-dasharray"] = cfg["dash"]
            ET.SubElement(lg, "line", line_attrs)

            # Label text
            ET.SubElement(lg, "text", {
                "x": str(cur_x + 38), "y": str(line_y + 4),
                "fill": cfg["color"], "font-family": style["font"],
                "font-size": "10", "font-weight": "500",
            }).text = label
            cur_x += 36 + _text_width(label) + 20

    # Update canvas size (legend may have extended it)
    svg.set("height", str(canvas_h))
    svg.set("viewBox", f"0 0 {canvas_w} {canvas_h}")

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
# Output path resolution
# ---------------------------------------------------------------------------

def _resolve_output(output_path: str, output_dir: str | None = None) -> str:
    """Resolve output path. Uses --output-dir if given, else .agents-output/diagram/svg/."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
    abs_out = os.path.abspath(output_path)
    agents_dir = os.path.join(project_root, ".agents")

    # If absolute path outside .agents/ — respect it
    if os.path.isabs(output_path) and not abs_out.startswith(agents_dir):
        os.makedirs(os.path.dirname(abs_out) or ".", exist_ok=True)
        return output_path

    # Use explicit --output-dir or default to .agents-output/diagram/svg/
    if output_dir:
        out_dir = os.path.join(project_root, output_dir)
    else:
        out_dir = os.path.join(project_root, ".agents-output", "diagram", "svg")

    os.makedirs(out_dir, exist_ok=True)
    resolved = os.path.join(out_dir, os.path.basename(output_path))

    # Safety net: never overwrite existing files — append counter
    if os.path.exists(resolved):
        base, ext = os.path.splitext(resolved)
        counter = 1
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        resolved = f"{base}_{counter}{ext}"
        print(f"File exists, renamed to: {resolved}", file=sys.stderr)

    print(f"Output: {resolved}", file=sys.stderr)
    return resolved


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
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        help="Output directory relative to project root (e.g. .agents-output/visualize/svg)",
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

    # Pre-flight validation
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    if len(nodes) < 2:
        print(f"Error: need at least 2 nodes, got {len(nodes)}.", file=sys.stderr)
        return 1
    if len(edges) == 0:
        print("Error: no edges defined. Diagram would have no connections.", file=sys.stderr)
        return 1

    # Check for duplicate node IDs
    seen_ids: set[str] = set()
    dup_ids: list[str] = []
    for n in nodes:
        nid = n.get("id")
        if nid is None:
            print(f"Error: node missing 'id' field: {n}", file=sys.stderr)
            return 1
        if nid in seen_ids:
            dup_ids.append(nid)
        seen_ids.add(nid)
    if dup_ids:
        print(f"Error: duplicate node IDs: {dup_ids}. Each node must have a unique id.", file=sys.stderr)
        return 1

    # Check for self-loops on non-feedback edges (would create visual noise)
    for e in edges:
        src = e.get("from") or e.get("source")
        tgt = e.get("to") or e.get("target")
        if src == tgt and e.get("type") != "feedback":
            print(f"Warning: self-loop on node '{src}' (edge type '{e.get('type','primary')}'). Consider type='feedback' or removing.", file=sys.stderr)

    node_ids = {n.get("id") for n in nodes}
    for e in edges:
        src = e.get("from") or e.get("source")
        tgt = e.get("to") or e.get("target")
        if src not in node_ids:
            print(f"Error: edge references unknown source node '{src}'. Valid IDs: {node_ids}", file=sys.stderr)
            return 1
        if tgt not in node_ids:
            print(f"Error: edge references unknown target node '{tgt}'. Valid IDs: {node_ids}", file=sys.stderr)
            return 1

    # Warn if input has features this script doesn't support
    if "containers" in data:
        print(f"Info: {len(data['containers'])} container(s) detected — using grouped layout.", file=sys.stderr)
    if any("x" in n and "y" in n for n in nodes):
        print("Warning: svg-gen.py ignores absolute x/y positions. It uses auto-layout based on 'layer' field.", file=sys.stderr)

    # Redirect output (respects --output-dir if given)
    args.output = _resolve_output(args.output, args.output_dir)

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
