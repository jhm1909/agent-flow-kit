"""
Layout engine bridge — converts JSON diagram data to positioned nodes/edges
using the vendored Sugiyama (grandalf) algorithm.

Features:
- Sugiyama hierarchical layout (no overlap guaranteed)
- Container/compound graph support (swim lanes)
- Orthogonal edge routing (L-shaped paths avoiding obstacles)
- Auto node width based on label length

Usage:
    from layout.engine import compute_layout
    positioned = compute_layout(diagram_json)
"""
from __future__ import annotations

import math
from typing import Any

from .graphs import Graph, Vertex, Edge
from .layouts import SugiyamaLayout, VertexViewer
from .routing import EdgeViewer


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_NODE_W = 140
DEFAULT_NODE_H = 56
LINE_H = 18            # height per line of text
PAD_Y = 20             # vertical padding inside node
CHAR_W_LATIN = 7.5     # approximate px per Latin character at 13px font
CHAR_W_CJK = 13.0      # CJK (Korean, Chinese, Japanese) chars are ~1.7x wider
MIN_NODE_W = 80
MAX_NODE_W = 360        # wider max for CJK text
H_SPACE = 80            # horizontal gap between nodes (spec: 80px)
V_SPACE = 120           # vertical gap between layers (spec: 120px)
MARGIN = 40             # canvas margin (spec: 40px)
CONTAINER_PAD = 24      # padding inside container around its contents
CONTAINER_HEADER = 32   # height reserved for container label
ROUTE_CLEARANCE = 20    # minimum clearance from node edge for routing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _estimate_text_width(label: str, font_size: float = 13) -> float:
    """Estimate pixel width accounting for CJK/wide characters."""
    scale = font_size / 13
    return sum((CHAR_W_CJK if _is_wide_char(ch) else CHAR_W_LATIN) * scale for ch in label)


