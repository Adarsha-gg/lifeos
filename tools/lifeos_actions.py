#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from lifeos_audit import log_event
from lifeos_policy import classify_action

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
OUT = ROOT / "output"
QUEUE = OUT / "lifeos-actions.json"
SCHEMA_VERSION = 2


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def snapshot_hash(snapshot: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(snapshot).encode("utf-8")).hexdigest()


def load() -> dict[str, Any]:
    if not QUEUE.exists():
        return {"actions": []}
    try:
        data = json.loads(QUEUE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"actions": []}
    except Exception:
        return {"actions": []}


def save(data: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = QUEUE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(QUEUE)


def propose(args: argparse.Namespace) -> int:
    data = load()
    payload = json.loads(args.payload_json) if args.payload_json else {}
    now = datetime.now().isoformat(timespec="seconds")
    action_snapshot = {
        "source": args.source,
        "action": args.action,
        "title": args.title,
        "purpose": args.purpose,
        "risk_level": args.risk_level,
        "preview": args.preview or args.title,
        "payload": payload,
    }
    policy = classify_action(args.action)
    action = {
        "schema_version": SCHEMA_VERSION,
        "id": str(uuid.uuid4())[:8],
        "created_at": now,
        "created_by": args.created_by,
        "status": "pending",
        "action_snapshot": action_snapshot,
        "snapshot_hash": snapshot_hash(action_snapshot),
        # Back-compat fields for older dashboard/readers.
        "source": args.source,
        "action": args.action,
        "title": args.title,
        "purpose": args.purpose,
        "risk_level": args.risk_level,
        "preview": args.preview or args.title,
        "payload": payload,
        "policy": policy.default_handling,
        "approval_required": policy.approval_required,
    }
    data.setdefault("actions", []).append(action)
    save(data)
    log_event(
        "action_staged",
        args.source,
        actor=args.created_by,
        action_id=action["id"],
        action=args.action,
        risk_level=args.risk_level,
        approval_required=policy.approval_required,
        snapshot_hash=action["snapshot_hash"],
    )
    print(json.dumps(action, indent=2))
    return 0


def update_status(action_id: str, status: str, decided_by: str = "pi") -> int:
    data = load()
    now = datetime.now().isoformat(timespec="seconds")
    for action in data.get("actions", []):
        if action.get("id") == action_id:
            if action.get("status") != "pending":
                print(f"action {action_id} is already {action.get('status')}")
                return 2
            snapshot = action.get("action_snapshot")
            if isinstance(snapshot, dict) and action.get("snapshot_hash") != snapshot_hash(snapshot):
                print(f"action {action_id} snapshot hash mismatch; refusing decision")
                return 3
            action["status"] = status
            action["updated_at"] = now
            action["decided_by"] = decided_by
            if status == "approved":
                action["approved_at"] = now
            elif status == "rejected":
                action["rejected_at"] = now
            save(data)
            log_event(
                f"action_{status}",
                str(action.get("source") or "actions"),
                actor=decided_by,
                action_id=action_id,
                action=action.get("action"),
                snapshot_hash=action.get("snapshot_hash"),
            )
            print(json.dumps(action, indent=2))
            return 0
    print(f"action not found: {action_id}")
    return 1


def list_actions(args: argparse.Namespace) -> int:
    data = load()
    actions = data.get("actions", [])
    if args.status != "all":
        actions = [a for a in actions if a.get("status") == args.status]
    print(json.dumps(actions, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="LifeOS staged action queue")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("propose", help="Stage an action for human approval")
    p.add_argument("--source", required=True, help="gmail, calendar, github, social, etc.")
    p.add_argument("--action", required=True, help="send_email, create_event, reply_dm, etc.")
    p.add_argument("--title", required=True, help="Human-readable action title")
    p.add_argument("--purpose", default="Not specified", help="Why this action is needed; shown in audit/approval UI")
    p.add_argument("--risk-level", default="medium", choices=["low", "medium", "high", "critical"], help="Risk level for human review")
    p.add_argument("--preview", default="", help="Human-readable preview of exactly what would happen")
    p.add_argument("--created-by", default="pi", help="Actor that proposed the action")
    p.add_argument("--payload-json", default="{}", help="JSON payload; not executed by this tool")
    p.set_defaults(func=propose)

    p = sub.add_parser("list", help="List staged actions")
    p.add_argument("--status", default="pending", choices=["pending", "approved", "rejected", "all"])
    p.set_defaults(func=list_actions)

    p = sub.add_parser("approve", help="Mark an action approved")
    p.add_argument("id")
    p.add_argument("--decided-by", default="pi")
    p.set_defaults(func=lambda a: update_status(a.id, "approved", a.decided_by))

    p = sub.add_parser("reject", help="Mark an action rejected")
    p.add_argument("id")
    p.add_argument("--decided-by", default="pi")
    p.set_defaults(func=lambda a: update_status(a.id, "rejected", a.decided_by))

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
