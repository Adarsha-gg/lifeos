#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from lifeos_audit import log_event
from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
OUT = ROOT / "output"
REPORTS = OUT / "reports"

PIPELINE = [
    [sys.executable, "tools/lifeos_web_digest.py", "refresh"],
    [sys.executable, "tools/lifeos_events.py", "refresh"],
    [sys.executable, "tools/lifeos_connectors.py"],
    [sys.executable, "tools/lifeos_archive.py", "sync"],
    [sys.executable, "tools/lifeos_connectors.py"],
    [sys.executable, "tools/daily_brief.py"],
    [sys.executable, "tools/lifeos_games.py", "build"],
    [sys.executable, "tools/lifeos_arcade.py", "build"],
    [sys.executable, "tools/lifeos_generate.py", "missions"],
    [sys.executable, "tools/lifeos_lessons.py", "build"],
    [sys.executable, "tools/lifeos_setup.py"],
    [sys.executable, "tools/lifeos_dashboard.py"],
    [sys.executable, "tools/lifeos_morning_ping.py"],
]


def run_step(cmd: list[str], timeout: int = 90) -> dict[str, Any]:
    started = datetime.now().isoformat(timespec="seconds")
    try:
        proc = subprocess.run(cmd, cwd=APP_ROOT, text=True, capture_output=True, timeout=timeout)
        return {
            "cmd": cmd,
            "started_at": started,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip()[-4000:],
            "stderr": proc.stderr.strip()[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "started_at": started,
            "returncode": 124,
            "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr": "timeout",
        }


def latest_brief() -> str:
    paths = sorted(REPORTS.glob("daily-brief-*.md"))
    return str(paths[-1].relative_to(ROOT)) if paths else ""


def ensure_action_queue() -> str:
    path = OUT / "lifeos-actions.json"
    if not path.exists():
        path.write_text(json.dumps({"actions": []}, indent=2, sort_keys=True), encoding="utf-8")
    return str(path.relative_to(ROOT))


def run_pipeline() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    approval_queue = ensure_action_queue()
    steps = [
        run_step(cmd, timeout=600 if "lifeos_generate.py" in cmd else 90)
        for cmd in PIPELINE
    ]
    ok = all(step["returncode"] == 0 for step in steps)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "ok": ok,
        "steps": steps,
        "dashboard": "output/lifeos-dashboard.html",
        "daily_brief": latest_brief(),
        "web_digest": f"output/reports/lifeos-web-digest-{datetime.now().date().isoformat()}.md",
        "connectors": "output/lifeos-connectors.json",
        "approval_queue": approval_queue,
        "safety": "Pipeline is read-first. Send/post/delete/payment actions stay staged for explicit approval.",
    }
    status_path = OUT / "lifeos-morning-status.json"
    status_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    log_event("morning_pipeline_ran", "lifeos_morning", ok=ok, failed_steps=[s["cmd"] for s in steps if s["returncode"] != 0])
    return payload


def task_scheduler_command(time_value: str) -> str:
    python = sys.executable
    script = APP_ROOT / "tools" / "lifeos_morning.py"
    return (
        'schtasks /Create /TN "LifeOS Morning Brief" /SC DAILY '
        f'/ST {time_value} /TR "\\"{python}\\" \\"{script}\\" run" /F'
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full LifeOS morning automation pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="Refresh web digest, daily brief, connectors, archive, setup, and dashboard")
    p = sub.add_parser("schedule-command", help="Print the Windows Task Scheduler command; does not install it")
    p.add_argument("--time", default="10:30", help="HH:MM local time, default 10:30")
    args = parser.parse_args()

    if args.cmd == "run":
        payload = run_pipeline()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1
    if args.cmd == "schedule-command":
        print(task_scheduler_command(args.time))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
