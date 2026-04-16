"""
icons.py — SVG icon registry for svg-gen.py

Three-tier icon loading:
  1. BUILTIN_ICONS (24 curated) — always available, zero overhead
  2. lucide/icon-nodes.json (1695 icons) — lazy-loaded if downloaded
  3. Fallback — no icon, just shape

Run `bash fetch-icons.sh` to download the full Lucide library.
Icons are Lucide-compatible (MIT license): viewBox 0 0 24 24, stroke-based.
"""

import json
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_LUCIDE_DIR = os.path.join(_SCRIPT_DIR, "lucide")
_LUCIDE_CACHE: dict[str, list[str]] | None = None  # lazy-loaded

# fmt: off

# All paths use viewBox 0 0 24 24. Rendered at 16x16 with transform scale.
BUILTIN_ICONS: dict[str, list[str]] = {

    "database": [
        '<ellipse cx="12" cy="5" rx="9" ry="3"/>',
        '<path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/>',
        '<path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/>',
    ],

    "server": [
        '<rect width="20" height="8" x="2" y="2" rx="2" ry="2"/>',
        '<rect width="20" height="8" x="2" y="14" rx="2" ry="2"/>',
        '<line x1="6" x2="6.01" y1="6" y2="6"/>',
        '<line x1="6" x2="6.01" y1="18" y2="18"/>',
    ],

    "cloud": [
        '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
    ],

    "code": [
        '<polyline points="16 18 22 12 16 6"/>',
        '<polyline points="8 6 2 12 8 18"/>',
    ],

    "terminal": [
        '<polyline points="4 17 10 11 4 5"/>',
        '<line x1="12" x2="20" y1="19" y2="19"/>',
    ],

    "user": [
        '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>',
        '<circle cx="12" cy="7" r="4"/>',
    ],

    "lock": [
        '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>',
        '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    ],

    "search": [
        '<circle cx="11" cy="11" r="8"/>',
        '<path d="m21 21-4.3-4.3"/>',
    ],

    "mail": [
        '<rect width="20" height="16" x="2" y="4" rx="2"/>',
        '<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    ],

    "globe": [
        '<circle cx="12" cy="12" r="10"/>',
        '<path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>',
        '<path d="M2 12h20"/>',
    ],

    "cpu": [
        '<rect width="16" height="16" x="4" y="4" rx="2"/>',
        '<rect width="6" height="6" x="9" y="9" rx="1"/>',
        '<path d="M15 2v2"/>',
        '<path d="M15 20v2"/>',
        '<path d="M2 15h2"/>',
        '<path d="M2 9h2"/>',
        '<path d="M20 15h2"/>',
        '<path d="M20 9h2"/>',
        '<path d="M9 2v2"/>',
        '<path d="M9 20v2"/>',
    ],

    "git-branch": [
        '<line x1="6" x2="6" y1="3" y2="15"/>',
        '<circle cx="18" cy="6" r="3"/>',
        '<circle cx="6" cy="18" r="3"/>',
        '<path d="M18 9a9 9 0 0 1-9 9"/>',
    ],

    "layers": [
        '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.84Z"/>',
        '<path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/>',
        '<path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
    ],

    "shield": [
        '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    ],

    "zap": [
        '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',
    ],

    "settings": [
        '<path d="M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"/>',
        '<circle cx="12" cy="12" r="3"/>',
    ],

    "file-text": [
        '<path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"/>',
        '<path d="M14 2v5a1 1 0 0 0 1 1h5"/>',
        '<path d="M10 9H8"/>',
        '<path d="M16 13H8"/>',
        '<path d="M16 17H8"/>',
    ],

    "message-circle": [
        '<path d="M2.992 16.342a2 2 0 0 1 .094 1.167l-1.065 3.29a1 1 0 0 0 1.236 1.168l3.413-.998a2 2 0 0 1 1.099.092 10 10 0 1 0-4.777-4.719"/>',
    ],

    "bot": [
        '<path d="M12 8V4H8"/>',
        '<rect width="16" height="12" x="4" y="8" rx="2"/>',
        '<path d="M2 14h2"/>',
        '<path d="M20 14h2"/>',
        '<path d="M15 13v2"/>',
        '<path d="M9 13v2"/>',
    ],

    "brain": [
        '<path d="M12 18V5"/>',
        '<path d="M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"/>',
        '<path d="M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"/>',
        '<path d="M17.997 5.125a4 4 0 0 1 2.526 5.77"/>',
        '<path d="M18 18a4 4 0 0 0 2-7.464"/>',
        '<path d="M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"/>',
        '<path d="M6 18a4 4 0 0 1-2-7.464"/>',
        '<path d="M6.003 5.125a4 4 0 0 0-2.526 5.77"/>',
    ],

    "network": [
        '<rect x="16" y="16" width="6" height="6" rx="1"/>',
        '<rect x="2" y="16" width="6" height="6" rx="1"/>',
        '<rect x="9" y="2" width="6" height="6" rx="1"/>',
        '<path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3"/>',
        '<path d="M12 12V8"/>',
    ],

    "key": [
        '<path d="m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"/>',
        '<path d="m21 2-9.6 9.6"/>',
        '<circle cx="7.5" cy="15.5" r="5.5"/>',
    ],

    "refresh-cw": [
        '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>',
        '<path d="M21 3v5h-5"/>',
        '<path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>',
        '<path d="M8 16H3v5"/>',
    ],

    "hard-drive": [
        '<path d="M10 16h.01"/>',
        '<path d="M2.212 11.577a2 2 0 0 0-.212.896V18a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5.527a2 2 0 0 0-.212-.896L18.55 5.11A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
        '<path d="M21.946 12.013H2.054"/>',
        '<path d="M6 16h.01"/>',
    ],

    "webhook": [
        '<path d="M18 16.98h-5.99c-1.1 0-1.95.94-2.48 1.9A4 4 0 0 1 2 17c.01-.7.2-1.4.57-2"/>',
        '<path d="m6 17 3.13-5.78c.53-.97.1-2.18-.5-3.1a4 4 0 1 1 6.89-4.06"/>',
        '<path d="m12 6 3.13 5.73C15.66 12.7 16.9 13 18 13a4 4 0 0 1 0 8"/>',
    ],
}

# fmt: on


# ---------------------------------------------------------------------------
# Lucide icon-nodes.json lazy loader (1695 icons)
# ---------------------------------------------------------------------------

def _load_lucide_icons() -> dict[str, list[str]]:
    """Load full Lucide icon set from icon-nodes.json if available.

    Converts Lucide's [[element, {attrs}], ...] format to SVG element strings.
    Returns empty dict if file not found (not downloaded yet).
    """
    global _LUCIDE_CACHE
    if _LUCIDE_CACHE is not None:
        return _LUCIDE_CACHE

    nodes_path = os.path.join(_LUCIDE_DIR, "icon-nodes.json")
    if not os.path.exists(nodes_path):
        _LUCIDE_CACHE = {}
        return _LUCIDE_CACHE

    try:
        with open(nodes_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        _LUCIDE_CACHE = {}
        return _LUCIDE_CACHE

    result: dict[str, list[str]] = {}
    for name, elements in raw.items():
        svg_parts: list[str] = []
        for elem in elements:
            if not isinstance(elem, list) or len(elem) < 2:
                continue
            tag = elem[0]
            attrs = elem[1] if isinstance(elem[1], dict) else {}
            attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
            svg_parts.append(f"<{tag} {attr_str}/>")
        if svg_parts:
            result[name] = svg_parts

    _LUCIDE_CACHE = result
    return _LUCIDE_CACHE


def get_icon(name: str) -> list[str] | None:
    """Get icon SVG elements by name. Checks built-in first, then Lucide cache."""
    if name in BUILTIN_ICONS:
        return BUILTIN_ICONS[name]
    lucide = _load_lucide_icons()
    return lucide.get(name)


# Unified accessor — used by svg-gen.py
class _IconRegistry:
    """Dict-like accessor that merges built-in + Lucide icons."""
    def __contains__(self, name: str) -> bool:
        return name in BUILTIN_ICONS or name in _load_lucide_icons()

    def __getitem__(self, name: str) -> list[str]:
        result = get_icon(name)
        if result is None:
            raise KeyError(name)
        return result

    def get(self, name: str, default=None):
        return get_icon(name) or default


ICONS = _IconRegistry()


# ---------------------------------------------------------------------------
# Auto-detect icon from shape type or label keywords
# ---------------------------------------------------------------------------

# Shape → default icon (only for shapes without built-in visual identity)
SHAPE_ICON_MAP: dict[str, str | None] = {
    "cylinder": "database",
    "database": "database",
    "hexagon": "globe",
    "agent": "bot",
    "llm": "zap",
    "memory": "refresh-cw",
    # Shapes with built-in identity → no icon needed
    "terminal": None,
    "document": None,
    "user_avatar": None,
    "user": None,
    "person": None,
    "diamond": None,
    "decision": None,
    "rect": None,
    "rounded-rect": None,
}

# Label keywords → icon (higher priority than shape)
KEYWORD_ICON_MAP: dict[str, str] = {
    "api": "globe",
    "gateway": "shield",
    "auth": "lock",
    "login": "lock",
    "password": "lock",
    "security": "shield",
    "search": "search",
    "email": "mail",
    "mail": "mail",
    "notification": "mail",
    "redis": "hard-drive",
    "cache": "refresh-cw",
    "config": "settings",
    "setting": "settings",
    "deploy": "cloud",
    "cloud": "cloud",
    "aws": "cloud",
    "docker": "layers",
    "kubernetes": "network",
    "k8s": "network",
    "git": "git-branch",
    "branch": "git-branch",
    "code": "code",
    "script": "terminal",
    "server": "server",
    "cpu": "cpu",
    "queue": "layers",
    "kafka": "layers",
    "webhook": "webhook",
    "key": "key",
    "token": "key",
    "jwt": "key",
    "file": "file-text",
    "report": "file-text",
    "pdf": "file-text",
    "log": "file-text",
    "message": "message-circle",
    "chat": "message-circle",
    "bot": "bot",
    "agent": "bot",
    "orchestrat": "bot",
    "llm": "zap",
    "gpt": "zap",
    "claude": "zap",
    "gemini": "zap",
    "model": "brain",
    "ai": "brain",
    "neural": "brain",
    "network": "network",
    "load balancer": "network",
}


def detect_icon(node: dict) -> str | None:
    """Auto-detect the best icon for a node based on its shape and label.

    Returns icon name (key in ICONS dict) or None if no icon should be shown.
    An explicit "icon" field in the node always takes priority.
    """
    # Explicit icon field overrides everything
    explicit = node.get("icon")
    if explicit is not None:
        if explicit == "none" or explicit == "":
            return None
        return explicit if explicit in ICONS else explicit  # try anyway, Lucide may have it

    label_lower = (node.get("label", "") + " " + node.get("sublabel", "")).lower()
    shape = node.get("shape", node.get("kind", "rect"))

    # 1) Check label keywords first (higher priority)
    for keyword, icon_name in KEYWORD_ICON_MAP.items():
        if keyword in label_lower:
            return icon_name

    # 2) Fall back to shape-based default
    return SHAPE_ICON_MAP.get(shape)
