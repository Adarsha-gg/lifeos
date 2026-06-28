# LifeOS Telegram Mini App Tunnel

Telegram Mini Apps require a public HTTPS URL. LifeOS still serves locally on
`http://localhost:8787`; Cloudflare Tunnel forwards a public hostname to it.

## Required Env

Use these canonical variables:

```powershell
$env:LIFEOS_TG_BOT_TOKEN = "<telegram bot token>"
$env:LIFEOS_TG_CHAT_ID = "<your telegram user/chat id>"
$env:LIFEOS_PUBLIC_URL = "https://learn.your-domain.com"
```

`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` remain fallback aliases, but new
LifeOS code should use `LIFEOS_TG_*`.

## Named Tunnel Setup

Install and authenticate `cloudflared`, then create a named tunnel:

```powershell
cloudflared tunnel login
cloudflared tunnel create lifeos-learn
cloudflared tunnel route dns lifeos-learn learn.your-domain.com
```

Create `%USERPROFILE%\.cloudflared\lifeos.yml`:

```yaml
tunnel: lifeos-learn
credentials-file: C:\Users\adars\.cloudflared\<tunnel-id>.json

ingress:
  - hostname: learn.your-domain.com
    service: http://localhost:8787
  - service: http_status:404
```

Start the LifeOS server, then start the tunnel:

```powershell
python C:\Users\adars\Coding\lifeos\tools\lifeos_server.py
C:\Users\adars\Coding\lifeos\tools\start_lifeos_tunnel.ps1
```

For always-on use, register both as login tasks or Windows services.

## What Is Exposed

The public URL is intended for:

- `GET /learn`
- `GET /output/learn/*`
- `POST /api/progress`

`/api/progress` requires valid Telegram Mini App `initData`, validated with
`LIFEOS_TG_BOT_TOKEN`, and rejects missing or tampered data.

The server enforces this public surface by treating `LIFEOS_PUBLIC_URL`,
`Host`/`X-Forwarded-Host`, and Cloudflare headers as public-request signals.
Public requests are denied for `/`, `/dashboard`, `/m`, `/api/state`, `/wiki`,
`/data`, `/raw`, and non-HTML `/output/learn/*` files such as
`progress.json`.

Do not expose other write/control routes publicly without a separate access
control pass.
