# Starts the MuleTrail backend (:8000) and frontend (:5173). Ctrl+C stops both.
# First run creates backend\.venv and installs dependencies (needs internet once).
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvPy = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPy)) {
    Write-Host "Creating backend virtualenv (Python 3.11)..."
    py -3.11 -m venv (Join-Path $backend ".venv")
    & $venvPy -m pip install -q -r (Join-Path $backend "requirements.txt")
}
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $frontend; npm install; Pop-Location
}

# Build (or load) the precompute cache before serving, so the first request is fast.
Push-Location $backend
& $venvPy -m app.precompute
Pop-Location

$api = Start-Process -FilePath $venvPy -WorkingDirectory $backend `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" `
    -PassThru -NoNewWindow
$web = Start-Process -FilePath "npm.cmd" -WorkingDirectory $frontend `
    -ArgumentList "run", "dev", "--", "--host", "127.0.0.1" `
    -PassThru -NoNewWindow

Write-Host ""
Write-Host "MuleTrail is starting:  http://127.0.0.1:5173   (API: http://127.0.0.1:8000/health)"
Write-Host "Press Ctrl+C to stop both."

try {
    while (-not $api.HasExited -and -not $web.HasExited) { Start-Sleep -Seconds 1 }
}
finally {
    foreach ($p in @($api, $web)) {
        if ($p -and -not $p.HasExited) { & taskkill /PID $p.Id /T /F | Out-Null }
    }
}
