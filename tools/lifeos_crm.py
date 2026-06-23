#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
CRM = ROOT / "data" / "lifeos" / "crm.json"


def load() -> dict[str, Any]:
    return json.loads(CRM.read_text(encoding="utf-8")) if CRM.exists() else {"people": []}


def list_people(_: argparse.Namespace) -> int:
    for idx, person in enumerate(load().get("people", []), start=1):
        print(f"{idx}. {person.get('name')} [{person.get('tag')}] — {person.get('angle')}")
    return 0


def stage(args: argparse.Namespace) -> int:
    people = load().get("people", [])
    idx = args.index - 1
    if idx < 0 or idx >= len(people):
        print(f"person index out of range: {args.index}")
        return 1
    person = people[idx]
    payload = {
        "person": person.get("name"),
        "space": person.get("space"),
        "draft": person.get("draft"),
        "channel": args.channel,
    }
    cmd = [
        sys.executable,
        str(APP_ROOT / "tools" / "lifeos_actions.py"),
        "propose",
        "--source", "crm",
        "--action", f"draft_{args.channel}_outreach",
        "--title", f"Draft outreach to {person.get('name')}",
        "--purpose", "Build ERC-8004/networking relationship without sending automatically",
        "--risk-level", "medium",
        "--preview", person.get("draft", ""),
        "--created-by", "lifeos_crm",
        "--payload-json", json.dumps(payload),
    ]
    p = subprocess.run(cmd, cwd=APP_ROOT, text=True)
    return p.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="LifeOS people CRM utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list", help="List relationship targets")
    p.set_defaults(func=list_people)
    p = sub.add_parser("stage", help="Stage an outreach draft for approval")
    p.add_argument("index", type=int)
    p.add_argument("--channel", default="x", choices=["x", "linkedin", "email"])
    p.set_defaults(func=stage)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
