#!/usr/bin/env python3
"""Generate premium mythic lesson art fallbacks and image-gen prompts.

This does not call an external image service. It creates deterministic SVG art for
all public knowledge-graph nodes and a manifest that can be fed to Codex/image
generation later. Real generated images can replace or sit beside these files.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

APP_ROOT = Path(__file__).resolve().parents[1]
VAULT = Path(os.environ.get("LIFEOS_VAULT", APP_ROOT / "public")).resolve()
LEARN_OUT = VAULT / "output" / "learn"
GRAPH_PATH = LEARN_OUT / "knowledge-graph.json"
ART_DIR = LEARN_OUT / "art" / "mythic"
MANIFEST_PATH = LEARN_OUT / "art" / "mythic-art-manifest.json"

PALETTES: dict[str, tuple[str, str, str, str, str]] = {
    "thinking": ("#15223f", "#6f8cff", "#ffe6a7", "#8bd3ff", "#f7efe0"),
    "math": ("#241842", "#9a7cff", "#fff0a8", "#72e5ff", "#f8f4ff"),
    "physics": ("#0c1d3d", "#2e7cff", "#d8f3ff", "#7ee3ff", "#f8fbff"),
    "history": ("#4a2218", "#c66b49", "#ffe1a6", "#d79b5d", "#fff2d2"),
    "statecraft": ("#2b2538", "#7e5a9b", "#f5d38a", "#d65d4a", "#f7efe0"),
    "culture": ("#3a1742", "#c86bc9", "#ffe3a1", "#ff8f70", "#fff0f4"),
    "systems": ("#113b31", "#1f9d78", "#ffe07a", "#7be0b8", "#fff4d7"),
    "growth": ("#17351f", "#4fae67", "#f7d36b", "#9be28d", "#fff8dc"),
    "startup": ("#17351f", "#42a77b", "#ffe07a", "#ff6b5f", "#fff4d7"),
    "general": ("#1d2a3b", "#5aa6ff", "#ffe3a1", "#f1c6a8", "#fff8ec"),
}

DOMAIN_NOUNS = {
    "thinking": "a luminous library-citadel of thought",
    "math": "a sacred geometric observatory",
    "physics": "a moonlit quantum temple under constellations",
    "history": "an ancient parchment city at golden dusk",
    "statecraft": "a strategy table inside a bronze war-room",
    "culture": "a mythic gallery of masks, music, and color",
    "systems": "a living clockwork forest of feedback loops",
    "growth": "a dawn garden where habits become towering trees",
    "startup": "a tiny workshop launching a brave impossible machine",
}


def slug_file(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-") or "lesson"


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def wrap_title(title: str, limit: int = 24) -> list[str]:
    words = title.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if sum(len(w) for w in current) + len(current) + len(word) > limit and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
        if len(lines) >= 2:
            break
    if current and len(lines) < 3:
        lines.append(" ".join(current))
    return lines[:3] or [title[:limit]]


def h32(text: str) -> int:
    h = 2166136261
    for ch in text:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def prompt_for(node: dict[str, Any]) -> str:
    title = str(node.get("title") or node.get("id") or "LifeOS lesson")
    domain = str(node.get("domain") or "general")
    summary = str(node.get("summary") or "source-first learning quest")
    scene = DOMAIN_NOUNS.get(domain, DOMAIN_NOUNS.get("general", "a mythic learning world"))
    return (
        "Premium storybook illustration for a LifeOS learning RPG card. "
        f"Lesson: {title}. Domain: {domain}. Concept: {summary}. "
        f"Scene: {scene}. Style: warm Fable / mythic parchment / Claude-like elegant editorial fantasy, "
        "hand-painted, cinematic soft light, no text, no logos, no UI, centered symbolic subject, "
        "rich but uncluttered, cozy magical realism, high detail, suitable for a 4:3 learning card hero image."
    )


def svg_for(node: dict[str, Any]) -> str:
    node_id = str(node.get("id") or "lesson")
    title = str(node.get("title") or node_id.replace("-", " "))
    domain = str(node.get("domain") or "general")
    summary = str(node.get("summary") or "")
    base, mid, sun, accent, paper = PALETTES.get(domain, PALETTES["general"])
    seed = h32(node_id)
    moon_x = 620 + seed % 130
    moon_y = 76 + (seed >> 8) % 54
    tower_x = 130 + (seed >> 16) % 140
    tower_h = 150 + (seed >> 20) % 90
    stars = []
    for i in range(34):
        x = 24 + ((seed + i * 97) % 752)
        y = 18 + (((seed >> 3) + i * 53) % 245)
        r = 0.8 + (((seed >> 5) + i * 11) % 17) / 10
        stars.append(f"<circle cx='{x}' cy='{y}' r='{r:.1f}' fill='rgba(255,255,255,.55)'/>")
    return f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 520' role='img' aria-label='{esc(title)} mythic lesson art'>
  <title>{esc(title)} mythic lesson art</title>
  <defs>
    <linearGradient id='sky' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0' stop-color='{base}'/>
      <stop offset='.58' stop-color='{mid}'/>
      <stop offset='1' stop-color='{paper}'/>
    </linearGradient>
    <radialGradient id='sun' cx='.78' cy='.20' r='.22'>
      <stop offset='0' stop-color='{sun}' stop-opacity='1'/>
      <stop offset='.48' stop-color='{sun}' stop-opacity='.55'/>
      <stop offset='1' stop-color='{sun}' stop-opacity='0'/>
    </radialGradient>
    <filter id='soft'><feGaussianBlur stdDeviation='14'/></filter>
    <style>
      .grain{{mix-blend-mode:soft-light;opacity:.28}}
    </style>
  </defs>
  <rect width='800' height='520' fill='url(#sky)'/>
  <rect width='800' height='520' fill='url(#sun)'/>
  <g opacity='.92'>{''.join(stars)}</g>
  <path d='M-40 354 C120 270 226 312 362 252 C498 190 620 254 850 184 L850 550 L-40 550 Z' fill='rgba(255,248,236,.22)'/>
  <path d='M-30 390 C112 328 238 370 374 318 C530 258 628 322 842 276 L842 550 L-30 550 Z' fill='rgba(22,17,12,.28)'/>
  <circle cx='{moon_x}' cy='{moon_y}' r='74' fill='{sun}' opacity='.82'/>
  <circle cx='{moon_x - 18}' cy='{moon_y - 12}' r='92' fill='{sun}' opacity='.20' filter='url(#soft)'/>
  <g transform='translate({tower_x} {306 - tower_h / 2})'>
    <path d='M60 {tower_h} L60 76 Q60 42 96 42 L152 42 Q188 42 188 76 L188 {tower_h} Z' fill='{paper}' opacity='.92'/>
    <path d='M76 42 L94 4 L112 42 M136 42 L154 4 L172 42' fill='{accent}' opacity='.95'/>
    <rect x='108' y='{tower_h - 62}' width='34' height='62' rx='17' fill='rgba(40,24,16,.42)'/>
    <circle cx='124' cy='94' r='15' fill='rgba(40,24,16,.22)'/>
    <path d='M34 {tower_h} C84 {tower_h - 28} 166 {tower_h - 22} 222 {tower_h} Z' fill='rgba(255,255,255,.26)'/>
  </g>
  <g transform='translate(514 258)' opacity='.96'>
    <circle cx='76' cy='76' r='70' fill='none' stroke='{accent}' stroke-width='9' opacity='.72'/>
    <circle cx='76' cy='76' r='14' fill='{paper}'/>
    <path d='M76 4 L92 76 L76 148 L60 76 Z' fill='{sun}' opacity='.9'/>
    <path d='M76 42 L91 91 L76 78 L61 91 Z' fill='{base}' opacity='.88'/>
    <circle cx='76' cy='76' r='5' fill='{accent}'/>
  </g>
  <path d='M52 456 C152 402 260 438 356 386 C474 322 584 356 742 316 L742 520 L52 520 Z' fill='rgba(255,248,236,.16)'/>
  <path d='M0 0 H800 V520 H0 Z' fill='none' stroke='rgba(255,248,236,.36)' stroke-width='18'/>
  <path class='grain' d='M-20 60 C120 42 206 112 350 74 C502 34 620 96 830 44 M-16 164 C142 138 230 214 374 168 C530 118 650 190 828 130 M-10 266 C110 238 248 300 388 258 C548 210 658 288 832 224' fill='none' stroke='rgba(255,255,255,.42)' stroke-width='2'/>
</svg>"""


