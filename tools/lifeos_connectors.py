#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from lifeos_archive import archive_summary
from lifeos_audit import log_event
from lifeos_events import events_summary
from lifeos_policy import policy_summary

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
OUT = ROOT / "output"
DEFAULT_EMAIL = os.environ.get("LIFEOS_GOOGLE_EMAIL", "adarshamishra33@gmail.com")
CRM_PATH = ROOT / "data" / "lifeos" / "crm.json"


def run(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def parse_json(text: str, fallback: Any) -> Any:
    try:
        return json.loads(text) if text else fallback
    except Exception:
        return fallback


def google_accounts(tool: str) -> list[str]:
    # gmcli supports JSON here; gccli 0.1.2 may not, so fall back to text.
    code, out, _ = run([tool, "accounts", "list", "--json"])
    data = parse_json(out, None)
    if isinstance(data, list):
        emails: list[str] = []
        for item in data:
            if isinstance(item, str):
                emails.append(item)
            elif isinstance(item, dict):
                emails.append(str(item.get("email") or item.get("account") or "").strip())
        return [e for e in emails if e]

    code, out, err = run([tool, "accounts", "list"])
    text = out or err
    if "No accounts configured" in text or code != 0:
        return []
    emails = []
    for token in text.replace(",", " ").split():
        if "@" in token and "." in token:
            emails.append(token.strip())
    return emails


def gmail_search(email: str, query: str, max_items: str = "6") -> list[dict[str, Any]]:
    code, out, _ = run(["gmcli", "--json", email, "search", query, "--max", max_items])
    if code != 0:
        return []
    data = parse_json(out, [])
    return data if isinstance(data, list) else []


def gmail_section(email: str) -> dict[str, Any]:
    accounts = google_accounts("gmcli")
    result: dict[str, Any] = {
        "configured": bool(accounts),
        "accounts": accounts,
        "email": email,
        "items": [],
        "categories": {},
        "error": "",
    }
    if not accounts:
        result["error"] = "Gmail not connected. Run gmcli account setup."
        return result
    email = email if email in accounts else accounts[0]
    categories = {
        "Priority Inbox": "in:inbox newer_than:14d (is:important OR is:starred OR is:unread)",
        "Needs Reply": "in:inbox newer_than:14d (is:unread OR label:important) -category:promotions -category:social",
        "LinkedIn Signals": "newer_than:14d (from:linkedin.com OR from:linkedin.com OR subject:(LinkedIn OR invitation OR message OR recruiter))",
        "Receipts / Security": "newer_than:14d (subject:(receipt OR invoice OR security OR verification OR alert) OR from:(no-reply OR noreply))",
    }
    result["email"] = email
    result["categories"] = {name: gmail_search(email, query, "6") for name, query in categories.items()}
    result["items"] = result["categories"].get("Priority Inbox", [])
    return result


def outlook_section() -> dict[str, Any]:
    token_paths = [
        Path.home() / ".lifeos" / "outlook-token.json",
        Path.home() / ".o365_token.txt",
    ]
    configured = any(p.exists() for p in token_paths) or bool(os.environ.get("LIFEOS_OUTLOOK_EMAIL"))
    result: dict[str, Any] = {
        "configured": configured,
        "provider": "outlook",
        "email": os.environ.get("LIFEOS_OUTLOOK_EMAIL", ""),
        "items": [],
        "categories": {
            "Priority Inbox": [],
            "Needs Reply": [],
            "Opportunities": [],
            "Receipts / Security": [],
        },
        "error": "Outlook not connected. Set up Microsoft Graph/O365 OAuth for LifeOS.",
    }
    if configured:
        result["error"] = "Outlook connector shell is ready; Microsoft Graph pull not authenticated/wired yet."
    return result


def email_command_center(gmail: dict[str, Any], outlook: dict[str, Any]) -> dict[str, Any]:
    categories: dict[str, list[dict[str, Any]]] = {}
    for provider, section in [("gmail", gmail), ("outlook", outlook)]:
        for name, items in (section.get("categories") or {}).items():
            bucket = categories.setdefault(name, [])
            for item in items or []:
                if isinstance(item, dict):
                    tagged = {**item, "provider": provider.upper()}
                else:
                    tagged = {"title": str(item), "provider": provider.upper()}
                bucket.append(tagged)
    configured = bool(gmail.get("configured") or outlook.get("configured"))
    return {
        "configured": configured,
        "providers": {
            "gmail": {"configured": gmail.get("configured"), "status": gmail.get("error") or gmail.get("status") or ""},
            "outlook": {"configured": outlook.get("configured"), "status": outlook.get("error") or outlook.get("status") or ""},
        },
        "categories": categories,
        "items": [item for items in categories.values() for item in items][:12],
        "status": "Unified Gmail + Outlook action inbox. No feed, only decisions.",
    }


def crm_section() -> dict[str, Any]:
    data = parse_json(CRM_PATH.read_text(encoding="utf-8") if CRM_PATH.exists() else "", {"people": []})
    people = data.get("people", []) if isinstance(data, dict) else []
    return {"configured": True, "items": people[:8], "status": f"{len(people)} relationship targets."}


def calendar_section(email: str) -> dict[str, Any]:
    accounts = google_accounts("gccli")
    result: dict[str, Any] = {"configured": bool(accounts), "accounts": accounts, "email": email, "items": [], "error": ""}
    if not accounts:
        result["error"] = "Calendar not connected. Run gccli account setup."
        return result
    email = email if email in accounts else accounts[0]
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=2)
    code, out, err = run([
        "gccli", email, "events", "primary",
        "--from", now.isoformat(), "--to", end.isoformat(), "--max", "10", "--json",
    ])
    if code != 0:
        result["error"] = err or out
        return result
    data = parse_json(out, [])
    result["email"] = email
    result["items"] = data if isinstance(data, list) else []
    return result


