#!/usr/bin/env python3
from __future__ import annotations

import html
import hashlib
import hmac
import ipaddress
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
from lifeos_todos import open_items as open_todos

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
JOURNAL = ROOT / "wiki" / "personal" / "done-journal.md"
RESEARCH_INBOX = ROOT / "raw" / "research" / "inbox.md"
OUT = ROOT / "output"
DASHBOARD = OUT / "lifeos-dashboard.html"
REFRESH_STATUS = OUT / "lifeos-refresh.json"
LEARN_PROGRESS = OUT / "learn" / "progress.json"
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


def state_payload() -> dict[str, Any]:
    """Lightweight JSON snapshot for the phone control panel (no full refresh)."""
    actions = [a for a in load_actions().get("actions", []) if a.get("status") == "pending"]
    slim_actions = [
        {
            "id": a.get("id"),
            "title": a.get("title") or a.get("action") or "Action",
            "purpose": a.get("purpose") or "",
            "preview": a.get("preview") or "",
            "risk_level": a.get("risk_level") or "medium",
            "source": a.get("source") or "",
        }
        for a in actions
    ]
    return {
        "ok": True,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "todos": open_todos(),
        "actions": slim_actions,
    }


def load_learning_progress() -> dict[str, Any]:
    try:
        data = json.loads(LEARN_PROGRESS.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    data.setdefault("done", {})
    data.setdefault("reviews", {})
    return data


def save_learning_progress(data: dict[str, Any]) -> None:
    LEARN_PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now().isoformat(timespec="seconds")
    LEARN_PROGRESS.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def telegram_init_data(init_data: str) -> tuple[bool, dict[str, Any] | None, str]:
    token = os.environ.get("LIFEOS_TG_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or ""
    if not token:
        return False, None, "missing LIFEOS_TG_BOT_TOKEN"
    parsed = parse_qs(init_data, keep_blank_values=True)
    supplied = (parsed.get("hash") or [""])[0]
    if not supplied:
        return False, None, "missing hash"
    pairs = []
    for key in sorted(k for k in parsed if k != "hash"):
        pairs.append(f"{key}={parsed[key][0]}")
    check_string = "\n".join(pairs)
    secret = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, supplied):
        return False, None, "invalid initData hash"
    user = None
    try:
        user_raw = (parsed.get("user") or [""])[0]
        user = json.loads(user_raw) if user_raw else None
    except Exception:
        user = None
    allowed = os.environ.get("LIFEOS_TG_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID") or ""
    if allowed and user and str(user.get("id")) != str(allowed).strip():
        return False, user, "telegram user not allowed"
    return True, user, ""


def node_xp(node_id: str) -> int:
    candidates = [OUT / "learn" / "graph-store.json", OUT / "learn" / "knowledge-graph.json"]
    for path in candidates:
        try:
            graph = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in graph.get("nodes", []):
            if node.get("id") == node_id:
                try:
                    return int(node.get("xp") or 80)
                except Exception:
                    return 80
    return 80


def record_learning_progress(payload: dict[str, Any], user: dict[str, Any] | None) -> dict[str, Any]:
    node_id = str(payload.get("node_id") or payload.get("lesson_id") or "").strip()
    if not node_id:
        return {"ok": False, "error": "missing node_id"}
    xp_value = node_xp(node_id)
    progress = load_learning_progress()
    progress.setdefault("done", {})[node_id] = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "xp": xp_value,
        "score": payload.get("score"),
        "result": payload.get("result") or "complete",
        "lesson_id": payload.get("lesson_id") or node_id,
        "source": "telegram-mini-app",
        "telegram_user": user or {},
    }
    save_learning_progress(progress)
    total = sum(int(item.get("xp") or 0) for item in progress.get("done", {}).values() if isinstance(item, dict))
    level = 4 if total >= 1440 else 3 if total >= 720 else 2 if total >= 240 else 1
    return {"ok": True, "node_id": node_id, "xp": xp_value, "total_xp": total, "level": level}


