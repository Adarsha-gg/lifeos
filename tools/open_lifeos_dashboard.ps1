$ErrorActionPreference = "Continue"
$repo = "C:/Users/adars/Coding/lifeos"
Set-Location $repo

# Start the local LifeOS server so dashboard buttons/forms actually work.
# If an older copied server owns the port, kill it and restart from this repo.
$portOwner = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8787 -ErrorAction SilentlyContinue | Select-Object -First 1
$needsStart = $true
if ($portOwner) {
  $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($portOwner.OwningProcess)" -ErrorAction SilentlyContinue
  if ($proc -and $proc.CommandLine -like "*$repo*lifeos_server.py*") {
    $needsStart = $false
  } else {
    try { Stop-Process -Id $portOwner.OwningProcess -Force } catch {}
    Start-Sleep -Seconds 1
  }
}
if ($needsStart) {
  Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "`"$repo\tools\lifeos_server.py`""
  Start-Sleep -Seconds 2
}

Start-Process "http://127.0.0.1:8787"
