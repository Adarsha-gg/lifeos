#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from lifeos_todos import open_items
from lifeos_web_digest import web_digest_summary

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
WIKI = ROOT / "wiki"
OUT = ROOT / "output" / "reports"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


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
    for key in ("summary", "subject", "title", "name", "workflowName", "url"):
        value = item.get(key)
        if value:
            return str(value)
    return str(item)


def item_link(item: object) -> str:
    if not isinstance(item, dict):
        return item_text(item)
    text = item_text(item)
    url = item.get("url") or item.get("html_url") or item.get("web_url")
    return f"[{text}]({url})" if url else text


def extract_tasks() -> list[str]:
    return [f"- [ ] {item.get('text', '')}" for item in open_items()]


def priority_keywords(priorities: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9-]{3,}", priorities.lower())
    stop = {"current", "priorities", "summary", "with", "from", "into", "this", "that", "action", "actions", "start", "build"}
    return [w for w in words if w not in stop]


def task_score(task: str, keywords: list[str]) -> int:
    text = task.lower()
    return sum(3 for k in keywords[:40] if k in text) + sum(1 for k in ["startup", "erc", "blockchain", "gym", "workout", "posture", "read", "brainrot", "lifeos", "oauth"] if k in text)


def linked_tasks(tasks: list[str], priorities: str) -> list[tuple[str, int]]:
    keywords = priority_keywords(priorities)
    scored = [(task, task_score(task, keywords)) for task in tasks]
    return sorted(scored, key=lambda item: item[1], reverse=True)


def main() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    out_path = OUT / f"daily-brief-{today}.md"
    OUT.mkdir(parents=True, exist_ok=True)

    priorities = read(WIKI / "personal" / "current-priorities.md")
    command = read(WIKI / "personal" / "daily-command-center.md")

    tasks = extract_tasks()
    scored_tasks = linked_tasks(tasks, priorities)
    top_tasks = [task for task, _ in scored_tasks[:8]]
    goal_linked = [(task, score) for task, score in scored_tasks if score > 0][:6]
    web_digest = web_digest_summary(6)
    connectors = read_json(ROOT / "output" / "lifeos-connectors.json")

    priority_body = priorities.split('##', 1)[1].strip() if '##' in priorities else '_No priorities page found._'
    priority_body = re.sub(r"^## ", "### ", priority_body, flags=re.M)

    body = f"""# Daily Brief — {today}

## Top Priorities

Source: `wiki/personal/current-priorities.md`

{priority_body}

## Open Todos

"""
    if top_tasks:
        body += "\n".join(top_tasks) + "\n"
    else:
        body += "_No open todos found in `data/lifeos/todos.json`._\n"

    body += "\n## Goal Links\n\n"
    if goal_linked:
        for task, score in goal_linked:
            body += f"- score {score}: {task[6:]}\n"
    else:
        body += "_No todos currently match `wiki/personal/current-priorities.md` keywords._\n"

    body += "\n## Web Digest\n\n"
    web_items = web_digest.get("items") or []
    if web_items:
        for item in web_items:
            title = item.get("title") or "Untitled"
            url = item.get("url") or ""
            source = item.get("source") or "web"
            score = item.get("score") or 0
            why = item.get("why") or "Matched morning web digest."
            link = f"[{title}]({url})" if url else title
            body += f"- score {score}: {link} — {source}. {why}\n"
        report = web_digest.get("report")
        if report:
            body += f"\nFull digest: `{report}`\n"
    else:
        status = web_digest.get("error") or web_digest.get("status") or "No web digest items yet."
        body += f"_{status}_\n"

    body += "\n## Calendar\n\n"
    calendar = connectors.get("calendar", {})
    if calendar.get("configured"):
        items = calendar.get("items") or []
        if items:
            for item in items[:8]:
                body += f"- {item_link(item)}\n"
        else:
            body += "_Calendar connected. No upcoming events found._\n"
    else:
        body += f"_{calendar.get('error') or 'Not connected yet. Authenticate a read-only calendar connector.'}_\n"

    body += "\n## Important Email\n\n"
    email = connectors.get("email", {})
    if email.get("configured"):
        categories = email.get("categories") or {}
        for category in ["Priority Inbox", "Needs Reply", "LinkedIn Signals", "Receipts / Security"]:
            rows = categories.get(category) or []
            body += f"### {category}\n"
            if rows:
                for item in rows[:5]:
                    provider = item.get("provider", "EMAIL") if isinstance(item, dict) else "EMAIL"
                    body += f"- [{provider}] {item_link(item)}\n"
            else:
                body += "_Clear._\n"
    else:
        providers = email.get("providers") or {}
        statuses = [str((providers.get(name) or {}).get("status") or "") for name in ["gmail", "outlook"]]
        message = "; ".join(s for s in statuses if s) or "Not connected yet. Add read-only email connectors."
        body += f"_{message}_\n"

    body += "\n## GitHub / Project Signals\n\n"
    github = connectors.get("github", {})
    if github.get("configured"):
        cats = github.get("categories") or {}
        any_rows = False
        for category in ["Assigned Issues", "PRs Needing Review", "Failed Workflows"]:
            rows = cats.get(category) or []
            if not rows:
                continue
            any_rows = True
            body += f"### {category}\n"
            for item in rows[:5]:
                body += f"- {item_link(item)}\n"
        if not any_rows:
            body += "_GitHub connected. No assigned issues, review requests, or failed workflows._\n"
    else:
        body += f"_{github.get('error') or 'GitHub not connected.'}_\n"

    body += "\n## Social / Texts\n\n"
    telegram = connectors.get("telegram", {})
    body += f"_{telegram.get('status') or 'Not connected yet. Keep this action-only: DMs, mentions, and messages requiring a reply — not feeds.'}_\n"

    body += """
## Health Defaults

- Do posture/neck reset before long computer sessions.
- Avoid opening Instagram/TikTok before the brief is reviewed.
- If sleep was bad, still do a tiny workout/walk rather than skipping the day.

## System Notes

- Daily Command Center spec: `wiki/personal/daily-command-center.md`
- Todo source: `data/lifeos/todos.json` (`wiki/personal/daily-todo.md` is generated readable view)
- This is intentionally incomplete until connectors are authenticated.
"""
    out_path.write_text(body, encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
