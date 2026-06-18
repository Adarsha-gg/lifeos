#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
DEFAULT_DIR = Path.home() / "AppData" / "Local" / "Temp" / "lifeos-research"
OUT = ROOT / "output" / "lifeos-reference-repos.json"


@dataclass(frozen=True)
class RefRepo:
    id: str
    name: str
    url: str
    license_policy: str


REPOS: list[RefRepo] = [
    RefRepo("S1", "mcp-personal-suite", "https://github.com/studiomeyer-io/mcp-personal-suite.git", "MIT: code reuse allowed with attribution"),
    RefRepo("S2", "PersonalDataHub", "https://github.com/AISmithLab/PersonalDataHub.git", "Apache-2.0: code reuse allowed with attribution"),
    RefRepo("S3", "mymcp", "https://github.com/Yassinello/mymcp.git", "AGPL-3.0: pattern only unless license accepted"),
    RefRepo("S4", "opentool", "https://github.com/Aditya251610/opentool.git", "MIT: code reuse allowed with attribution"),
    RefRepo("S5", "vadimgest", "https://github.com/VCasecnikovs/vadimgest.git", "inspect before reuse"),
    RefRepo("S6", "Clira", "https://github.com/Rushik-B/Clira.git", "MIT: code reuse allowed with attribution"),
    RefRepo("S7", "chief-of-staff", "https://github.com/ceaksan/chief-of-staff.git", "inspect before reuse"),
    RefRepo("S8a", "claude-chief-of-staff", "https://github.com/mimurchison/claude-chief-of-staff.git", "inspect before reuse"),
    RefRepo("S8b", "gary-ai", "https://github.com/matthewod11-stack/gary-ai.git", "inspect before reuse"),
    RefRepo("S9a", "froggo-mission-control", "https://github.com/ProfFroggo/froggo-mission-control.git", "inspect before reuse"),
    RefRepo("S9b", "ghost", "https://github.com/wcatz/ghost.git", "inspect before reuse"),
    RefRepo("S9c", "Thoth", "https://github.com/haraldh/Thoth.git", "inspect before reuse"),
    RefRepo("S9d", "mpa", "https://github.com/mattmezza/mpa.git", "inspect before reuse"),
    RefRepo("S9e", "jarvis", "https://github.com/boubakerwa/jarvis.git", "inspect before reuse"),
    RefRepo("S9f", "meepo", "https://github.com/leancoderkavy/meepo.git", "inspect before reuse"),
]


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def detect_license(path: Path) -> str:
    for name in ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]:
        p = path / name
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="ignore")[:1200].lower()
            if "gnu affero general public license" in text or "agpl" in text:
                return "AGPL"
            if "apache license" in text:
                return "Apache-2.0"
            if "mit license" in text or "permission is hereby granted" in text:
                return "MIT"
            if "sustainable use license" in text:
                return "Sustainable Use / fair-code"
            return p.read_text(encoding="utf-8", errors="ignore").splitlines()[0][:120]
    pkg = path / "package.json"
    if pkg.exists():
        try:
            return json.loads(pkg.read_text(encoding="utf-8")).get("license") or "package.json has no license"
        except Exception:
            pass
    return "UNKNOWN"


def update_repo(repo: RefRepo, base_dir: Path, fetch: bool) -> dict:
    path = base_dir / repo.name
    result = {**asdict(repo), "path": str(path), "ok": False, "commit": "", "detected_license": "", "error": ""}
    if path.exists() and (path / ".git").exists():
        if fetch:
            code, out, err = run(["git", "pull", "--ff-only"], cwd=path)
            if code != 0:
                result["error"] = err or out
        result["ok"] = True
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        code, out, err = run(["git", "clone", "--depth", "1", repo.url, str(path)], timeout=180)
        if code != 0:
            result["error"] = err or out
            return result
        result["ok"] = True

    code, out, err = run(["git", "rev-parse", "--short", "HEAD"], cwd=path)
    result["commit"] = out if code == 0 else ""
    result["detected_license"] = detect_license(path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Clone/update LifeOS reference repos and record license/commit map")
    parser.add_argument("--dir", default=str(DEFAULT_DIR), help="Reference clone directory")
    parser.add_argument("--no-fetch", action="store_true", help="Do not git pull existing clones")
    args = parser.parse_args()

    base_dir = Path(args.dir).expanduser()
    records = [update_repo(repo, base_dir, fetch=not args.no_fetch) for repo in REPOS]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"base_dir": str(base_dir), "repos": records}, indent=2), encoding="utf-8")

    for r in records:
        status = "OK" if r["ok"] else "ERR"
        print(f"{status} {r['id']:>3} {r['name']:<24} {r['commit']:<8} {r['detected_license'] or '-'}")
        if r["error"]:
            print(f"    {r['error'].splitlines()[0][:160]}")
    print(OUT)
    return 0 if all(r["ok"] for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
