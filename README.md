# LifeOS

Local-first personal command center app for Adar.

This repo contains the app/tools. The personal vault stays separate at:

```text
C:\Users\adars\adarsha-knowledge-base
```

By default scripts read/write that vault. Override with:

```powershell
$env:LIFEOS_VAULT = "C:\path\to\vault"
```

## Run

```powershell
python tools/lifeos_server.py
```

Open:

```text
http://127.0.0.1:8787
```

Desktop launcher:

```powershell
powershell -ExecutionPolicy Bypass -File tools\open_lifeos_dashboard.ps1
```

Phone/LAN helper:

```powershell
powershell -ExecutionPolicy Bypass -File tools\open_lifeos_phone.ps1
```

Do not expose port `8787` publicly. Use Tailscale for remote phone access.
