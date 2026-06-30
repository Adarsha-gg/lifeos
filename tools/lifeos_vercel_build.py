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
HUB_SRC = APP_ROOT / "lifeos-hub"
HUB_DIST = HUB_SRC / "dist"
HUB_PUBLIC = PUBLIC / "hub"


def run(cmd: list[str], env: dict[str, str], cwd: Path = APP_ROOT) -> dict[str, Any]:
    print("$", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=cwd, env=env, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return {"cmd": cmd, "returncode": proc.returncode}


def write_hub_fallback() -> None:
    """If the hub can't be built, keep `/hub` working as a redirect to /learn."""
    HUB_PUBLIC.mkdir(parents=True, exist_ok=True)
    (HUB_PUBLIC / "index.html").write_text(
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta http-equiv=\"refresh\" content=\"0; url=/learn\">"
        "<title>LifeOS Quest Hub</title></head>"
        "<body><a href=\"/learn\">Open LifeOS Learn →</a></body></html>",
        encoding="utf-8",
    )


def build_hub(env: dict[str, str]) -> dict[str, Any]:
    """Build the single-page Quest Hub (React + lifeos-ds) into public/hub.

    The hub is a static Vite build. If npm or the build is unavailable in this
    environment, fall back to a redirect page so the deploy never breaks.
    """
    npm = shutil.which("npm")
    if not npm or not HUB_SRC.exists():
        print("! npm or lifeos-hub missing — writing hub fallback", flush=True)
        write_hub_fallback()
        return {"hub": "skipped"}
    try:
        run([npm, "install", "--no-audit", "--no-fund"], env, cwd=HUB_SRC)
        run([npm, "run", "build"], env, cwd=HUB_SRC)
    except SystemExit:
        print("! hub build failed — writing fallback", flush=True)
        write_hub_fallback()
        return {"hub": "build-failed"}
    if not HUB_DIST.exists():
        write_hub_fallback()
        return {"hub": "no-dist"}
    if HUB_PUBLIC.exists():
        shutil.rmtree(HUB_PUBLIC)
    shutil.copytree(HUB_DIST, HUB_PUBLIC)
    return {"hub": "built", "files": sum(1 for p in HUB_PUBLIC.rglob("*") if p.is_file())}


def write_review_page() -> None:
    (PUBLIC / "review.html").write_text(
        """<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>LifeOS Review</title><style>body{font-family:system-ui;margin:0;min-height:100vh;display:grid;place-items:center;background:#07100c;color:#eaffef}main{max-width:680px;padding:32px}a{color:#58d68d;font-weight:800}</style></head><body><main><h1>LifeOS Quest Hub</h1><p>This public build is generated from the GitHub repository on every Vercel deployment.</p><p><a href=\"/hub\">Open the Quest Hub →</a></p></main></body></html>""",
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
        [sys.executable, "tools/lifeos_paul_graham.py", "build", "--refresh", "--sleep", "0"],
        [sys.executable, "tools/lifeos_games.py", "build"],
        [sys.executable, "tools/lifeos_arcade.py", "build"],
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
    hub = build_hub(env)

    manifest = {
        "ok": True,
        "commands": results,
        "learn_files": sum(1 for p in LEARN_PUBLIC.rglob("*") if p.is_file()),
        "hub": hub,
    }
    (PUBLIC / "vercel-build.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