def build() -> int:
    if not GRAPH_PATH.exists():
        raise SystemExit(f"missing graph: {GRAPH_PATH}")
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    nodes = [n for n in graph.get("nodes", []) if isinstance(n, dict)]
    ART_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for node in nodes:
        node_id = str(node.get("id") or "").strip()
        if not node_id:
            continue
        filename = slug_file(node_id) + ".svg"
        svg_path = ART_DIR / filename
        svg_path.write_text(svg_for(node), encoding="utf-8")
        records.append({
            "id": node_id,
            "title": node.get("title"),
            "domain": node.get("domain"),
            "kind": node.get("kind"),
            "source_url": node.get("url"),
            "fallback_svg": f"/learn/art/mythic/{filename}",
            "generated_target": f"/learn/art/generated/{slug_file(node_id)}.webp",
            "prompt": prompt_for(node),
        })
    manifest = {
        "version": 1,
        "count": len(records),
        "style": "premium Fable / mythic parchment / storybook learning-card hero",
        "note": "Fallback SVGs are deterministic. Feed prompts to an image generator and write optimized webp files to generated_target when available.",
        "records": records,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": True, "count": len(records), "dir": str(ART_DIR), "manifest": str(MANIFEST_PATH)}, indent=2), flush=True)
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "build"
    if cmd != "build":
        print("usage: lifeos_mythic_art.py build", file=sys.stderr)
        return 2
    return build()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
