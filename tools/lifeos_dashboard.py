#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

from lifeos_audit import log_event
from lifeos_todos import open_items

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
SERVER_URL = ""
OUT = ROOT / "output"
REPORTS = OUT / "reports"
RESEARCH_INBOX = ROOT / "raw" / "research" / "inbox.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def section(md: str, name: str) -> str:
    pattern = rf"^## {re.escape(name)}\n(?P<body>.*?)(?=^## |\Z)"
    m = re.search(pattern, md, flags=re.M | re.S)
    return m.group("body").strip() if m else ""


def bullets(md: str) -> list[str]:
    out: list[str] = []
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("- [ ] "):
            out.append(s[6:])
        elif re.match(r"^\d+\.\s+", s):
            out.append(re.sub(r"^\d+\.\s+", "", s))
        elif s.startswith("- "):
            out.append(s[2:])
    return out


def inline_html(text: str, *, linkify: bool = True) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    if not linkify:
        return escaped
    url_re = re.compile(r"(https?://[^\s<]+)")
    return url_re.sub(lambda m: f"<a class='inline-link' href='{m.group(1)}' target='_blank' rel='noreferrer'>{m.group(1)}</a>", escaped)


def render_list(items: list[str], empty: str) -> str:
    if not items:
        return f"<p class='muted'>{html.escape(empty)}</p>"
    return "<ul>" + "".join(f"<li>{inline_html(i)}</li>" for i in items) + "</ul>"


def item_url(item: object) -> str:
    if not isinstance(item, dict):
        return ""
    url = item.get("url") or item.get("html_url") or item.get("web_url")
    return str(url or "")


def linked_item(item: object, prefix: str = "") -> str:
    text = item_text(item)
    url = item_url(item)
    label = inline_html((prefix + text).strip(), linkify=False)
    if url:
        return f"<a class='inline-link' href='{html.escape(url)}' target='_blank' rel='noreferrer'>{label}</a>"
    return label


def hide_attention_items(items: list[str]) -> list[str]:
    blocked = ("attention", "brainrot", "instagram", "tiktok", "shorts", "porn")
    return [item for item in items if not any(term in item.lower() for term in blocked)]


def todo_items(limit: int = 10) -> list[dict[str, object]]:
    return open_items(limit)


def todo_panel(items: list[dict[str, object]]) -> str:
    rows = []
    for item in items:
        text = str(item.get("text", ""))
        item_id = str(item.get("id", ""))
        section_name = str(item.get("section", ""))
        rows.append(
            "<li>"
            f"<form method='post' action='{SERVER_URL}/todo/complete' class='inline-form'>"
            f"<input type='hidden' name='id' value='{html.escape(item_id)}'>"
            f"<button class='tiny-button' title='Mark done'>✓</button>"
            f"</form> <span class='tag'>{html.escape(section_name)}</span> {inline_html(text)}"
            "</li>"
        )
    add = f"""
<form method='post' action='{SERVER_URL}/todo/add' class='add-form'>
  <input name='text' placeholder='Add todo...' autocomplete='off'>
  <input type='hidden' name='section' value='Today'>
  <button title='Add todo'>+</button>
</form>
"""
    body = "<ul>" + "".join(rows) + "</ul>" if rows else "<p class='muted'>No open todos found.</p>"
    return body + add


def latest_brief() -> Path | None:
    briefs = sorted(REPORTS.glob("daily-brief-*.md"))
    return briefs[-1] if briefs else None


def latest_research_briefs() -> list[Path]:
    briefs = sorted(REPORTS.glob("*-morning-brief-*.md"), reverse=True)
    return briefs[:4]


def research_inbox_items(limit: int = 5) -> list[str]:
    if not RESEARCH_INBOX.exists():
        return []
    items = []
    for line in reversed(RESEARCH_INBOX.read_text(encoding="utf-8").splitlines()):
        if line.startswith("- "):
            items.append(line[2:])
        if len(items) >= limit:
            break
    return items


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}


def item_text(item: object) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return str(item)
    for keys in [("title", "source"), ("summary", "start"), ("subject", "sender"), ("title", "repository"), ("name", "email")]:
        left = item.get(keys[0])
        right = item.get(keys[1])
        if left and right:
            if isinstance(right, dict):
                right = right.get("name") or right.get("fullName") or str(right)
            return f"{left} — {right}"
    return str(item.get("summary") or item.get("subject") or item.get("title") or item.get("name") or item.get("workflowName") or item.get("url") or item)