def action_queue_section() -> dict[str, Any]:
    path = OUT / "lifeos-actions.json"
    if not path.exists():
        return {"configured": True, "items": [], "status": "No staged actions."}
    data = parse_json(path.read_text(encoding="utf-8"), {"actions": []})
    actions = data.get("actions", []) if isinstance(data, dict) else []
    pending = [a for a in actions if isinstance(a, dict) and a.get("status") == "pending"]
    return {"configured": True, "items": pending[:8], "status": f"{len(pending)} pending action(s)."}


def github_section() -> dict[str, Any]:
    code, out, err = run(["gh", "auth", "status"])
    result: dict[str, Any] = {"configured": code == 0, "items": [], "categories": {}, "error": "" if code == 0 else (err or out)}
    if code != 0:
        return result

    categories: dict[str, list[dict[str, Any]]] = {}
    code, out, _ = run(["gh", "issue", "list", "--limit", "8", "--json", "title,url,repository,assignees,updatedAt"])
    categories["Assigned Issues"] = parse_json(out, []) if code == 0 else []

    code, out, _ = run(["gh", "pr", "list", "--search", "review-requested:@me", "--limit", "8", "--json", "title,url,repository,reviewDecision,updatedAt"])
    categories["PRs Needing Review"] = parse_json(out, []) if code == 0 else []

    code, out, _ = run(["gh", "run", "list", "--limit", "8", "--json", "name,status,conclusion,workflowName,url,updatedAt"])
    runs = parse_json(out, []) if code == 0 else []
    categories["Failed Workflows"] = [r for r in runs if isinstance(r, dict) and r.get("conclusion") in {"failure", "cancelled", "timed_out", "action_required"}]

    result["categories"] = categories
    result["items"] = categories["Assigned Issues"] + categories["PRs Needing Review"] + categories["Failed Workflows"]
    result["status"] = f"{sum(len(v) for v in categories.values())} GitHub signal(s)."
    return result


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    gmail = gmail_section(DEFAULT_EMAIL)
    outlook = outlook_section()
    email = email_command_center(gmail, outlook)
    calendar = calendar_section(DEFAULT_EMAIL)
    github = github_section()
    actions = action_queue_section()
    archive = archive_summary()
    crm = crm_section()
    events = events_summary()
    data = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "gmail": gmail,
        "outlook": outlook,
        "email": email,
        "calendar": calendar,
        "github": github,
        "actions": actions,
        "archive": archive,
        "crm": crm,
        "events": events,
        "policy": {"configured": True, "rules": policy_summary(), "status": "Read auto; drafts staged; send/post/delete/payment require approval."},
        "telegram": {"configured": True, "status": "Telegram bridge is active for this pi session; message history is not exported to dashboard yet."},
        "cursor": {"configured": False, "status": "Cursor Agent installed; run `agent login` to authenticate."},
        "gemini": {"configured": bool(os.environ.get("GEMINI_API_KEY")), "status": "Set GEMINI_API_KEY or Gemini settings to enable persistent workers."},
    }
    path = OUT / "lifeos-connectors.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    log_event(
        "connectors_refreshed",
        "lifeos_connectors",
        gmail_configured=gmail.get("configured"),
        outlook_configured=outlook.get("configured"),
        calendar_configured=calendar.get("configured"),
        github_configured=github.get("configured"),
        pending_actions=len(actions.get("items") or []),
        archive_records=archive.get("count", 0),
        events=len(events.get("items") or []),
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
