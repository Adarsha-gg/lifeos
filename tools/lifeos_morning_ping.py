#!/usr/bin/env python3
"""Send a morning 'lessons are ready' ping to the user's phone.

Runs as part of the morning pipeline, right after lessons are built. Reads the
lesson manifest and pushes a short message with the /learn link. Supports two
channels — configure whichever you like (both work; it sends to any configured):

  Telegram:  set env LIFEOS_TG_BOT_TOKEN and LIFEOS_TG_CHAT_ID
             (make a bot via @BotFather, then get your chat id)
  ntfy.sh:   set env LIFEOS_NTFY_TOPIC  (install the ntfy app, subscribe to the
             same topic — zero account needed)

If nothing is configured it prints setup hints and exits 0 (never fails the
pipeline).
"""
from __future__ import annotations

import json
import os
import socket
import urllib.parse
import urllib.request
from pathlib import Path

from lifeos_paths import VAULT_ROOT

MANIFEST = VAULT_ROOT / "output" / "learn" / "today.json"
PORT = 8787


def lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def load_manifest() -> dict:
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_message() -> tuple[str, str]:
    m = load_manifest()
    url = f"http://{lan_ip()}:{PORT}/learn"
    titles = [f"{l.get('emoji','•')} {l.get('title','')}" for l in m.get("lessons", [])]
    body_lines = ["🌅 Your LifeOS morning lessons are ready —", *titles, "", f"Open: {url}",
                  "(read one instead of scrolling)"]
    return "LifeOS morning lessons", "\n".join(body_lines)


def send_telegram(title: str, body: str) -> str | None:
    token = os.environ.get("LIFEOS_TG_BOT_TOKEN", "").strip()
    chat = os.environ.get("LIFEOS_TG_CHAT_ID", "").strip()
    if not token or not chat:
        return None
    data = urllib.parse.urlencode({
        "chat_id": chat, "text": body, "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage", data=data,
        headers={"User-Agent": "LifeOS/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        ok = json.loads(resp.read()).get("ok")
        return "telegram: sent" if ok else "telegram: api returned not-ok"


def send_ntfy(title: str, body: str) -> str | None:
    topic = os.environ.get("LIFEOS_NTFY_TOPIC", "").strip()
    if not topic:
        return None
    req = urllib.request.Request(
        f"https://ntfy.sh/{urllib.parse.quote(topic)}", data=body.encode("utf-8"),
        headers={"Title": title, "Tags": "sunrise,books", "User-Agent": "LifeOS/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return "ntfy: sent" if resp.status < 300 else f"ntfy: status {resp.status}"


def main() -> int:
    title, body = build_message()
    sent = []
    for sender in (send_telegram, send_ntfy):
        try:
            result = sender(title, body)
            if result:
                sent.append(result)
        except Exception as exc:  # never break the morning pipeline over a ping
            sent.append(f"{sender.__name__}: error {exc}")
    if sent:
        print("; ".join(sent))
    else:
        print("morning ping: no channel configured (skipped). "
              "Set LIFEOS_TG_BOT_TOKEN+LIFEOS_TG_CHAT_ID for Telegram, "
              "or LIFEOS_NTFY_TOPIC for ntfy.sh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
