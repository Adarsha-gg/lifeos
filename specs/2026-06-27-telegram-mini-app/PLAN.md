# BUILD SPEC — Phase 2: Telegram Mini App delivery

**Status:** Ready to build (depends on Phase 1 generation, which is DONE)
**Estimated size:** 1 tunnel setup + 1 Mini App page variant + 1 server endpoint + bot receive path + ping wiring
**Goal:** Turn the morning lessons from "a text ping with a LAN URL you open in a browser on the same Wi-Fi" into a real **Telegram Mini App**: tap a button in Telegram → a full interactive lesson+game opens inside Telegram → finishing the game sends results back so the knowledge graph updates. Works anywhere, not just home Wi-Fi.

Read `specs/2026-06-27-ai-content-generation/PLAN.md` first for system context.

---

## 1. Current state (verified)

- **Content generation:** DONE (Phase 1). `lifeos_generate.py` produces lessons + games into `output/learn/`, rendered as HTML pages by `lifeos_lessons.py`.
- **Local web server:** `tools/lifeos_server.py` serves the learn pages. `lifeos_morning_ping.py` builds a URL `http://<LAN-IP>:8787/learn` (PORT 8787, routes `/learn`, `/m`, static `/output/learn/*`). **CONFIRM exact port + routes in `lifeos_server.py` before building.**
- **Delivery today:** `lifeos_morning_ping.py` sends a plain `sendMessage` with that LAN URL. Phone must be on the same network. No interactivity returns to the system.
- **Telegram receive path:** `telegram-workflow/Telegram-Workflow-Bot.ps1` is a long-poll bot (`getUpdates` + offset, single-chat allowlist) that **only handles `message.text`** — it does not handle `web_app_data`. Progress today lives only in browser `localStorage` (`lifeos.learning.progress.v1`).
- **⚠️ Token env mismatch to reconcile:** `morning_ping.py` reads `LIFEOS_TG_BOT_TOKEN` / `LIFEOS_TG_CHAT_ID`; the PS bot reads `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`. Pick one canonical pair (recommend `LIFEOS_TG_*`) and make both use it, or document the mapping. Don't leave two.

---

## 2. Hard constraints from Telegram (read before designing)

1. **Mini Apps must load over HTTPS** from a public URL. They cannot open a `file://` or a bare LAN IP. → We need a tunnel.
2. **Two ways results can return from a Mini App:**
   - `Telegram.WebApp.sendData(string)` — **only works when the Mini App was opened from a reply-keyboard `KeyboardButton` with `web_app`.** It sends a service message `web_app_data` to the bot and closes the app. Cannot be used for menu-button / inline-button launches.
   - **POST to your own backend**, authenticating with `Telegram.WebApp.initData` (validated server-side via HMAC-SHA256 using the bot token). Works for any launch method, supports two-way, and lets the app stay open. **This is the recommended path** since we already run a server.
3. `initData` validation is mandatory for trust: never accept progress writes without verifying the `hash` field against the bot token per Telegram's documented algorithm.

---

## 3. Architecture (recommended)

```
Telegram app (phone)
   │  taps "Open today's lessons" (inline web_app button in the morning ping)
   ▼
Mini App page  (HTTPS via Cloudflare Tunnel)  ──►  lifeos_server.py  :8787
   │  loads telegram-web-app.js, renders lesson + game (existing HTML, themed)
   │
   │  on game completion:
   ▼
POST https://<tunnel>/api/progress   { lesson_id, score, initData }
   │  server validates initData HMAC, then writes progress store
   ▼
output/learn/progress.json  (server-side personal model)  ──► graph + recommender read it
```

Cloudflare Tunnel (`cloudflared`) gives a **stable named HTTPS URL** → `localhost:8787`, free, no inbound ports opened on the router. (ngrok works too but free URLs rotate; prefer a named cloudflared tunnel.)

---

## 4. Components to build

### 4.1 HTTPS tunnel
- Install `cloudflared`. Create a **named tunnel** with a stable hostname (a Cloudflare account + a domain, or use a quick tunnel for testing with the understanding the URL rotates).
- Config file mapping the hostname → `http://localhost:8787`.
- Run it as a background service / Windows Task at login so it's up when the morning pipeline fires.
- Deliverable: `tools/start_lifeos_tunnel.ps1` + a short `specs/.../TUNNEL.md` with the setup steps and where the public URL is stored (e.g. env `LIFEOS_PUBLIC_URL`).

