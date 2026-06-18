$ErrorActionPreference = "Continue"
$repo = "C:/Users/adars/Coding/lifeos"
Set-Location $repo

# LAN mode: exposes LifeOS to devices on the same Wi-Fi.
# Keep this on trusted home Wi-Fi only.
$existing = Get-NetTCPConnection -LocalPort 8787 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existing) {
  try { Stop-Process -Id $existing.OwningProcess -Force } catch {}
  Start-Sleep -Seconds 1
}

Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "`"$repo\tools\lifeos_server.py`"" -Environment @{ LIFEOS_HOST = "0.0.0.0" }
Start-Sleep -Seconds 2

$ip = (Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } |
  Select-Object -First 1 -ExpandProperty IPAddress)

if (-not $ip) { $ip = "127.0.0.1" }
$url = "http://$ip`:8787"
Set-Clipboard $url
Start-Process "http://127.0.0.1:8787/phone"
Write-Host "LifeOS phone URL copied to clipboard: $url"
