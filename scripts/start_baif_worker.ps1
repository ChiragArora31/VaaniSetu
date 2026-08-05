Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:BAIF_MODEL_PROFILE = if ($env:BAIF_MODEL_PROFILE) { $env:BAIF_MODEL_PROFILE } else { "balanced" }
$env:BAIF_ALLOW_MODEL_DOWNLOAD = "0"
$VenvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    throw "VaaniSetu is not set up yet. Run .\scripts\setup_baif_worker.ps1 once, then start again."
}
& $VenvPython scripts\operations.py migrate
if ($LASTEXITCODE -ne 0) { throw "VaaniSetu could not prepare its local data. See the message above." }
Write-Host "VaaniSetu is starting at http://127.0.0.1:8501"
Write-Host "Keep this window open while VaaniSetu is in use. Press Ctrl+C to stop it safely."
& $VenvPython -m uvicorn app:app --host 0.0.0.0 --port 8501
