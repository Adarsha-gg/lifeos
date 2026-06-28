param(
  [string]$Config = "$env:USERPROFILE\.cloudflared\lifeos.yml"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
  Write-Error "cloudflared is not installed or not on PATH. Install it, then run this script again."
}

if (-not (Test-Path -LiteralPath $Config)) {
  Write-Host "Missing tunnel config: $Config"
  Write-Host "Create a named Cloudflare Tunnel config that maps your hostname to http://localhost:8787."
  Write-Host "See specs\2026-06-27-telegram-mini-app\TUNNEL.md"
  exit 1
}

Write-Host "Starting LifeOS Cloudflare Tunnel using $Config"
cloudflared tunnel --config $Config run
