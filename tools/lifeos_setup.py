#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import subprocess
from pathlib import Path
from typing import Any

from lifeos_audit import log_event

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
OUT = ROOT / "output"
CONNECTORS = OUT / "lifeos-connectors.json"
SETUP_MD = OUT / "lifeos-setup.md"
SETUP_HTML = OUT / "lifeos-setup.html"


def run(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=APP_ROOT, text=True, capture_output=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback
    except Exception:
        return fallback


def checkbox(done: bool) -> str:
    return "[x]" if done else "[ ]"


def build_steps() -> list[dict[str, Any]]:
    conn = read_json(CONNECTORS, {})
    code, out, err = run(["python", "tools/check_lifeos_agents.py"])
    agents = json.loads(out) if code in (0, 1) and out.startswith("{") else {}
    return [
        {
            "id": "gmail",
            "title": "Connect Gmail",
            "done": bool((conn.get("gmail") or {}).get("configured")),
            "command": "gmcli accounts credentials C:\\Users\\adars\\secrets\\google-oauth-client.json && gmcli accounts add adarshamishra33@gmail.com",
            "why": "Populates Priority Inbox, Needs Reply, LinkedIn Signals, Receipts/Security.",
        },
        {
            "id": "calendar",
            "title": "Connect Google Calendar",
            "done": bool((conn.get("calendar") or {}).get("configured")),
            "command": "gccli accounts credentials C:\\Users\\adars\\secrets\\google-oauth-client.json && gccli accounts add adarshamishra33@gmail.com",
            "why": "Populates today/tomorrow events and enables future AI Plan calendar staging.",
        },
        {
            "id": "personal-suite",
            "title": "Run mcp-personal-suite setup",
            "done": bool((agents.get("codex_config") or {}).get("configured")),
            "command": "npx mcp-personal-suite setup",
            "why": "Gives Codex a local-first connector suite for email/calendar/messaging/search.",
        },
        {
            "id": "cursor",
            "title": "Log into Cursor Agent",
            "done": bool((agents.get("cursor") or {}).get("logged_in")),
            "command": "agent login && agent status",
            "why": "Enables worker delegation through tools/cursor_worker.py.",
        },
        {
            "id": "gemini",
            "title": "Configure Gemini worker",
            "done": bool((agents.get("gemini") or {}).get("configured")),
            "command": "set GEMINI_API_KEY=...  # or configure C:\\Users\\adars\\.gemini\\settings.json",
            "why": "Enables persistent Gemini worker tasks.",
        },
        {
            "id": "archive",
            "title": "Sync local archive",
            "done": bool((conn.get("archive") or {}).get("count", 0)),
            "command": "python tools/lifeos_archive.py sync",
            "why": "Caches local records for offline dashboard/search.",
        },
    ]


def render_md(steps: list[dict[str, Any]]) -> str:
    lines = ["# LifeOS Setup", "", "Run the first unchecked command. Outbound actions remain staged for approval.", ""]
    for step in steps:
        lines += [f"- {checkbox(step['done'])} **{step['title']}**", f"  - Why: {step['why']}", f"  - Command: `{step['command']}`"]
    lines.append("")
    return "\n".join(lines)


def render_html(md: str) -> str:
    rows = []
    for line in md.splitlines():
        if line.startswith("# "):
            rows.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("- ["):
            rows.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.strip().startswith("- "):
            rows.append(f"<p class='sub'>{html.escape(line.strip()[2:])}</p>")
        elif line.strip():
            rows.append(f"<p>{html.escape(line)}</p>")
    css = "body{background:#020403;color:#d7ffe8;font-family:Consolas,monospace;max-width:900px;margin:40px auto;padding:0 20px}h1{color:#39ff88;text-transform:uppercase}li{margin:18px 0 6px}.sub{color:#78a88d;margin:4px 0 4px 24px}code{color:#39ff88}"
    return f"<!doctype html><meta charset='utf-8'><title>LifeOS Setup</title><style>{css}</style>{''.join(rows)}"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    steps = build_steps()
    md = render_md(steps)
    SETUP_MD.write_text(md, encoding="utf-8")
    SETUP_HTML.write_text(render_html(md), encoding="utf-8")
    log_event("setup_rendered", "lifeos_setup", remaining=sum(1 for s in steps if not s["done"]))
    print(SETUP_HTML)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
