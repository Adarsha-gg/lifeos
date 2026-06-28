#!/usr/bin/env python3
"""Build the public static LifeOS Learn site for Vercel.

The normal LifeOS app reads/writes a private local vault. Vercel builds must not
need that vault, so this script uses ``public/`` as an isolated build vault,
regenerates public learning artifacts there, then mirrors ``output/learn`` to
``public/learn`` for the existing production URL shape.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

APP_ROOT = Path(__file__).resolve().parents[1]
PUBLIC = APP_ROOT / "public"
LEARN_OUT = PUBLIC / "output" / "learn"
LEARN_PUBLIC = PUBLIC / "learn"


def run(cmd: list[str], env: dict[str, str]) -> dict[str, Any]:
    print("$", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=APP_ROOT, env=env, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return {"cmd": cmd, "returncode": proc.returncode}


def write_review_page() -> None:
    (PUBLIC / "review.html").write_text(
        """<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>LifeOS Review</title><style>body{font-family:system-ui;margin:0;min-height:100vh;display:grid;place-items:center;background:#07100c;color:#eaffef}main{max-width:680px;padding:32px}a{color:#58d68d;font-weight:800}</style></head><body><main><h1>LifeOS Learn</h1><p>This public build is generated from the GitHub repository on every Vercel deployment.</p><p><a href=\"/learn\">Open the learning site →</a></p></main></body></html>""",
        encoding="utf-8",
    )


def main() -> int:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["LIFEOS_VAULT"] = str(PUBLIC)
    # Vercel builds should be deterministic and fast. Local builds can still
    # fetch/cache Wikimedia images by omitting this env var.
    env["LIFEOS_SKIP_LESSON_IMAGES"] = "1"

    commands = [
        [sys.executable, "tools/lifeos_paul_graham.py", "build", "--metadata-only", "--refresh", "--sleep", "0"],
        [sys.executable, "tools/lifeos_skill_tree.py", "build"],
        [sys.executable, "tools/lifeos_learning_engine.py", "build"],
        [sys.executable, "tools/lifeos_lessons.py", "build"],
    ]
    results = [run(cmd, env) for cmd in commands]

    if not LEARN_OUT.exists():
        raise SystemExit(f"missing generated learn output: {LEARN_OUT}")
    if LEARN_PUBLIC.exists():
        shutil.rmtree(LEARN_PUBLIC)
    shutil.copytree(LEARN_OUT, LEARN_PUBLIC)
    write_review_page()

    manifest = {
        "ok": True,
        "commands": results,
        "learn_files": sum(1 for p in LEARN_PUBLIC.rglob("*") if p.is_file()),
    }
    (PUBLIC / "vercel-build.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