def connector_list(conn: dict, empty: str) -> str:
    if not conn.get("configured"):
        return f"<p class='muted'>{html.escape(conn.get('error') or conn.get('status') or empty)}</p>"
    items = [linked_item(i) for i in conn.get("items") or []]
    if not items:
        return f"<p class='muted'>Connected. {html.escape(empty)}</p>"
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def email_panel(conn: dict) -> str:
    providers = conn.get("providers") or {}
    cats = conn.get("categories") or {}
    chunks = []
    provider_bits = []
    for name in ["gmail", "outlook"]:
        p = providers.get(name) or {}
        state = "ONLINE" if p.get("configured") else "SETUP"
        provider_bits.append(f"<span class='tag'>{html.escape(name.upper())}: {state}</span>")
    chunks.append("<p class='muted'>" + " ".join(provider_bits) + "</p>")
    for name in ["Priority Inbox", "Needs Reply", "Opportunities", "LinkedIn Signals", "Receipts / Security"]:
        rows = []
        for item in cats.get(name, [])[:5]:
            provider = item.get("provider", "EMAIL") if isinstance(item, dict) else "EMAIL"
            rows.append(linked_item(item, f"[{provider}] "))
        body = "<ul>" + "".join(f"<li>{row}</li>" for row in rows) + "</ul>" if rows else "<p class='muted'>Clear.</p>"
        chunks.append(f"<div class='mini'><h3>{html.escape(name)}</h3>{body}</div>")
    if not conn.get("configured"):
        chunks.append("<p class='muted'>Connect Gmail/Outlook to populate live email actions.</p>")
    return "".join(chunks)


def crm_panel(conn: dict) -> str:
    people = conn.get("items") or []
    if not people:
        return "<p class='muted'>No relationship targets queued.</p>"
    chunks = []
    for idx, person in enumerate(people[:4], start=1):
        if not isinstance(person, dict):
            continue
        title = f"{person.get('name')} — {person.get('tag')}"
        body = f"{person.get('space')} | {person.get('angle')}"
        buttons = "".join(
            f"<form method='post' action='{SERVER_URL}/crm/stage' class='inline-form'><input type='hidden' name='index' value='{idx}'><input type='hidden' name='channel' value='{channel}'><button class='tiny-button'>{label}</button></form>"
            for channel, label in [("x", "X"), ("linkedin", "LI"), ("email", "Email")]
        )
        chunks.append(f"<li><strong>{html.escape(title)}</strong><br><span class='muted'>{inline_html(body)}</span><div class='mini-actions'>{buttons}</div></li>")
    return "<ul>" + "".join(chunks) + f"</ul><div class='actions'><a class='action' href='{SERVER_URL}/data/lifeos/crm.json'>CRM JSON</a></div>"


def github_panel(conn: dict) -> str:
    if not conn.get("configured"):
        return f"<p class='muted'>{html.escape(conn.get('error') or 'GitHub not connected.')}</p>"
    cats = conn.get("categories") or {}
    chunks = []
    for name in ["Assigned Issues", "PRs Needing Review", "Failed Workflows"]:
        items = [linked_item(i) for i in cats.get(name, [])[:4]]
        body = "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>" if items else "<p class='muted'>Clear.</p>"
        chunks.append(f"<div class='mini'><h3>{html.escape(name)}</h3>{body}</div>")
    return "".join(chunks)


def tool_status(label: str, conn: dict) -> str:
    state = "ONLINE" if conn.get("configured") else "SETUP"
    return f"<li><span class='tool-state'>{state}</span> {html.escape(label)} — {html.escape(conn.get('status') or conn.get('error') or '')}</li>"


