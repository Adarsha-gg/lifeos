#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import socket
import subprocess
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from typing import Any

from lifeos_actions import load as load_actions
from lifeos_actions import update_status
from lifeos_audit import log_event
from lifeos_todos import add as add_structured_todo
from lifeos_todos import complete as complete_structured_todo

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
JOURNAL = ROOT / "wiki" / "personal" / "done-journal.md"
RESEARCH_INBOX = ROOT / "raw" / "research" / "inbox.md"
OUT = ROOT / "output"
DASHBOARD = OUT / "lifeos-dashboard.html"
REFRESH_STATUS = OUT / "lifeos-refresh.json"
HOST = os.environ.get("LIFEOS_HOST", "127.0.0.1")
PORT = 8787


def run(cmd: list[str], timeout: int = 90) -> dict[str, Any]:
    started = datetime.now().isoformat(timespec="seconds")
    try:
        proc = subprocess.run(cmd, cwd=APP_ROOT, check=False, text=True, capture_output=True, timeout=timeout)
        return {
            "cmd": cmd,
            "started_at": started,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip()[-3000:],
            "stderr": proc.stderr.strip()[-3000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "started_at": started,
            "returncode": 124,
            "stdout": (exc.stdout or "")[-3000:] if isinstance(exc.stdout, str) else "",
            "stderr": "timeout",
        }


def local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def refresh() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    steps = [
        run([sys.executable, "tools/lifeos_web_digest.py", "refresh"]),
        run([sys.executable, "tools/lifeos_events.py", "refresh"]),
        run([sys.executable, "tools/lifeos_connectors.py"]),
        run([sys.executable, "tools/lifeos_archive.py", "sync"]),
        run([sys.executable, "tools/lifeos_connectors.py"]),
        run([sys.executable, "tools/daily_brief.py"]),
        run([sys.executable, "tools/lifeos_setup.py"]),
        run([sys.executable, "tools/lifeos_dashboard.py"]),
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "ok": all(step["returncode"] == 0 for step in steps),
        "steps": steps,
    }
    REFRESH_STATUS.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    log_event("server_refresh", "lifeos_server", ok=payload["ok"], failed_steps=[s["cmd"] for s in steps if s["returncode"] != 0])
    return payload


def ensure_journal() -> None:
    if JOURNAL.exists():
        return
    JOURNAL.write_text(
        "---\ntitle: Done Journal\ncategory: personal\ntags: [journal, done, lifeos]\n---\n\n# Done Journal\n\n",
        encoding="utf-8",
    )


def append_journal(text: str, source: str = "dashboard") -> None:
    ensure_journal()
    now = datetime.now().isoformat(timespec="seconds")
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(f"- {now} — {text} _(via {source})_\n")


def complete_todo(item_id: str) -> bool:
    item = complete_structured_todo(item_id)
    if not item:
        return False
    text = str(item.get("text") or "")
    append_journal(text)
    log_event("todo_completed", "lifeos_server", todo_id=item_id, text=text)
    return True


def add_todo(text: str, section: str = "Today") -> bool:
    item = add_structured_todo(text, section)
    if not item:
        return False
    log_event("todo_added", "lifeos_server", todo_id=item.get("id"), section=section, text=item.get("text"))
    return True


def stage_crm(index: int, channel: str) -> None:
    subprocess.run([sys.executable, "tools/lifeos_crm.py", "stage", str(index), "--channel", channel], cwd=APP_ROOT, check=False)
    log_event("crm_outreach_staged", "lifeos_server", index=index, channel=channel)


def capture_research(text: str, kind: str = "source") -> bool:
    text = " ".join(text.strip().split())
    if not text:
        return False
    RESEARCH_INBOX.parent.mkdir(parents=True, exist_ok=True)
    if not RESEARCH_INBOX.exists():
        RESEARCH_INBOX.write_text("---\ntitle: Research Inbox\ncategory: raw\ntags: [research, inbox, lifeos]\n---\n\n# Research Inbox\n\n", encoding="utf-8")
    now = datetime.now().isoformat(timespec="seconds")
    with RESEARCH_INBOX.open("a", encoding="utf-8") as f:
        f.write(f"- {now} [{kind}] {text}\n")
    log_event("research_captured", "lifeos_server", kind=kind, text=text[:200])
    return True


class Handler(BaseHTTPRequestHandler):
    MUTATION_PATHS = {
        "/todo/complete",
        "/todo/add",
        "/crm/stage",
        "/actions/approve",
        "/actions/reject",
        "/research/capture",
        "/research/capture-api",
    }

    def is_loopback_client(self) -> bool:
        host = self.client_address[0] if self.client_address else ""
        return host in {"127.0.0.1", "::1", "localhost"} or host.startswith("127.")

    def mutation_allowed(self, data: dict[str, list[str]]) -> bool:
        if HOST in {"127.0.0.1", "localhost", "::1"} or self.is_loopback_client():
            return True
        token = os.environ.get("LIFEOS_WRITE_TOKEN", "")
        if not token:
            return False
        supplied = data.get("token", [""])[0] or self.headers.get("X-LifeOS-Write-Token", "")
        return supplied == token

    def reject_mutation(self) -> None:
        body = b"Mutation blocked. LAN writes require LIFEOS_WRITE_TOKEN."
        self.send_response(403)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)

    def send_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-LifeOS-Write-Token")

    def redirect_home(self) -> None:
        self.send_response(303)
        self.send_header("Location", "/")
        self.send_cors()
        self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            checks = {
                "server": True,
                "vault": ROOT.exists(),
                "todos": (ROOT / "data" / "lifeos" / "todos.json").exists(),
                "dashboard": DASHBOARD.exists(),
                "research_inbox": RESEARCH_INBOX.exists(),
                "actions_queue": isinstance(load_actions().get("actions"), list),
                "refresh_status": REFRESH_STATUS.exists(),
            }
            body = (json.dumps({"ok": all(checks.values()), "checks": checks}, indent=2) + "\n").encode()
            self.send_response(200 if all(checks.values()) else 500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/phone":
            ip = local_ip()
            url = f"http://{ip}:{PORT}"
            body = f"""<!doctype html><meta charset='utf-8'><title>LifeOS Phone Access</title><body style='font-family:system-ui;background:#020403;color:#d7ffe8;padding:32px'><h1>LifeOS Phone Access</h1><p>Start the server in LAN mode, then open this URL on your phone while on the same Wi-Fi:</p><p style='font-size:24px'><a style='color:#39ff88' href='{url}'>{url}</a></p><p>If it does not load, Windows Firewall is blocking Python or the server was started local-only.</p><p><a style='color:#00f5ff' href='/'>Dashboard</a></p></body>""".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path in ("/", "/dashboard"):
            refresh_result = refresh()
            if not refresh_result.get("ok") or not DASHBOARD.exists():
                body = (json.dumps(refresh_result, indent=2) + "\n").encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            body = DASHBOARD.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/reports":
            reports = sorted((ROOT / "output" / "reports").glob("*.md"), reverse=True)
            rows = "".join(f"<li><a href='/output/reports/{html.escape(path.name)}'>{html.escape(path.name)}</a></li>" for path in reports)
            body = f"<!doctype html><meta charset='utf-8'><title>LifeOS Reports</title><body><h1>LifeOS Reports</h1><ul>{rows}</ul><p><a href='/'>Dashboard</a></p></body>".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path.startswith("/output/") or parsed.path.startswith("/wiki/") or parsed.path.startswith("/data/") or parsed.path.startswith("/raw/"):
            path = (ROOT / parsed.path.lstrip("/")).resolve()
            if ROOT in path.parents and path.exists() and path.is_file():
                body = path.read_bytes()
                ctype = "text/plain; charset=utf-8"
                if path.suffix == ".html":
                    ctype = "text/html; charset=utf-8"
                elif path.suffix == ".json":
                    ctype = "application/json; charset=utf-8"
                elif path.suffix == ".png":
                    ctype = "image/png"
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        body = f"Not found: {html.escape(parsed.path)}".encode()
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        data = parse_qs(self.rfile.read(length).decode("utf-8"))
        parsed = urlparse(self.path)
        if parsed.path in self.MUTATION_PATHS and not self.mutation_allowed(data):
            self.reject_mutation()
            return
        if parsed.path == "/todo/complete":
            complete_todo(data.get("id", [""])[0])
            self.redirect_home()
            return
        if parsed.path == "/todo/add":
            add_todo(data.get("text", [""])[0], data.get("section", ["Today"])[0])
            self.redirect_home()
            return
        if parsed.path == "/crm/stage":
            stage_crm(int(data.get("index", ["0"])[0]), data.get("channel", ["x"])[0])
            self.redirect_home()
            return
        if parsed.path == "/actions/approve":
            update_status(data.get("id", [""])[0], "approved", "dashboard")
            self.redirect_home()
            return
        if parsed.path == "/actions/reject":
            update_status(data.get("id", [""])[0], "rejected", "dashboard")
            self.redirect_home()
            return
        if parsed.path == "/research/capture":
            capture_research(data.get("text", [""])[0], data.get("kind", ["source"])[0])
            self.redirect_home()
            return
        if parsed.path == "/research/capture-api":
            ok = capture_research(data.get("text", [""])[0], data.get("kind", ["source"])[0])
            body = (b'{"ok":true}' if ok else b'{"ok":false}')
            self.send_response(200 if ok else 400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_cors()
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    refresh()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"http://{HOST}:{PORT}")
    if HOST in ("0.0.0.0", ""):
        print(f"phone: http://{local_ip()}:{PORT}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
