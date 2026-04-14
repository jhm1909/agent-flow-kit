"""
Layout engine bridge — converts JSON diagram data to positioned nodes/edges
using the vendored Sugiyama (grandalf) algorithm.

Usage:
    from layout.engine import compute_layout
    positioned = compute_layout(diagram_json)
    # Returns: {"nodes": [...with x,y...], "edges": [...with route points...], "width": N, "height": N}
"""
from __future__ import annotations

import math
from typing import Any

from .graphs import Graph, Vertex, Edge
from .layouts import SugiyamaLayout, VertexViewer
from .routing import EdgeViewer, route_with_lines


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_NODE_W = 140
DEFAULT_NODE_H = 56
CHAR_WIDTH = 7.5  # approximate px per character at 13px font
MIN_NODE_W = 80
MAX_NODE_W = 300
H_SPACE = 80   # horizontal gap between nodes (spec: 80px)
V_SPACE = 120  # vertical gap between layers (spec: 120px)
MARGIN = 40    # canvas margin (spec: 40px)


def _estimate_text_width(label: str, font_size: float = 13) -> float:
    """Estimate text width based on character count and font size."""
    return len(label) * CHAR_WIDTH * (font_size / 13)


def _auto_node_width(label: str) -> int:
    """Calculate appropriate node width for a label."""
    text_w = _estimate_text_width(label)
    padding = 24  # 12px each side
    w = max(MIN_NODE_W, min(MAX_NODE_W, int(text_w + padding)))
    # Snap to 8px grid
    return ((w + 7) // 8) * 8


def _snap(v: float, grid: int = 8) -> int:
    """Snap value to grid."""
    return round(v / grid) * grid


# ---------------------------------------------------------------------------
# Container layout (compound graph support)
# ---------------------------------------------------------------------------

def _layout_container_contents(container_nodes: list[dict], container_edges: list[dict]) -> dict:
    """Layout nodes inside a container as a sub-graph, return bounding box."""
    if not container_nodes:
        return {"width": 0, "height": 0, "nodes": []}

    result = _layout_flat(container_nodes, container_edges)
    return result


def _layout_flat(nodes: list[dict], edges: list[dict]) -> dict:
    """
    Core layout: position nodes and route edges using Sugiyama algorithm.
    Returns dict with positioned nodes, routed edges, and canvas dimensions.
    """
    if not nodes:
        return {"nodes": [], "edges": edges, "width": 0, "height": 0}

    # Build grandalf graph
    vertex_map: dict[str, Vertex] = {}
    for n in nodes:
        nid = n.get("id", "")
        label = n.get("label", nid)
        w = n.get("width") or _auto_node_width(label)
        h = n.get("height") or DEFAULT_NODE_H

        v = Vertex(data=n)
        v.view = VertexViewer(w=int(w), h=int(h))
        vertex_map[nid] = v

    edge_objects: list[Edge] = []
    for e in edges:
        src_id = e.get("from", e.get("source", ""))
        dst_id = e.get("to", e.get("target", ""))
        if src_id in vertex_map and dst_id in vertex_map:
            edge_obj = Edge(vertex_map[src_id], vertex_map[dst_id])
            edge_obj.view = EdgeViewer()
            edge_obj.data = e
            edge_objects.append(edge_obj)

    if not vertex_map:
        return {"nodes": [], "edges": edges, "width": 0, "height": 0}

    g = Graph(list(vertex_map.values()), edge_objects, directed=True)

    # Layout each connected component
    for component in g.C:
        sug = SugiyamaLayout(component)
        sug.xspace = H_SPACE
        sug.yspace = V_SPACE
        sug.init_all()
        sug.draw()

    # Read positions back and normalize (shift so min_x, min_y start at MARGIN)
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for v in vertex_map.values():
        if v.view.xy is None:
            continue
        cx, cy = v.view.xy
        w, h = v.view.w, v.view.h
        # grandalf gives center coordinates — convert to top-left
        x = cx - w / 2
        y = cy - h / 2
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x + w)
        max_y = max(max_y, y + h)

    # Normalize: shift everything so top-left is at MARGIN
    offset_x = MARGIN - min_x if min_x != float("inf") else 0
    offset_y = MARGIN - min_y if min_y != float("inf") else 0

    positioned_nodes = []
    for nid, v in vertex_map.items():
        if v.view.xy is None:
            continue
        cx, cy = v.view.xy
        w, h = v.view.w, v.view.h
        x = _snap(cx - w / 2 + offset_x)
        y = _snap(cy - h / 2 + offset_y)

        node_data = dict(v.data)  # copy original
        node_data["x"] = x
        node_data["y"] = y
        node_data["width"] = w
        node_data["height"] = h
        positioned_nodes.append(node_data)

    # Edge routing: compute connection points
    positioned_edges = []
    for eo in edge_objects:
        src_v = eo.v[0]
        dst_v = eo.v[1]
        if src_v.view.xy is None or dst_v.view.xy is None:
            continue

        sx, sy = src_v.view.xy
        dx, dy = dst_v.view.xy
        sw, sh = src_v.view.w, src_v.view.h
        dw, dh = dst_v.view.w, dst_v.view.h

        # Source bottom center, target top center (hierarchical)
        x1 = _snap(sx + offset_x)
        y1 = _snap(sy + sh / 2 + offset_y)
        x2 = _snap(dx + offset_x)
        y2 = _snap(dy - dh / 2 + offset_y)

        edge_data = dict(eo.data) if eo.data else {}
        edge_data["_route"] = [(x1, y1), (x2, y2)]
        positioned_edges.append(edge_data)

    canvas_w = _snap(max_x + offset_x + MARGIN) if max_x != float("-inf") else 960
    canvas_h = _snap(max_y + offset_y + MARGIN) if max_y != float("-inf") else 600

    return {
        "nodes": positioned_nodes,
        "edges": positioned_edges,
        "width": max(960, canvas_w),
        "height": max(400, canvas_h),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_layout(data: dict[str, Any]) -> dict[str, Any]:
    """
    Compute layout for a diagram JSON structure.

    Input: {"nodes": [...], "edges": [...], "title": "...", "containers": [...]}
    Output: same structure but nodes have x, y, width, height; edges have _route points

    If nodes already have x,y (absolute positioning), they are kept as-is.
    """
    nodes = data.get("nodes", [])
    edges = data.get("edges", data.get("arrows", []))
    containers = data.get("containers", [])

    # Check if nodes already have absolute positions
    has_positions = all("x" in n and "y" in n for n in nodes) if nodes else False

    if has_positions:
        # Already positioned — just pass through
        return data

    # No positions → compute layout
    result = _layout_flat(nodes, edges)

    # Rebuild output
    output = dict(data)
    output["nodes"] = result["nodes"]
    output["edges"] = result["edges"]
    output["_canvas_width"] = result["width"]
    output["_canvas_height"] = result["height"]

    return output
