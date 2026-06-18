#!/usr/bin/env python3
from __future__ import annotations

import json
import socket
from datetime import datetime
from pathlib import Path
from typing import Any

from lifeos_paths import APP_ROOT, VAULT_ROOT

ROOT = VAULT_ROOT
OUT = ROOT / "output"
AUDIT_LOG = OUT / "lifeos-audit.jsonl"


def log_event(event: str, source: str, actor: str = "system", **details: Any) -> dict[str, Any]:
    """Append a JSONL audit event. Never raise into caller paths."""
    record = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "event": event,
        "source": source,
        "actor": actor,
        "host": socket.gethostname(),
        "details": details,
    }
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return record