### 4.2 Mini App page
- Add a Mini-App-aware render mode. Easiest: a query flag (e.g. `/learn?app=1` or a dedicated `/app/<lesson_id>` route) that injects:
  - `<script src="https://telegram.org/js/telegram-web-app.js"></script>`
  - On load: `Telegram.WebApp.ready(); Telegram.WebApp.expand();` apply `themeParams` (use Telegram's dark/light variables so it matches the user's Telegram theme).
  - Haptics on game interactions (`Telegram.WebApp.HapticFeedback`).
  - The existing lesson + game UI, unchanged in substance.
  - A "Lock this into your graph" action that, on game completion, calls §4.3 (POST results) and shows a success state. Use `Telegram.WebApp.MainButton` for the primary action.
- Keep the page usable as a plain web page too (feature-detect `window.Telegram?.WebApp`), so the LAN/browser path keeps working.
- Do this as a small layer over `lifeos_lessons.py` rendering — do NOT fork the whole renderer.

### 4.3 Server endpoint: `POST /api/progress` (edit `lifeos_server.py`)
- Accept JSON `{ lesson_id, node_id, score, result, initData }`.
- **Validate `initData`** (HMAC-SHA256 per Telegram spec, key derived from the bot token). Reject if invalid or if the Telegram user id isn't the allowlisted owner. Use stdlib `hmac`/`hashlib`.
- On success: upsert into `output/learn/progress.json` — `{ done: {node_id: {at, xp, score}}, reviews: {...} }`, mirroring the localStorage shape so the graph/recommender can read either source.
- Return `{ ok, xp, level }` so the Mini App can show the reward.
- Keep the rest of the server read-only; this is the only write route. Don't expose other write actions through the tunnel.

### 4.4 Bot receive path (only if you also support `sendData`)
- If you implement the `sendData` fallback, extend a single canonical bot to handle `update.message.web_app_data.data` → parse JSON → same upsert as §4.3. Recommend extending the existing PS long-poll bot OR (preferred for consistency with Phase 1) a small Python long-poll receiver `tools/lifeos_telegram_bot.py` using stdlib `urllib`. **Pick one bot; don't run two on the same token** (getUpdates conflicts).

### 4.5 Morning ping wiring (edit `lifeos_morning_ping.py`)
- Replace the bare LAN URL with an **inline keyboard** message: a `web_app` button per lesson (or one "Open today's lessons" button) pointing at `${LIFEOS_PUBLIC_URL}/learn?app=1`.
- Keep the LAN URL as a fallback line for when the tunnel is down.
- Still never crash the pipeline (match existing try/except behavior).

---

## 5. Personal model: localStorage → server (design note)
Phase 1's personal graph is browser `localStorage`. The Mini App runs in Telegram's webview, where localStorage is fragile and not shared with your desktop browser. Moving the source of truth to **server-side `progress.json`** (§4.3) is the right call — it unifies progress across phone + desktop and sets up future multi-device. Keep localStorage as a client cache that syncs to the server on load/complete. The graph + recommender should read server progress when present, falling back to localStorage.

---

## 6. Security
- Validate `initData` on every write. No exceptions.
- Allowlist the owner's Telegram user id (you already single-chat-gate in the PS bot).
- Tunnel exposes only `/learn`, `/output/learn/*` (read) and `/api/progress` (write). Audit `lifeos_server.py` routes so nothing sensitive (connectors, dashboard control `/m`, action queue) is reachable through the public hostname — ideally a separate restricted route prefix for the tunnel.

---

## 7. Acceptance criteria
1. `cloudflared` serves the LifeOS learn page over HTTPS at a stable URL → opens in a normal browser.
2. From Telegram on a phone **not on home Wi-Fi**, tapping the morning ping's button opens the lesson inside Telegram, themed to match Telegram, expanded full-height.
3. Completing the game POSTs results; server validates `initData` (a tampered/absent `initData` is rejected with 401/403).
4. After completion, `output/learn/progress.json` reflects the node as done with score; re-opening the graph shows that node learned (XP/level updated).
5. The same page still works as a plain browser page (LAN fallback) with no JS errors when `Telegram.WebApp` is absent.
6. Only one bot runs against the token; no `getUpdates` 409 conflicts.
7. Token env vars reconciled to a single canonical pair, documented.

---

## 8. Risks / notes
- **Tunnel uptime** is now a dependency for phone delivery. Mitigate: named tunnel as a login service; ping falls back to LAN URL with a note if `LIFEOS_PUBLIC_URL` is unreachable.
- **`sendData` vs POST** confusion is the most common Mini App bug — we use POST+initData as primary specifically to avoid the keyboard-button-only limitation. Don't mix.
- **initData validation** must follow Telegram's exact algorithm (sorted key=value lines joined by `\n`, secret key = HMAC(bot_token, "WebAppData")). Test against a known-good sample.
- Keep generated lesson pages self-contained (they already are) so they load fast over the tunnel.