MOBILE_HTML = """<!doctype html><html lang='en'><head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>
<meta name='color-scheme' content='dark'>
<title>LifeOS Control</title>
<style>
:root{--bg:#020403;--card:#0a140f;--line:#143025;--fg:#d7ffe8;--accent:#39ff88;--cyan:#00f5ff;--muted:#6f9a85}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--fg);margin:0;padding:16px 16px 64px;max-width:640px;margin:0 auto}
header{display:flex;align-items:baseline;justify-content:space-between;gap:8px;position:sticky;top:0;background:var(--bg);padding:8px 0 12px;z-index:5}
h1{font-size:20px;margin:0}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:24px 0 8px}
#status{font-size:12px;color:var(--accent);min-height:14px}
section{margin-bottom:8px}
form{display:flex;gap:8px}
input,select,button,textarea{font:inherit;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--fg);padding:12px}
input,textarea{flex:1;min-width:0}
button{background:var(--accent);color:#021008;border:none;font-weight:700;cursor:pointer}
button.ghost{background:var(--card);color:var(--fg);border:1px solid var(--line)}
.row{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:8px}
.row .done{flex:none;width:44px;height:44px;border-radius:50%;font-size:18px;background:transparent;border:2px solid var(--accent);color:var(--accent)}
.row small{color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:8px}
.card small{display:block;color:var(--muted);margin:4px 0 10px}
.risk{font-size:11px;text-transform:uppercase;color:var(--cyan);border:1px solid var(--line);border-radius:6px;padding:1px 6px;margin-left:6px}
.btns{display:flex;gap:8px}
.btns .reject{background:#2a0f12;color:#ff8a8a}
.empty{color:var(--muted);font-style:italic}
details summary{color:var(--muted);cursor:pointer;font-size:12px;margin-bottom:8px}
#tokrow{margin-top:8px}
#refresh{width:100%;margin-top:24px}
</style></head><body>
<header><h1>LifeOS <small style='font-size:11px;color:var(--muted)'>control</small></h1><a href='/learn' style='font-size:13px;color:var(--accent);text-decoration:none'>🌅 Learn</a><span id='status'></span></header>

<section><form id='addform'>
  <input id='addtext' placeholder='Add a todo…' enterkeyhint='done' autocomplete='off'>
  <select id='addsection'><option>Today</option><option>Soon</option><option>Parking Lot</option></select>
  <button>Add</button>
</form></section>

<section><form id='capform'>
  <input id='captext' placeholder='Capture research…' enterkeyhint='done' autocomplete='off'>
  <button>Save</button>
</form></section>

<details><summary>LAN write token (set once per device)</summary>
<form id='tokrow'><input id='tok' placeholder='LIFEOS_WRITE_TOKEN' autocomplete='off'><button class='ghost' id='savetok' type='button'>Save</button></form>
</details>

<h2>Todos</h2><div id='todos'></div>
<h2>Pending actions</h2><div id='actions'></div>
<button class='ghost' id='refresh'>↻ Reload</button>

<script>
const $=s=>document.querySelector(s);
const tok=()=>localStorage.getItem('lifeos_tok')||'';
function esc(s){const e=document.createElement('div');e.textContent=s==null?'':String(s);return e.innerHTML;}
function flash(m){$('#status').textContent=m;setTimeout(()=>{$('#status').textContent='';},1600);}
async function post(path,data){
  const body=new URLSearchParams(data);const t=tok();if(t)body.set('token',t);
  const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded','X-LifeOS-Write-Token':t},body});
  if(r.status===403){flash('Blocked: set write token');return null;}
  return r;
}
function renderTodos(items){
  $('#todos').innerHTML=items.length?items.map(i=>
    `<div class='row'><button class='done' data-id='${esc(i.id)}'>✓</button><div><div>${esc(i.text)}</div><small>${esc(i.section)}</small></div></div>`
  ).join(''):"<p class='empty'>All clear 🎉</p>";
}
function renderActions(items){
  $('#actions').innerHTML=items.length?items.map(a=>
    `<div class='card'><div><b>${esc(a.title)}</b><span class='risk'>${esc(a.risk_level)}</span></div><small>${esc(a.preview||a.purpose)}</small><div class='btns'><button class='approve' data-id='${esc(a.id)}'>Approve</button><button class='reject' data-id='${esc(a.id)}'>Reject</button></div></div>`
  ).join(''):"<p class='empty'>No pending actions</p>";
}
async function load(){
  try{const d=await (await fetch('/api/state')).json();renderTodos(d.todos||[]);renderActions(d.actions||[]);flash('updated '+new Date().toLocaleTimeString());}
  catch(e){flash('offline');}
}
document.addEventListener('click',async e=>{
  const b=e.target.closest('button');if(!b||!b.dataset.id)return;const id=b.dataset.id;
  if(b.classList.contains('done')){b.textContent='…';if(await post('/api/todo/complete',{id}))load();}
  else if(b.classList.contains('approve')){if(await post('/api/actions/approve',{id}))load();}
  else if(b.classList.contains('reject')){if(confirm('Reject this action?')&&await post('/api/actions/reject',{id}))load();}
});
$('#addform').onsubmit=async e=>{e.preventDefault();const t=$('#addtext').value.trim();if(!t)return;if(await post('/api/todo/add',{text:t,section:$('#addsection').value})){$('#addtext').value='';load();}};
$('#capform').onsubmit=async e=>{e.preventDefault();const t=$('#captext').value.trim();if(!t)return;if(await post('/research/capture-api',{text:t,kind:'source'})){$('#captext').value='';flash('Captured');}};
$('#refresh').onclick=load;
$('#tok').value=tok();
$('#savetok').onclick=()=>{localStorage.setItem('lifeos_tok',$('#tok').value.trim());flash('Token saved');};
load();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    MUTATION_PATHS = {
        "/todo/complete",
        "/todo/add",
        "/crm/stage",
        "/actions/approve",
        "/actions/reject",
        "/research/capture",
        "/research/capture-api",
        "/api/todo/complete",
        "/api/todo/add",
        "/api/actions/approve",
        "/api/actions/reject",
        "/api/progress",
    }

    def is_loopback_client(self) -> bool:
        host = self.client_address[0] if self.client_address else ""
        return host in {"127.0.0.1", "::1", "localhost"} or host.startswith("127.")

    @staticmethod
    def _header_hostname(raw: str) -> str:
        host = raw.split(",", 1)[0].strip().lower()
        if host.startswith("[") and "]" in host:
            return host[1:].split("]", 1)[0]
        return host.rsplit(":", 1)[0] if ":" in host else host

    @staticmethod
    def _host_is_local(host: str) -> bool:
        if not host:
            return True
        if host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
            return True
        try:
            ip = ipaddress.ip_address(host)
            return ip.is_loopback or ip.is_private or ip.is_link_local
        except ValueError:
            return "." not in host or host.endswith(".local")

    def is_public_request(self) -> bool:
        public_url = os.environ.get("LIFEOS_PUBLIC_URL", "").strip()
        public_host = self._header_hostname(urlparse(public_url).netloc) if public_url else ""
        forwarded_host = self._header_hostname(self.headers.get("X-Forwarded-Host", ""))
        host = self._header_hostname(self.headers.get("Host", ""))
        if self.headers.get("CF-Connecting-IP"):
            return True
        if public_host and (host == public_host or forwarded_host == public_host):
            return True
        if forwarded_host and not self._host_is_local(forwarded_host):
            return True
        return self.is_loopback_client() and bool(host) and not self._host_is_local(host)

    @staticmethod
    def public_get_allowed(path: str) -> bool:
        return path in {"/learn", "/learn/"} or (
            path.startswith("/output/learn/") and path.endswith(".html")
        )

    def mutation_allowed(self, data: dict[str, list[str]]) -> bool:
        if self.is_public_request():
            return False
        if self.is_loopback_client():
            return True
        token = os.environ.get("LIFEOS_WRITE_TOKEN", "")
        if not token:
            return False
        supplied = data.get("token", [""])[0] or self.headers.get("X-LifeOS-Write-Token", "")
        return supplied == token

    def reject_mutation(self) -> None:
        body = b"Mutation blocked. LAN/public writes require LIFEOS_WRITE_TOKEN or Telegram initData."
        self.send_response(403)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)

    def reject_public_route(self) -> None:
        body = b"Public LifeOS tunnel only serves /learn, /output/learn/*.html, and authenticated /api/progress."
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

    def send_json(self, payload: Any, code: int = 200) -> None:
        body = (json.dumps(payload, default=str) + "\n").encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if self.is_public_request() and not self.public_get_allowed(parsed.path):
            self.reject_public_route()
            return
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
        if parsed.path == "/api/state":
            self.send_json(state_payload())
            return
        if parsed.path in ("/learn", "/learn/"):
            index = OUT / "learn" / "index.html"
            if not index.exists():
                run([sys.executable, "tools/lifeos_lessons.py", "build"], timeout=60)
            if index.exists():
                body = index.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        if parsed.path in ("/private", "/private/"):
            index = OUT / "private-readings" / "index.html"
            if not index.exists():
                run([sys.executable, "tools/lifeos_private_library.py", "build"], timeout=60)
            if index.exists():
                body = index.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        if parsed.path in ("/m", "/mobile", "/control"):
            body = MOBILE_HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/phone":
            ip = local_ip()
            url = f"http://{ip}:{PORT}"
            body = f"""<!doctype html><meta charset='utf-8'><title>LifeOS Phone Access</title><body style='font-family:system-ui;background:#020403;color:#d7ffe8;padding:32px'><h1>LifeOS Phone Access</h1><p>Start the server in LAN mode, then open this URL on your phone while on the same Wi-Fi:</p><p style='font-size:24px'><a style='color:#39ff88' href='{url}/m'>{url}/m</a></p><p>The <b>/m</b> control panel lets you complete todos, add todos, capture research, and approve/reject actions from your phone.</p><p>If it does not load, Windows Firewall is blocking Python or the server was started local-only.</p><p><a style='color:#00f5ff' href='/m'>Open control panel</a> &middot; <a style='color:#00f5ff' href='/'>Dashboard</a></p></body>""".encode()
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
        raw_body = self.rfile.read(length).decode("utf-8")
        parsed = urlparse(self.path)
        if parsed.path == "/api/progress":
            try:
                payload = json.loads(raw_body or "{}")
            except Exception:
                self.send_json({"ok": False, "error": "invalid json"}, 400)
                return
            ok, user, error = telegram_init_data(str(payload.get("initData") or ""))
            if not ok:
                self.send_json({"ok": False, "error": error}, 401)
                return
            result = record_learning_progress(payload, user)
            self.send_json(result, 200 if result.get("ok") else 400)
            return
        data = parse_qs(raw_body)
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
        if parsed.path == "/api/todo/complete":
            ok = complete_todo(data.get("id", [""])[0])
            self.send_json({"ok": ok}, 200 if ok else 400)
            return
        if parsed.path == "/api/todo/add":
            ok = add_todo(data.get("text", [""])[0], data.get("section", ["Today"])[0])
            self.send_json({"ok": ok}, 200 if ok else 400)
            return
        if parsed.path == "/api/actions/approve":
            rc = update_status(data.get("id", [""])[0], "approved", "phone")
            self.send_json({"ok": rc == 0, "code": rc}, 200 if rc == 0 else 400)
            return
        if parsed.path == "/api/actions/reject":
            rc = update_status(data.get("id", [""])[0], "rejected", "phone")
            self.send_json({"ok": rc == 0, "code": rc}, 200 if rc == 0 else 400)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    if os.environ.get("LIFEOS_SKIP_BOOT_REFRESH", "").lower() not in ("1", "true", "yes"):
        refresh()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"http://{HOST}:{PORT}")
    if HOST in ("0.0.0.0", ""):
        print(f"phone: http://{local_ip()}:{PORT}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