def _auto_node_width(label: str, shape: str = "rect") -> int:
    # Handle multiline labels — use widest line
    lines = label.split("\n") if label else [""]
    text_w = max(_estimate_text_width(line) for line in lines)
    # Shape-aware: hexagons/diamonds need wider bounding box for same text
    if shape in ("diamond", "decision"):
        area_w = text_w / 0.5 + 24  # diamond usable ≈ 50%
    elif shape in ("hexagon", "agent"):
        area_w = text_w / 0.7 + 24  # hexagon usable ≈ 70%
    else:
        area_w = text_w + 24 * 2
    w = max(MIN_NODE_W, min(MAX_NODE_W, int(area_w)))
    return ((w + 7) // 8) * 8


def _snap(v: float, grid: int = 8) -> int:
    return round(v / grid) * grid


# ---------------------------------------------------------------------------
# Orthogonal edge routing
# ---------------------------------------------------------------------------

def _route_orthogonal(
    x1: float, y1: float, x2: float, y2: float,
    node_bounds: list[tuple[float, float, float, float]],
) -> list[tuple[int, int]]:
    """
    Route an edge from (x1,y1) to (x2,y2) using orthogonal (L-shaped) segments.
    Avoids crossing through node bounding boxes.

    Returns list of (x,y) waypoints including start and end.
    """
    points = []
    sx, sy = _snap(x1), _snap(y1)
    ex, ey = _snap(x2), _snap(y2)

    if abs(sx - ex) < 4:
        # Vertically aligned — straight line
        return [(sx, sy), (ex, ey)]

    # Try simple L-route: down then across then down
    mid_y = _snap((sy + ey) / 2)

    # Check if midpoint horizontal segment hits any node
    collision = False
    for bx, by, bw, bh in node_bounds:
        # Horizontal segment at mid_y from sx to ex
        if by <= mid_y <= by + bh:
            seg_left = min(sx, ex) - ROUTE_CLEARANCE
            seg_right = max(sx, ex) + ROUTE_CLEARANCE
            if bx < seg_right and bx + bw > seg_left:
                collision = True
                break

    if not collision:
        # Simple L-route works
        points = [
            (sx, sy),
            (sx, mid_y),
            (ex, mid_y),
            (ex, ey),
        ]
    else:
        # Route around: go wider
        all_rights = [bx + bw for bx, _, bw, _ in node_bounds]
        detour_x = _snap(max(all_rights) + ROUTE_CLEARANCE * 2) if all_rights else ex + 60

        points = [
            (sx, sy),
            (sx, mid_y),
            (detour_x, mid_y),
            (detour_x, ey),
            (ex, ey),
        ]

    # Simplify: remove redundant colinear points
    return _simplify_route(points)


def _simplify_route(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Remove colinear intermediate points."""
    if len(points) <= 2:
        return points

    result = [points[0]]
    for i in range(1, len(points) - 1):
        px, py = points[i - 1]
        cx, cy = points[i]
        nx, ny = points[i + 1]
        # Keep point if direction changes
        if not ((px == cx == nx) or (py == cy == ny)):
            result.append(points[i])
    result.append(points[-1])
    return result


# ---------------------------------------------------------------------------
# Container / compound graph layout
# ---------------------------------------------------------------------------

def _group_by_container(
    nodes: list[dict], containers: list[dict]
) -> dict[str | None, list[dict]]:
    """
    Group nodes by their container. Nodes with 'container' field go into
    that group. Nodes without go into None group (top level).
    """
    groups: dict[str | None, list[dict]] = {None: []}
    for c in containers:
        cid = c.get("id", c.get("label", f"container-{id(c)}"))
        groups[cid] = []

    for n in nodes:
        cid = n.get("container")
        if cid and cid in groups:
            groups[cid].append(n)
        else:
            groups[None].append(n)

    return groups


def _layout_with_containers(
    nodes: list[dict], edges: list[dict], containers: list[dict]
) -> dict:
    """
    Layout with container support using collapse-and-expand:
    1. Layout each container's contents as a sub-graph
    2. Replace each container with a single super-node (sized to its contents)
    3. Layout the top-level graph
    4. Expand containers back and offset their contents
    """
    if not containers:
        return _layout_flat(nodes, edges)

    groups = _group_by_container(nodes, containers)
    container_map: dict[str, dict] = {}

    # Step 1: layout each container's contents
    for c in containers:
        cid = c.get("id", c.get("label", ""))
        group_nodes = groups.get(cid, [])
        if not group_nodes:
            container_map[cid] = {"width": 160, "height": 80, "nodes": [], "container": c}
            continue

        # Get edges internal to this container
        node_ids = {n["id"] for n in group_nodes}
        internal_edges = [
            e for e in edges
            if e.get("from", e.get("source", "")) in node_ids
            and e.get("to", e.get("target", "")) in node_ids
        ]

        if internal_edges:
            sub_result = _layout_flat(group_nodes, internal_edges)
        else:
            # No internal edges: simple horizontal arrangement with generous spacing
            positioned = []
            cur_x = MARGIN
            max_h = 0
            for n in group_nodes:
                label = n.get("label", n.get("id", ""))
                shape = n.get("shape", n.get("kind", "rect"))
                w = n.get("width") or _auto_node_width(label, shape)
                lines = label.split("\n") if label else [""]
                auto_h = max(DEFAULT_NODE_H, len(lines) * LINE_H + PAD_Y)
                h = n.get("height") or (((auto_h + 7) // 8) * 8)
                positioned.append({**n, "x": cur_x, "y": MARGIN, "width": w, "height": h})
                cur_x += w + H_SPACE + 60  # generous spacing inside containers
                max_h = max(max_h, h)
            total_w = cur_x - H_SPACE - 60 + MARGIN if positioned else 200
            sub_result = {
                "nodes": positioned,
                "edges": [],
                "width": total_w,
                "height": max_h + MARGIN * 2,
            }

        container_map[cid] = {
            "width": sub_result["width"] + CONTAINER_PAD * 2,
            "height": sub_result["height"] + CONTAINER_PAD * 2 + CONTAINER_HEADER,
            "nodes": sub_result["nodes"],
            "container": c,
        }

    # Step 2: create super-nodes for each container + keep top-level nodes
    # Build node-to-container mapping
    node_to_container: dict[str, str] = {}
    for cid, cdata in container_map.items():
        for n in cdata["nodes"]:
            node_to_container[n["id"]] = cid

    super_nodes = list(groups.get(None, []))
    for cid, cdata in container_map.items():
        super_nodes.append({
            "id": f"__container__{cid}",
            "label": cdata["container"].get("label", cid),
            "width": cdata["width"],
            "height": cdata["height"],
        })

    # Map cross-container edges to super-node edges
    # Edge from node_a (in container_X) to node_b (in container_Y)
    # → becomes edge from __container__X to __container__Y
    top_edges: list[dict] = []
    seen_top_edges: set[tuple[str, str]] = set()

    for e in edges:
        src = e.get("from", e.get("source", ""))
        tgt = e.get("to", e.get("target", ""))
        src_c = node_to_container.get(src)
        tgt_c = node_to_container.get(tgt)

        # Map to super-node IDs
        top_src = f"__container__{src_c}" if src_c else src
        top_tgt = f"__container__{tgt_c}" if tgt_c else tgt

        # Skip internal edges (same container) and self-loops
        if top_src == top_tgt:
            continue

        edge_key = (top_src, top_tgt)
        if edge_key not in seen_top_edges:
            seen_top_edges.add(edge_key)
            top_edges.append({"from": top_src, "to": top_tgt, "type": e.get("type", "primary")})

    # Step 3: layout top-level graph
    top_result = _layout_flat(super_nodes, top_edges)

    # Step 4: expand containers — offset internal nodes
    all_nodes = []
    positioned_containers = []

    for n in top_result["nodes"]:
        nid = n["id"]
        if nid.startswith("__container__"):
            cid = nid[len("__container__"):]
            cdata = container_map[cid]
            cx, cy = n["x"], n["y"]

            # Container bounds
            positioned_containers.append({
                **cdata["container"],
                "x": cx,
                "y": cy,
                "width": n["width"],
                "height": n["height"],
            })

            # Offset internal nodes
            for inner in cdata["nodes"]:
                inner["x"] += cx + CONTAINER_PAD
                inner["y"] += cy + CONTAINER_PAD + CONTAINER_HEADER
                all_nodes.append(inner)
        else:
            all_nodes.append(n)

    return {
        "nodes": all_nodes,
        "edges": top_result["edges"],
        "containers": positioned_containers,
        "width": top_result["width"],
        "height": top_result["height"],
    }


# ---------------------------------------------------------------------------
# Core flat layout (no containers)
# ---------------------------------------------------------------------------

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
        shape = n.get("shape", n.get("kind", "rect"))
        w = n.get("width") or _auto_node_width(label, shape)
        # Auto-height from multiline labels
        lines = label.split("\n") if label else [""]
        auto_h = max(DEFAULT_NODE_H, len(lines) * LINE_H + PAD_Y)
        auto_h = ((auto_h + 7) // 8) * 8  # snap to 8px grid
        h = n.get("height") or auto_h

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

    # Adaptive vertical spacing based on node count
    num_nodes = len(vertex_map)
    if num_nodes <= 8:
        adaptive_v = V_SPACE
    elif num_nodes <= 14:
        adaptive_v = max(88, V_SPACE - (num_nodes - 8) * 5)
    else:
        adaptive_v = max(72, 88 - (num_nodes - 14) * 3)

    # Layout each connected component — shift each horizontally to avoid overlap
    component_x_offset = 0
    for component in g.C:
        sug = SugiyamaLayout(component)
        sug.xspace = H_SPACE
        sug.yspace = adaptive_v
        sug.init_all()
        sug.draw()

        # Find this component's width and shift it
        comp_min_x = float("inf")
        comp_max_x = float("-inf")
        comp_vertices = [v for v in component.sV]
        for v in comp_vertices:
            if v.view.xy is None:
                continue
            cx = v.view.xy[0]
            w = v.view.w
            comp_min_x = min(comp_min_x, cx - w / 2)
            comp_max_x = max(comp_max_x, cx + w / 2)

        if comp_min_x == float("inf"):
            continue

        # Shift this component so it starts at component_x_offset
        shift = component_x_offset - comp_min_x
        for v in comp_vertices:
            if v.view.xy is not None:
                v.view.xy = (v.view.xy[0] + shift, v.view.xy[1])

        # Update offset for next component
        component_x_offset += (comp_max_x - comp_min_x) + H_SPACE + 40

    # Read positions back and normalize
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for v in vertex_map.values():
        if v.view.xy is None:
            continue
        cx, cy = v.view.xy
        w, h = v.view.w, v.view.h
        x = cx - w / 2
        y = cy - h / 2
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x + w)
        max_y = max(max_y, y + h)

    # Normalize: shift content so min is at MARGIN
    offset_x = MARGIN - min_x if min_x != float("inf") else 0
    offset_y = MARGIN - min_y if min_y != float("inf") else 0

    # Compute content bounds and canvas size
    content_w = (max_x - min_x) if max_x != float("-inf") else 0
    content_h = (max_y - min_y) if max_y != float("-inf") else 0
    canvas_w = max(960, _snap(content_w + 2 * MARGIN))
    canvas_h = max(400, _snap(content_h + 2 * MARGIN))

    # Center content horizontally on canvas
    center_offset_x = _snap((canvas_w - content_w) / 2) - MARGIN
    offset_x += center_offset_x

    # Position nodes
    positioned_nodes = []
    node_bounds_list = []

    for nid, v in vertex_map.items():
        if v.view.xy is None:
            continue
        cx, cy = v.view.xy
        w, h = v.view.w, v.view.h
        x = _snap(cx - w / 2 + offset_x)
        y = _snap(cy - h / 2 + offset_y)

        node_data = dict(v.data)
        node_data["x"] = x
        node_data["y"] = y
        node_data["width"] = w
        node_data["height"] = h
        positioned_nodes.append(node_data)
        node_bounds_list.append((x, y, w, h))

    # Route edges orthogonally
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

        # Source bottom center → target top center
        x1 = sx + offset_x
        y1 = sy + sh / 2 + offset_y
        x2 = dx + offset_x
        y2 = dy - dh / 2 + offset_y

        route = _route_orthogonal(x1, y1, x2, y2, node_bounds_list)

        edge_data = dict(eo.data) if eo.data else {}
        edge_data["_route"] = route
        positioned_edges.append(edge_data)

    return {
        "nodes": positioned_nodes,
        "edges": positioned_edges,
        "width": canvas_w,
        "height": canvas_h,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_layout(data: dict[str, Any]) -> dict[str, Any]:
    """
    Compute layout for a diagram JSON structure.

    Input: {"nodes": [...], "edges": [...], "title": "...", "containers": [...]}
    Output: same structure but nodes have x, y, width, height; edges have _route points

    Handles:
    - Flat graphs (nodes + edges)
    - Compound graphs (nodes + edges + containers)
    - Already-positioned nodes (pass through)
    """
    nodes = data.get("nodes", [])
    edges = data.get("edges", data.get("arrows", []))
    containers = data.get("containers", [])

    # Check if nodes already have absolute positions
    has_positions = all("x" in n and "y" in n for n in nodes) if nodes else False

    if has_positions:
        return data

    # Compute layout
    if containers:
        result = _layout_with_containers(nodes, edges, containers)
    else:
        result = _layout_flat(nodes, edges)

    # Rebuild output
    output = dict(data)
    output["nodes"] = result["nodes"]
    output["edges"] = result["edges"]
    if "containers" in result:
        output["containers"] = result["containers"]
    output["_canvas_width"] = result["width"]
    output["_canvas_height"] = result["height"]

    return output
