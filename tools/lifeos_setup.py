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
    google_oauth = conn.get("google_oauth") or {}
    gmail = conn.get("gmail") or {}
    calendar = conn.get("calendar") or {}
    github = conn.get("github") or {}
    cursor = conn.get("cursor") or {}
    gemini = conn.get("gemini") or {}
    personal_suite = conn.get("personal_suite") or {}
    oauth_path = google_oauth.get("path") or r"C:\Users\adars\secrets\google-oauth-client.json"
    email = gmail.get("email") or calendar.get("email") or "adarshamishra33@gmail.com"
    return [
        {
            "id": "google-oauth",
            "title": "Create Google OAuth desktop client JSON",
            "done": bool(google_oauth.get("configured")),
            "command": rf"Save a Desktop OAuth client with Gmail API + Google Calendar API enabled to {oauth_path}",
            "why": google_oauth.get("status") or "Required before Gmail/Calendar account login can work.",
        },
        {
            "id": "gmail",
            "title": "Connect Gmail",
            "done": bool(gmail.get("configured")),
            "command": rf"gmcli accounts credentials {oauth_path} && gmcli accounts add {email}",
            "why": gmail.get("error") or "Populates Priority Inbox, Needs Reply, LinkedIn Signals, Receipts/Security.",
        },
        {
            "id": "calendar",
            "title": "Connect Google Calendar",
            "done": bool(calendar.get("configured")),
            "command": rf"gccli accounts credentials {oauth_path} && gccli accounts add {email}",
            "why": calendar.get("error") or "Populates today/tomorrow events and enables future AI Plan calendar staging.",
        },
        {
            "id": "github",
            "title": "GitHub CLI auth",
            "done": bool(github.get("configured")),
            "command": "gh auth login && gh auth status",
            "why": github.get("status") or github.get("error") or "Pulls assigned issues, review requests, and failed workflows.",
        },
        {
            "id": "personal-suite",
            "title": "Run mcp-personal-suite setup",
            "done": bool(personal_suite.get("configured")),
            "command": "npx mcp-personal-suite setup",
            "why": personal_suite.get("status") or "Gives Codex a local-first connector suite for email/calendar/messaging/search.",
        },
        {
            "id": "cursor",
            "title": "Log into Cursor Agent",
            "done": bool(cursor.get("configured")),
            "command": "agent login && agent status",
            "why": cursor.get("status") or cursor.get("error") or "Enables worker delegation.",
        },
        {
            "id": "gemini",
            "title": "Configure Gemini worker",
            "done": bool(gemini.get("configured")),
            "command": "set GEMINI_API_KEY=...  # or install/login Gemini CLI",
            "why": gemini.get("status") or gemini.get("error") or "Enables persistent Gemini worker tasks.",
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
