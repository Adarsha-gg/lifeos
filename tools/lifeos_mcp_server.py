#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from lifeos_audit import log_event

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT


def run(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=APP_ROOT, text=True, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def text_content(text: str) -> list[dict[str, str]]:
    return [{"type": "text", "text": text}]


def tool_defs() -> list[dict[str, Any]]:
    return [
        {
            "name": "lifeos_daily_brief",
            "description": "Regenerate the local LifeOS daily brief and return the report path.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "lifeos_search_archive",
            "description": "Search the local LifeOS SQLite FTS archive.",
            "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]},
        },
        {
            "name": "lifeos_stage_action",
            "description": "Stage a LifeOS action for human approval. Does not execute the action.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "action": {"type": "string"},
                    "title": {"type": "string"},
                    "purpose": {"type": "string"},
                    "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "preview": {"type": "string"},
                    "payload": {"type": "object"},
                },
                "required": ["source", "action", "title", "purpose"],
            },
        },
        {
            "name": "lifeos_list_pending_actions",
            "description": "List pending LifeOS staged actions awaiting approval.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    ]


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    log_event("mcp_tool_called", "lifeos_mcp", tool=name)
    if name == "lifeos_daily_brief":
        code, out, err = run([sys.executable, "tools/daily_brief.py"])
        return {"content": text_content(out or err), "isError": code != 0}
    if name == "lifeos_search_archive":
        query = str(args.get("query", ""))
        limit = str(int(args.get("limit", 10)))
        code, out, err = run([sys.executable, "tools/lifeos_archive.py", "search", query, "--limit", limit])
        return {"content": text_content(out or err), "isError": code != 0}
    if name == "lifeos_stage_action":
        payload = json.dumps(args.get("payload") or {})
        cmd = [
            sys.executable,
            "tools/lifeos_actions.py",
            "propose",
            "--source", str(args.get("source", "mcp")),
            "--action", str(args.get("action", "unknown")),
            "--title", str(args.get("title", "Untitled action")),
            "--purpose", str(args.get("purpose", "MCP staged action")),
            "--risk-level", str(args.get("risk_level", "medium")),
            "--preview", str(args.get("preview", args.get("title", ""))),
            "--created-by", "lifeos_mcp",
            "--payload-json", payload,
        ]
        code, out, err = run(cmd)
        return {"content": text_content(out or err), "isError": code != 0}
    if name == "lifeos_list_pending_actions":
        code, out, err = run([sys.executable, "tools/lifeos_actions.py", "list"])
        return {"content": text_content(out or err), "isError": code != 0}
    return {"content": text_content(f"unknown tool: {name}"), "isError": True}


def response(msg_id: Any, result: Any = None, error: Any = None) -> dict[str, Any]:
    msg = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    return msg


def handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    method = msg.get("method")
    msg_id = msg.get("id")
    if method == "initialize":
        return response(msg_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "lifeos", "version": "0.1.0"}})
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return response(msg_id, {"tools": tool_defs()})
    if method == "tools/call":
        params = msg.get("params") or {}
        return response(msg_id, call_tool(str(params.get("name")), params.get("arguments") or {}))
    return response(msg_id, error={"code": -32601, "message": f"method not found: {method}"})


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            resp = handle(msg)
        except Exception as exc:
            resp = response(None, error={"code": -32603, "message": str(exc)})
        if resp is not None:
            print(json.dumps(resp, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
