#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from lifeos_paths import VAULT_ROOT

BASE = "http://127.0.0.1:8787"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def get(path: str) -> tuple[int, str]:
    try:
        r = urllib.request.urlopen(BASE + path, timeout=20)
        return r.status, r.read().decode("utf-8", errors="replace")
    except Exception as e:
        fail(f"GET {path}: {e}")


def post(path: str, data: dict[str, str]) -> int:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=20)
        r.read()
        return r.status
    except Exception as e:
        fail(f"POST {path}: {e}")


def backup(rel: str) -> tuple[Path, Path] | None:
    p = VAULT_ROOT / rel
    if not p.exists():
        return None
    b = Path.home() / "AppData" / "Local" / "Temp" / f"lifeos-doctor-{rel.replace('/', '_')}.bak"
    b.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, b)
    return p, b


def main() -> int:
    backups = [x for x in [
        backup("data/lifeos/todos.json"),
        backup("wiki/personal/daily-todo.md"),
        backup("wiki/personal/done-journal.md"),
        backup("raw/research/inbox.md"),
        backup("output/lifeos-actions.json"),
    ] if x]
    try:
        code, body = get("/health")
        if code != 200:
            fail(f"/health returned {code}: {body}")
        health = json.loads(body)
        if not health.get("ok"):
            fail(f"health checks failed: {health}")
        print("OK: health")

        code, html = get("/")
        if code != 200 or "/todo/complete" not in html:
            fail("dashboard did not render usable todo forms")
        print("OK: dashboard")

        if post("/todo/add", {"text": "LIFEOS DOCTOR TODO", "section": "Today"}) not in (200, 303):
            fail("todo add failed")
        todos = json.loads((VAULT_ROOT / "data/lifeos/todos.json").read_text(encoding="utf-8"))
        item = next(i for i in todos["items"] if i["text"] == "LIFEOS DOCTOR TODO")
        if post("/todo/complete", {"id": item["id"]}) not in (200, 303):
            fail("todo complete failed")
        todos = json.loads((VAULT_ROOT / "data/lifeos/todos.json").read_text(encoding="utf-8"))
        if next(i for i in todos["items"] if i["id"] == item["id"])["status"] != "done":
            fail("todo complete did not persist")
        print("OK: todo add/complete")

        if post("/research/capture", {"text": "https://example.com/lifeos-doctor", "kind": "source"}) not in (200, 303):
            fail("research capture failed")
        if "lifeos-doctor" not in (VAULT_ROOT / "raw/research/inbox.md").read_text(encoding="utf-8"):
            fail("research capture did not persist")
        print("OK: research capture")

        print("ALL LOCAL FUNCTIONS OK")
        return 0
    finally:
        for p, b in backups:
            shutil.copyfile(b, p)


if __name__ == "__main__":
    raise SystemExit(main())
