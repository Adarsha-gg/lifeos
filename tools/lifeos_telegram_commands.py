#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from lifeos_audit import log_event

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
OUT = ROOT / "output"


def run(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=APP_ROOT, text=True, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback
    except Exception:
        return fallback


def brief() -> str:
    code, out, err = run(["python", "tools/daily_brief.py"])
    if code != 0:
        return err or out
    path = Path(out.strip()) if out.strip() else None
    if path and path.exists():
        text = path.read_text(encoding="utf-8")
        return text[:3500]
    return out


def emails() -> str:
    conn = read_json(OUT / "lifeos-connectors.json", {})
    gmail = conn.get("gmail") or {}
    if not gmail.get("configured"):
        return gmail.get("error") or "Gmail not connected. Open LifeOS Setup."
    lines = ["Gmail Command Center"]
    for category, items in (gmail.get("categories") or {}).items():
        lines.append(f"\n{category}")
        if not items:
            lines.append("- Clear")
        for item in items[:5]:
            if isinstance(item, dict):
                lines.append(f"- {item.get('subject') or item.get('title') or item.get('summary') or item}")
            else:
                lines.append(f"- {item}")
    return "\n".join(lines)[:3500]


def meetings() -> str:
    conn = read_json(OUT / "lifeos-connectors.json", {})
    cal = conn.get("calendar") or {}
    if not cal.get("configured"):
        return cal.get("error") or "Calendar not connected. Open LifeOS Setup."
    items = cal.get("items") or []
    if not items:
        return "No upcoming meetings found."
    lines = ["Upcoming meetings"]
    for item in items[:10]:
        if isinstance(item, dict):
            lines.append(f"- {item.get('summary') or item.get('title') or item} — {item.get('start') or ''}")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)[:3500]


def approve(action_id: str) -> str:
    code, out, err = run(["python", "tools/lifeos_actions.py", "approve", action_id, "--decided-by", "telegram"])
    return out or err


def handle(command: str) -> str:
    parts = command.strip().split(maxsplit=1)
    name = parts[0].lower() if parts else ""
    arg = parts[1] if len(parts) > 1 else ""
    log_event("telegram_command", "lifeos_telegram", command=name)
    if name == "/briefing":
        return brief()
    if name == "/emails":
        return emails()
    if name == "/meetings":
        return meetings()
    if name == "/approve" and arg:
        return approve(arg.strip())
    return "Commands: /briefing, /emails, /meetings, /approve <id>"


def main() -> int:
    parser = argparse.ArgumentParser(description="LifeOS Telegram command handler")
    parser.add_argument("command", nargs="+", help="Command text, e.g. /briefing")
    args = parser.parse_args()
    print(handle(" ".join(args.command)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
