#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from lifeos_audit import log_event
from lifeos_todos import all_items

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
DATA = ROOT / "data" / "lifeos"
ARCHIVE = DATA / "archive"
DB = DATA / "lifeos.sqlite"
OUT = ROOT / "output"
CONNECTORS = OUT / "lifeos-connectors.json"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_id(source: str, payload: Any) -> str:
    return hashlib.sha256(f"{source}:{canonical_json(payload)}".encode("utf-8")).hexdigest()[:20]


def read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback
    except Exception:
        return fallback


def todo_records() -> list[dict[str, Any]]:
    records = []
    for item in all_items():
        title = str(item.get("text") or "")
        raw = dict(item)
        records.append(record("daily_todo", stable_id("daily_todo", raw), title, title, raw=raw, tags=["todo", str(item.get("status") or "open")]))
    return records


def item_text(item: Any) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return str(item)
    return str(item.get("summary") or item.get("subject") or item.get("title") or item.get("name") or item.get("url") or item)


def connector_records() -> list[dict[str, Any]]:
    data = read_json(CONNECTORS, {})
    records: list[dict[str, Any]] = []
    for source in ["calendar", "github"]:
        section = data.get(source, {}) if isinstance(data, dict) else {}
        for item in section.get("items") or []:
            title = item_text(item)
            url = item.get("url") if isinstance(item, dict) else ""
            records.append(record(source, stable_id(source, item), title, title, url=url, raw=item))
    gmail = data.get("gmail", {}) if isinstance(data, dict) else {}
    categories = gmail.get("categories") or {}
    for category, items in categories.items():
        for item in items or []:
            title = item_text(item)
            raw = {"category": category, "item": item}
            records.append(record("gmail", stable_id("gmail", raw), title, title, raw=raw, tags=[category]))
    web_digest = data.get("web_digest", {}) if isinstance(data, dict) else {}
    for item in web_digest.get("items") or []:
        title = str(item.get("title") or item_text(item)) if isinstance(item, dict) else item_text(item)
        text = str(item.get("summary") or title) if isinstance(item, dict) else title
        url = item.get("url") if isinstance(item, dict) else ""
        tags = item.get("matched_keywords", []) if isinstance(item, dict) else []
        records.append(record("web_digest", stable_id("web_digest", item), title, text, url=url, raw=item, tags=tags))
    return records


def record(source: str, source_id: str, title: str, text: str, *, url: str = "", raw: Any = None, tags: Iterable[str] = ()) -> dict[str, Any]:
    return {
        "observed_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "source_id": source_id,
        "title": title,
        "text": text,
        "url": url or "",
        "tags": list(tags),
        "raw": raw if raw is not None else {},
    }


def existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            obj = json.loads(line)
            ids.add(str(obj.get("source_id")))
        except Exception:
            continue
    return ids


def append_records(records: list[dict[str, Any]]) -> dict[str, int]:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    by_source: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        by_source.setdefault(rec["source"], []).append(rec)
    added_by_source: dict[str, int] = {}
    for source, recs in by_source.items():
        path = ARCHIVE / f"{source}.jsonl"
        seen = existing_ids(path)
        added = 0
        with path.open("a", encoding="utf-8") as f:
            for rec in recs:
                if rec["source_id"] in seen:
                    continue
                f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
                seen.add(rec["source_id"])
                added += 1
        added_by_source[source] = added
    return added_by_source


def iter_archive_records() -> Iterable[dict[str, Any]]:
    if not ARCHIVE.exists():
        return
    for path in sorted(ARCHIVE.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    yield obj
            except Exception:
                continue


def rebuild_index() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS records (source TEXT NOT NULL, source_id TEXT NOT NULL, observed_at TEXT, title TEXT, text TEXT, url TEXT, raw_json TEXT, PRIMARY KEY(source, source_id))")
        con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(title, text, source, content='records', content_rowid='rowid')")
        con.execute("DELETE FROM records")
        con.execute("DELETE FROM records_fts")
        count = 0
        for rec in iter_archive_records() or []:
            cur = con.execute(
                "INSERT OR REPLACE INTO records(source, source_id, observed_at, title, text, url, raw_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (rec.get("source"), rec.get("source_id"), rec.get("observed_at"), rec.get("title"), rec.get("text"), rec.get("url"), canonical_json(rec.get("raw", {}))),
            )
            rowid = cur.lastrowid
            con.execute("INSERT INTO records_fts(rowid, title, text, source) VALUES (?, ?, ?, ?)", (rowid, rec.get("title", ""), rec.get("text", ""), rec.get("source", "")))
            count += 1
        con.commit()
        return count
    finally:
        con.close()


def archive_summary(limit: int = 8) -> dict[str, Any]:
    records = list(iter_archive_records() or [])
    counts: dict[str, int] = {}
    for rec in records:
        counts[rec.get("source", "unknown")] = counts.get(rec.get("source", "unknown"), 0) + 1
    recent = sorted(records, key=lambda r: r.get("observed_at", ""), reverse=True)[:limit]
    return {"configured": True, "count": len(records), "counts": counts, "items": recent, "status": f"{len(records)} archived record(s)."}


def search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    if not DB.exists():
        return []
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            "SELECT records.source, records.source_id, records.title, records.text, records.url FROM records_fts JOIN records ON records_fts.rowid = records.rowid WHERE records_fts MATCH ? LIMIT ?",
            (query, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def sync() -> dict[str, Any]:
    records = todo_records() + connector_records()
    added = append_records(records)
    indexed = rebuild_index()
    summary = archive_summary()
    log_event("archive_synced", "lifeos_archive", added=added, indexed=indexed, total=summary["count"])
    return {"added": added, "indexed": indexed, **summary}


def main() -> int:
    parser = argparse.ArgumentParser(description="LifeOS local append-only archive and SQLite FTS index")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync", help="Append new records from todos/connectors and rebuild SQLite FTS")
    sub.add_parser("summary", help="Print archive summary")
    p = sub.add_parser("search", help="Search local archive")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    if args.cmd == "sync":
        print(json.dumps(sync(), indent=2, sort_keys=True))
    elif args.cmd == "summary":
        print(json.dumps(archive_summary(), indent=2, sort_keys=True))
    elif args.cmd == "search":
        print(json.dumps(search(args.query, args.limit), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
