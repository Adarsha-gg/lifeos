$ErrorActionPreference = "Continue"
$repo = "C:/Users/adars/Coding/lifeos"
Set-Location $repo

# Start the local LifeOS server so dashboard buttons/forms actually work.
$portInUse = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8787 -ErrorAction SilentlyContinue
if (-not $portInUse) {
  Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "`"$repo\tools\lifeos_server.py`""
  Start-Sleep -Seconds 2
}

Start-Process "http://127.0.0.1:8787"
