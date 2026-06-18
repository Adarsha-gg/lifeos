#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
DATA = ROOT / "data" / "lifeos"
TODO_JSON = DATA / "todos.json"
TODO_MD = ROOT / "wiki" / "personal" / "daily-todo.md"

SECTIONS = ("Today", "Soon", "Parking Lot")


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_id() -> str:
    return uuid.uuid4().hex[:10]


def load() -> dict[str, Any]:
    if not TODO_JSON.exists():
        return {"version": 1, "items": []}
    try:
        data = json.loads(TODO_JSON.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"version": 1, "items": []}
    except Exception:
        return {"version": 1, "items": []}


def save(data: dict[str, Any]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = TODO_JSON.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(TODO_JSON)
    export_markdown(data)


def parse_markdown() -> dict[str, Any]:
    section = "Today"
    items: list[dict[str, Any]] = []
    if not TODO_MD.exists():
        return {"version": 1, "items": items}
    for line in TODO_MD.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            if name in SECTIONS:
                section = name
            continue
        m = re.match(r"^- \[([ xX])\] (.+)$", line.strip())
        if not m:
            continue
        done = m.group(1).lower() == "x"
        items.append({
            "id": new_id(),
            "text": m.group(2).strip(),
            "section": section,
            "status": "done" if done else "open",
            "created_at": now(),
            "completed_at": now() if done else None,
        })
    return {"version": 1, "items": items}


def ensure() -> dict[str, Any]:
    if TODO_JSON.exists():
        return load()
    data = parse_markdown()
    save(data)
    return data


def export_markdown(data: dict[str, Any] | None = None) -> None:
    data = data or load()
    lines = [
        "---",
        "title: Daily Todo",
        "category: personal",
        "tags: [todo, lifeos, daily-brief]",
        "sources: []",
        "created: 2026-06-17",
        f"updated: {datetime.now().strftime('%Y-%m-%d')}",
        "---",
        "",
        "**Summary:** Generated readable view of `data/lifeos/todos.json`. Use the LifeOS dashboard as the source of truth for edits.",
        "",
    ]
    items = data.get("items", []) if isinstance(data, dict) else []
    for section in SECTIONS:
        lines += [f"## {section}", ""]
        section_items = [i for i in items if i.get("section") == section]
        if not section_items:
            lines.append("_No items._")
        else:
            for item in section_items:
                mark = "x" if item.get("status") == "done" else " "
                lines.append(f"- [{mark}] {item.get('text', '')}")
        lines.append("")
    lines += ["## See Also", "", "- [[personal/daily-command-center]]", "- [[personal/current-priorities]]", ""]
    TODO_MD.write_text("\n".join(lines), encoding="utf-8")


def open_items(limit: int | None = None) -> list[dict[str, Any]]:
    data = ensure()
    items = [i for i in data.get("items", []) if i.get("status") == "open"]
    order = {name: idx for idx, name in enumerate(SECTIONS)}
    items.sort(key=lambda i: (order.get(str(i.get("section")), 99), str(i.get("created_at") or "")))
    return items[:limit] if limit else items


def all_items() -> list[dict[str, Any]]:
    return list(ensure().get("items", []))


def add(text: str, section: str = "Today") -> dict[str, Any] | None:
    text = " ".join(text.strip().split())
    if not text:
        return None
    if section not in SECTIONS:
        section = "Today"
    data = ensure()
    item = {"id": new_id(), "text": text, "section": section, "status": "open", "created_at": now(), "completed_at": None}
    data.setdefault("items", []).append(item)
    save(data)
    return item


def complete(item_id: str) -> dict[str, Any] | None:
    data = ensure()
    for item in data.get("items", []):
        if item.get("id") == item_id and item.get("status") == "open":
            item["status"] = "done"
            item["completed_at"] = now()
            save(data)
            return item
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="LifeOS structured todos")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate", help="Create data/lifeos/todos.json from markdown if missing")
    sub.add_parser("list", help="List open todos as JSON")
    p = sub.add_parser("add", help="Add todo")
    p.add_argument("text")
    p.add_argument("--section", default="Today", choices=SECTIONS)
    p = sub.add_parser("complete", help="Complete todo by id")
    p.add_argument("id")
    args = parser.parse_args()
    if args.cmd == "migrate":
        print(json.dumps(ensure(), indent=2))
    elif args.cmd == "list":
        print(json.dumps(open_items(), indent=2))
    elif args.cmd == "add":
        print(json.dumps(add(args.text, args.section), indent=2))
    elif args.cmd == "complete":
        print(json.dumps(complete(args.id), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