def actions_panel(conn: dict) -> str:
    items = conn.get("items") or []
    if not items:
        return "<p class='muted'>No pending actions.</p>"
    rows = []
    for action in items:
        if not isinstance(action, dict):
            continue
        action_id = html.escape(str(action.get("id") or ""))
        title = html.escape(str(action.get("title") or action.get("preview") or "Untitled action"))
        risk = html.escape(str(action.get("risk_level") or "medium").upper())
        preview = html.escape(str(action.get("preview") or ""))
        buttons = (
            f"<form method='post' action='{SERVER_URL}/actions/approve' class='inline-form'><input type='hidden' name='id' value='{action_id}'><button class='tiny-button'>Approve</button></form>"
            f"<form method='post' action='{SERVER_URL}/actions/reject' class='inline-form'><input type='hidden' name='id' value='{action_id}'><button class='tiny-button danger-button'>Reject</button></form>"
        )
        rows.append(f"<li><span class='tag'>{risk}</span> <strong>{title}</strong><br><span class='muted'>{preview}</span><div class='mini-actions'>{buttons}</div></li>")
    return "<ul>" + "".join(rows) + f"</ul><div class='actions'><a class='action' href='{SERVER_URL}/output/lifeos-actions.json'>Queue JSON</a></div>"


def policy_panel(policy: dict) -> str:
    rules = policy.get("rules") or []
    items = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        marker = "APPROVAL" if rule.get("approval_required") else "AUTO"
        items.append(f"{marker}: {rule.get('kind')} → {rule.get('default_handling')}")
    return render_list(items, "No policy rules found.")


