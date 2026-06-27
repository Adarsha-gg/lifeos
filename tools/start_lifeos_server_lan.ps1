# Starts the LifeOS server in LAN mode (reachable from your phone on the same Wi-Fi).
# Used by the "LifeOS Server (LAN)" scheduled task that runs at logon.
# Safe to run manually too. Keep to trusted home Wi-Fi.
$ErrorActionPreference = "Continue"
$repo = "C:\Users\adars\Coding\lifeos"
Set-Location $repo

# Don't double-start if something is already listening on 8787.
$listening = Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue
if ($listening) { Write-Host "LifeOS server already running on 8787"; exit 0 }

$env:LIFEOS_HOST = "0.0.0.0"          # expose on the LAN for the phone
$env:LIFEOS_SKIP_BOOT_REFRESH = "1"   # fast start; the 7am pipeline already refreshed content

$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = "python" }
Start-Process -WindowStyle Hidden -FilePath $py -ArgumentList "`"$repo\tools\lifeos_server.py`""
Write-Host "LifeOS server starting in LAN mode on http://0.0.0.0:8787  (phone: /learn)"
