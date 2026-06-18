#!/usr/bin/env python3
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from lifeos_todos import open_items

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
WIKI = ROOT / "wiki"
OUT = ROOT / "output" / "reports"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


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

    body += """
## Calendar

_Not connected yet._ Choose and authenticate a read-only calendar connector.

## Important Email

_Not connected yet._ Add a read-only email connector and an importance filter before surfacing email here.

## Social / Texts

_Not connected yet._ Keep this action-only: DMs, mentions, and messages requiring a reply — not feeds.

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