def markdown_to_html(md: str) -> str:
    parts: list[str] = []
    in_list = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if in_list:
                parts.append("</ul>")
                in_list = False
            continue
        if line.startswith("# "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_list:
                parts.append("<ul>")
                in_list = True
            parts.append(f"<li>{html.escape(line[2:])}</li>")
        else:
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<p>{html.escape(line)}</p>")
    if in_list:
        parts.append("</ul>")
    return "".join(parts)


def research_panel(paths: list[Path]) -> tuple[str, str]:
    if not paths:
        return "<p class='muted'>No morning research briefs queued.</p>", ""
    items = []
    templates = []
    for idx, path in enumerate(paths):
        title = path.stem.replace("-", " ").title()
        text = read(path)
        summary = section(text, "TL;DR") or section(text, "Summary")
        first = " ".join(summary.split())[:180] if summary else "Queued research brief."
        rid = f"research-{idx}"
        items.append(f"<li><button class='inline-button' data-reader='{rid}'>{html.escape(title)}</button><br><span class='muted'>{html.escape(first)}</span></li>")
        templates.append(f"<template id='{rid}'><article>{markdown_to_html(text)}</article></template>")
    return "<ul>" + "".join(items) + "</ul>", "".join(templates)


def main() -> int:
    brief_path = latest_brief()
    research_briefs = latest_research_briefs()
    brief = read(brief_path) if brief_path else ""
    now = datetime.now()
    today = f"{now.strftime('%A')}, {now.strftime('%B')} {now.day}, {now.year}"

    connectors = read_json(OUT / "lifeos-connectors.json")
    priorities = hide_attention_items(bullets(section(brief, "Top Priorities")))[:8]
    todos = todo_items(10)
    health = hide_attention_items(bullets(section(brief, "Health Defaults")))[:6]
    calendar_conn = connectors.get("calendar", {})
    email_conn = connectors.get("email", {})
    gmail_conn = connectors.get("gmail", {})
    github_conn = connectors.get("github", {})
    telegram_conn = connectors.get("telegram", {})
    actions_conn = connectors.get("actions", {})
    archive_conn = connectors.get("archive", {})
    crm_conn = connectors.get("crm", {})
    policy_conn = connectors.get("policy", {})
    cursor_conn = connectors.get("cursor", {})
    gemini_conn = connectors.get("gemini", {})
    social = section(brief, "Social / Texts") or "Not connected yet."
    research_html, research_templates = research_panel(research_briefs)
    brief_template = f"<template id='daily-brief'><article>{markdown_to_html(brief)}</article></template>" if brief else ""
    research_inbox_html = render_list(research_inbox_items(), "No captured research yet.")

    css = """
:root { color-scheme: dark; --bg:#020403; --card:#04110b; --card2:#071a10; --text:#d7ffe8; --muted:#78a88d; --accent:#39ff88; --accent2:#00f5ff; --danger:#ff2bd6; --warn:#d7ff39; }
* { box-sizing: border-box; }
html { min-height:100%; background:#020403; }
body { margin:0; min-height:100vh; font-family: "Share Tech Mono", "Cascadia Mono", "Consolas", "Segoe UI", monospace; color:var(--text); background:#020403; }
body:before { content:""; position:fixed; inset:0; pointer-events:none; background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='34' height='34' viewBox='0 0 34 34'%3E%3Cpath d='M34 0H0V34' fill='none' stroke='%2339ff88' stroke-opacity='.08'/%3E%3C/svg%3E"); opacity:.9; z-index:10; }
body:after { content:""; position:fixed; inset:0; pointer-events:none; box-shadow: inset 0 0 140px rgba(0,0,0,.86); z-index:11; }
main { max-width:1220px; margin:0 auto; padding:34px; position:relative; z-index:1; }
.hero { display:flex; justify-content:space-between; gap:24px; align-items:flex-end; margin-bottom:24px; border-bottom:1px solid rgba(57,255,136,.35); padding-bottom:18px; }
h1 { font-size:48px; margin:0; letter-spacing:-0.06em; color:#ecfff4; text-transform:uppercase; text-shadow:0 0 10px rgba(57,255,136,.8), 2px 0 0 rgba(255,43,214,.45), -2px 0 0 rgba(0,245,255,.42); }
.date { color:var(--accent); font-size:16px; border:1px solid rgba(57,255,136,.5); padding:10px 12px; background:rgba(4,17,11,.72); box-shadow:0 0 24px rgba(57,255,136,.16); }
.grid { display:grid; grid-template-columns: 1.2fr 1fr; gap:18px; }
.row { display:grid; grid-template-columns: repeat(3,1fr); gap:18px; margin-top:18px; }
.card { position:relative; background:#04110b; border:1px solid rgba(57,255,136,.42); border-radius:4px; padding:22px; box-shadow:0 0 0 1px rgba(0,245,255,.06), 0 0 28px rgba(57,255,136,.12), 0 18px 70px rgba(0,0,0,.55); overflow:hidden; }
.card:before { content:""; position:absolute; left:0; right:0; top:0; height:2px; background:var(--accent); opacity:.9; box-shadow:0 0 18px rgba(57,255,136,.7); }
.card:after { content:""; position:absolute; inset:0; pointer-events:none; border:1px solid rgba(0,245,255,.08); }
.card h2 { position:relative; z-index:1; margin:0 0 14px; font-size:17px; color:var(--accent); display:flex; align-items:center; gap:10px; text-transform:uppercase; letter-spacing:.08em; text-shadow:0 0 8px rgba(57,255,136,.65); }
.mini { position:relative; z-index:1; border-top:1px solid rgba(57,255,136,.18); padding-top:10px; margin-top:10px; }
.mini h3 { margin:0 0 8px; color:var(--accent2); font-size:13px; text-transform:uppercase; letter-spacing:.08em; }
.badge { font-size:11px; color:#031006; border:1px solid rgba(57,255,136,.9); border-radius:0; padding:4px 8px; background:var(--accent); box-shadow:0 0 14px rgba(57,255,136,.42); }
.tag { display:inline-block; color:#031006; background:var(--accent2); padding:2px 6px; margin:0 6px 6px 0; font-size:11px; }
ul { position:relative; z-index:1; margin:0; padding-left:20px; }
li { margin:10px 0; line-height:1.4; }
li::marker { color:var(--accent); }
.muted { position:relative; z-index:1; color:var(--muted); line-height:1.45; }
.big { min-height:320px; }
.kicker { color:var(--accent2); font-weight:700; text-transform:uppercase; font-size:12px; letter-spacing:.18em; text-shadow:0 0 10px rgba(0,245,255,.75); }
.actions { position:relative; z-index:1; display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; }
.action { color:var(--accent); text-decoration:none; border:1px solid rgba(57,255,136,.55); padding:10px 12px; border-radius:0; background:rgba(2,8,5,.92); box-shadow:inset 0 0 12px rgba(57,255,136,.08); text-transform:uppercase; }
.action:hover { background:rgba(57,255,136,.14); color:#fff; box-shadow:0 0 18px rgba(57,255,136,.35); }
.action-button { font:inherit; cursor:pointer; }
.inline-form { display:inline; margin:0 4px 0 0; }
.mini-actions { display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }
.tiny-button { color:#031006; background:var(--accent); border:0; padding:3px 7px; font:inherit; cursor:pointer; box-shadow:0 0 10px rgba(57,255,136,.25); }
.danger-button { background:var(--danger); color:#fff; }
.add-form { position:relative; z-index:1; display:flex; gap:8px; margin-top:16px; }
.add-form input { flex:1; min-width:0; color:var(--text); background:#020403; border:1px solid rgba(57,255,136,.45); padding:10px; font:inherit; }
.add-form button { color:#031006; background:var(--accent); border:0; padding:10px 14px; font:inherit; cursor:pointer; }
.inline-link { color:var(--accent2); text-decoration:none; border-bottom:1px dotted rgba(0,245,255,.45); }
.inline-link:hover { color:#fff; text-shadow:0 0 10px rgba(0,245,255,.7); }
code { color:var(--warn); background:rgba(215,255,57,.08); border:1px solid rgba(215,255,57,.18); padding:1px 4px; }
.inline-button { color:var(--accent2); background:transparent; border:0; padding:0; font:inherit; text-align:left; cursor:pointer; }
.inline-button:hover { color:#fff; text-shadow:0 0 10px rgba(0,245,255,.7); }
.reader { display:none; position:fixed; inset:22px; z-index:30; background:#020403; border:1px solid rgba(57,255,136,.72); box-shadow:0 0 70px rgba(57,255,136,.18), inset 0 0 80px rgba(0,0,0,.8); padding:22px; overflow:auto; }
.reader.open { display:block; }
.reader-bar { position:sticky; top:-22px; background:#020403; border-bottom:1px solid rgba(57,255,136,.35); padding:0 0 12px; margin-bottom:18px; display:flex; justify-content:space-between; gap:12px; align-items:center; z-index:2; }
.reader-close { color:#031006; background:var(--accent); border:0; padding:8px 12px; font:inherit; cursor:pointer; text-transform:uppercase; }
.reader-content { max-width:920px; margin:0 auto; line-height:1.55; }
.reader-content h1 { font-size:34px; letter-spacing:-.04em; }
.reader-content h2 { color:var(--accent); margin-top:28px; text-transform:uppercase; }
.reader-content h3 { color:var(--accent2); margin-top:20px; }
.reader-content p { color:var(--text); }
.focus-buttons { position:relative; z-index:1; display:flex; gap:8px; flex-wrap:wrap; }
.focus-button { color:#031006; background:var(--accent); border:0; padding:9px 11px; font:inherit; cursor:pointer; text-transform:uppercase; box-shadow:0 0 14px rgba(57,255,136,.28); }
.focus-clock { display:none; position:fixed; right:18px; bottom:18px; z-index:40; min-width:230px; background:#020403; border:1px solid rgba(57,255,136,.75); box-shadow:0 0 42px rgba(57,255,136,.22), inset 0 0 22px rgba(57,255,136,.06); padding:14px; }
.focus-clock.open { display:block; }
.focus-clock-title { color:var(--accent2); font-size:12px; text-transform:uppercase; letter-spacing:.14em; }
.focus-clock-time { color:#ecfff4; font-size:38px; line-height:1; margin:10px 0; text-shadow:0 0 14px rgba(57,255,136,.75); }
.focus-clock-actions { display:flex; gap:8px; }
.focus-clock-actions button { color:var(--accent); background:#020403; border:1px solid rgba(57,255,136,.55); padding:6px 8px; font:inherit; cursor:pointer; }
.tool-state { color:#031006; background:var(--accent); padding:2px 6px; margin-right:6px; box-shadow:0 0 10px rgba(57,255,136,.38); }
.footer { margin-top:18px; color:var(--muted); font-size:13px; }
@media (max-width: 850px) { .grid,.row { grid-template-columns:1fr; } main{padding:20px;} h1{font-size:34px;} .hero{display:block;} .date{display:inline-block;margin-top:14px;} }
"""
    doc = f"""<!doctype html>
<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>LifeOS Dashboard</title><style>{css}</style></head>
<body><main>
  <div class='hero'>
    <div><div class='kicker'>Adarsha LifeOS</div><h1>Morning Command Center</h1></div>
    <div class='date'>{html.escape(today)}</div>
  </div>
  <section class='grid'>
    <div class='card big'><h2>Top Priorities <span class='badge'>focus</span></h2>{render_list(priorities, 'No priorities found.')}<div class='actions'><button class='action action-button' data-reader='daily-brief'>Open Full Brief</button></div></div>
    <div class='card big'><h2>Todos <span class='badge'>next actions</span></h2>{todo_panel(todos)}</div>
  </section>
  <section class='row'>
    <div class='card'><h2>Morning Research <span class='badge'>learn</span></h2>{research_html}</div>
    <div class='card'><h2>Email Command Center</h2>{email_panel(email_conn)}</div>
    <div class='card'><h2>People CRM <span class='badge'>outreach</span></h2>{crm_panel(crm_conn)}</div>
  </section>
  <section class='row'>
    <div class='card'><h2>Calendar</h2>{connector_list(calendar_conn, 'No upcoming events found.')}</div>
    <div class='card'><h2>GitHub</h2>{github_panel(github_conn)}</div>
    <div class='card'><h2>Learning Queue</h2>{research_html}</div>
  </section>
  <section class='row'>
    <div class='card'><h2>Research Inbox <span class='badge'>capture</span></h2>{research_inbox_html}<form method='post' action='{SERVER_URL}/research/capture' class='add-form'><input name='text' placeholder='Paste paper/link/tweet/topic...' autocomplete='off'><input type='hidden' name='kind' value='source'><button title='Capture research'>+</button></form><div class='actions'><a class='action' href='{SERVER_URL}/raw/research/inbox.md'>Open Inbox</a></div></div>
  </section>
  <section class='row'>
    <div class='card'><h2>Approval Queue</h2>{actions_panel(actions_conn)}</div>
    <div class='card'><h2>Focus Timer <span class='badge'>lock in</span></h2><p class='muted'>Start a session. Timer stays pinned bottom-right while you work.</p><div class='focus-buttons'><button class='focus-button' data-focus-min='25'>25m</button><button class='focus-button' data-focus-min='50'>50m</button><button class='focus-button' data-focus-min='90'>90m</button></div></div>
    <div class='card'><h2>Quick Links</h2><div class='actions'><a class='action' href='{SERVER_URL}/wiki/personal/daily-todo.md'>Todo file</a><a class='action' href='{SERVER_URL}/wiki/personal/daily-command-center.md'>Spec</a><a class='action' href='{SERVER_URL}/output/lifeos-setup.html'>Setup</a><a class='action' href='{SERVER_URL}/reports'>Reports</a><a class='action' href='{SERVER_URL}/output/lifeos-connectors.json'>Connectors JSON</a></div></div>
    <div class='card'><h2>Local Archive</h2>{connector_list(archive_conn, 'No cached records yet.')}<p class='muted'>{html.escape(archive_conn.get('status') or '')}</p></div>
    <div class='card'><h2>Action Policy</h2>{policy_panel(policy_conn)}<p class='muted'>No social feeds. No destructive/outbound actions without explicit approval.</p></div>
  </section>
  <section class='row'>
    <div class='card'><h2>Tools / Agents</h2><ul>{tool_status('Gmail', gmail_conn)}{tool_status('Outlook', connectors.get('outlook', {}))}{tool_status('Calendar', calendar_conn)}{tool_status('GitHub', github_conn)}{tool_status('Telegram', telegram_conn)}{tool_status('Cursor Agent', cursor_conn)}{tool_status('Gemini Worker', gemini_conn)}<li><span class='tool-state'>ONLINE</span> Approval staging — write actions queue before execution.</li><li><span class='tool-state'>ONLINE</span> Voice transcription — local faster-whisper ready.</li></ul></div>
  </section>
  <div class='footer'>Generated from {html.escape(str(brief_path.relative_to(ROOT)) if brief_path else 'no brief')} at {datetime.now().strftime('%H:%M:%S')}.</div>
</main>
<div id='reader' class='reader' aria-hidden='true'><div class='reader-bar'><div class='kicker'>LifeOS Reader</div><button id='reader-close' class='reader-close'>Close</button></div><div id='reader-content' class='reader-content'></div></div>
<div id='focus-clock' class='focus-clock' aria-live='polite'><div class='focus-clock-title'>Focus Session</div><div id='focus-clock-time' class='focus-clock-time'>25:00</div><div class='focus-clock-actions'><button id='focus-pause'>Pause</button><button id='focus-stop'>Stop</button></div></div>
{research_templates}
{brief_template}
<script>
const reader = document.getElementById('reader');
const readerContent = document.getElementById('reader-content');
function openReader(id) {{
  const tpl = document.getElementById(id);
  if (!tpl) return;
  readerContent.innerHTML = tpl.innerHTML;
  reader.classList.add('open');
  reader.setAttribute('aria-hidden', 'false');
  reader.scrollTop = 0;
}}
document.querySelectorAll('[data-reader]').forEach(btn => {{
  btn.addEventListener('click', () => openReader(btn.dataset.reader));
}});
if (location.hash.startsWith('#research-')) openReader(location.hash.slice(1));
document.getElementById('reader-close').addEventListener('click', () => {{
  reader.classList.remove('open');
  reader.setAttribute('aria-hidden', 'true');
}});
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') document.getElementById('reader-close').click(); }});

const lifeosBase = location.protocol === 'file:' ? 'http://127.0.0.1:8787' : '';
if (lifeosBase) {{
  document.querySelectorAll('form[action^="/"]').forEach(form => form.action = lifeosBase + form.getAttribute('action'));
  document.querySelectorAll('a[href^="/"]').forEach(a => a.href = lifeosBase + a.getAttribute('href'));
}}

const focusClock = document.getElementById('focus-clock');
const focusTime = document.getElementById('focus-clock-time');
const focusPause = document.getElementById('focus-pause');
const focusStop = document.getElementById('focus-stop');
let focusEnd = Number(localStorage.getItem('lifeosFocusEnd') || 0);
let focusRemaining = Number(localStorage.getItem('lifeosFocusRemaining') || 0);
let focusPaused = localStorage.getItem('lifeosFocusPaused') === '1';
function fmt(ms) {{
  const total = Math.max(0, Math.ceil(ms / 1000));
  const m = String(Math.floor(total / 60)).padStart(2, '0');
  const s = String(total % 60).padStart(2, '0');
  return `${{m}}:${{s}}`;
}}
function showFocus(ms) {{ focusClock.classList.add('open'); focusTime.textContent = fmt(ms); }}
function clearFocus() {{
  focusEnd = 0; focusRemaining = 0; focusPaused = false;
  localStorage.removeItem('lifeosFocusEnd'); localStorage.removeItem('lifeosFocusRemaining'); localStorage.removeItem('lifeosFocusPaused');
  focusClock.classList.remove('open'); focusPause.textContent = 'Pause';
}}
function startFocus(minutes) {{
  focusPaused = false; focusEnd = Date.now() + minutes * 60 * 1000; focusRemaining = 0;
  localStorage.setItem('lifeosFocusEnd', String(focusEnd)); localStorage.removeItem('lifeosFocusRemaining'); localStorage.removeItem('lifeosFocusPaused');
  showFocus(focusEnd - Date.now());
}}
function tickFocus() {{
  if (focusPaused) {{ showFocus(focusRemaining); return; }}
  if (!focusEnd) return;
  const remaining = focusEnd - Date.now();
  if (remaining <= 0) {{ showFocus(0); focusTime.textContent = 'DONE'; return; }}
  showFocus(remaining);
}}
document.querySelectorAll('[data-focus-min]').forEach(btn => btn.addEventListener('click', () => startFocus(Number(btn.dataset.focusMin))));
focusPause.addEventListener('click', () => {{
  if (!focusEnd && !focusRemaining) return;
  if (focusPaused) {{
    focusPaused = false; focusEnd = Date.now() + focusRemaining;
    localStorage.setItem('lifeosFocusEnd', String(focusEnd)); localStorage.removeItem('lifeosFocusPaused'); focusPause.textContent = 'Pause';
  }} else {{
    focusPaused = true; focusRemaining = Math.max(0, focusEnd - Date.now());
    localStorage.setItem('lifeosFocusRemaining', String(focusRemaining)); localStorage.setItem('lifeosFocusPaused', '1'); focusPause.textContent = 'Resume';
  }}
}});
focusStop.addEventListener('click', clearFocus);
if (focusPaused && focusRemaining) {{ focusPause.textContent = 'Resume'; showFocus(focusRemaining); }} else if (focusEnd > Date.now()) tickFocus();
setInterval(tickFocus, 1000);
</script>
</body></html>"""
    out = OUT / "lifeos-dashboard.html"
    out.write_text(doc, encoding="utf-8")
    log_event(
        "dashboard_refreshed",
        "lifeos_dashboard",
        brief=str(brief_path.relative_to(ROOT)) if brief_path else "",
        pending_actions=len(actions_conn.get("items") or []),
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
