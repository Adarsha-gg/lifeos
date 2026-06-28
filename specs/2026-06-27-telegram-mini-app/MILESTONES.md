# Milestones

## 2026-06-27 Local Mini App Plumbing

- Added `POST /api/progress` to `lifeos_server.py`.
  - Accepts JSON progress writes from the Telegram Mini App.
  - Validates Telegram `initData` with HMAC-SHA256 using `LIFEOS_TG_BOT_TOKEN`.
  - Enforces owner allowlist via `LIFEOS_TG_CHAT_ID` when present.
  - Writes server progress to `output/learn/progress.json`.
- Lesson pages now include Telegram's Mini App bridge script.
  - Plain browser path remains feature-detected and unaffected.
  - Telegram WebApp calls `ready()`, `expand()`, uses `MainButton`, and posts completion progress.
- `lifeos_morning_ping.py` now supports:
  - canonical `LIFEOS_TG_BOT_TOKEN` / `LIFEOS_TG_CHAT_ID`,
  - fallback aliases `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`,
  - `LIFEOS_PUBLIC_URL`,
  - inline `web_app` button when a public URL is configured,
  - LAN fallback URL in the message body.
- Added `tools/start_lifeos_tunnel.ps1`.
- Added `TUNNEL.md` with Cloudflare Tunnel setup and env documentation.

## Validation

- `python -m py_compile tools\lifeos_server.py tools\lifeos_lessons.py tools\lifeos_morning_ping.py`
- Generated lesson scripts parse after adding the Telegram bridge.
- Direct server helper validation rejects empty `initData`.
- Ping message includes `LIFEOS_PUBLIC_URL/learn?app=1` when configured.
- Full morning pipeline exited 0 with notification env vars cleared.

## Remaining External Setup

- A real Cloudflare Tunnel hostname must still be configured in the user's Cloudflare account.
- The running LifeOS server must be restarted to expose the newly added `/api/progress` route.
- End-to-end Telegram validation requires a real Mini App launch so Telegram provides valid `initData`.
