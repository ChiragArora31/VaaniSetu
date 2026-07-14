Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:BAIF_MODEL_PROFILE = if ($env:BAIF_MODEL_PROFILE) { $env:BAIF_MODEL_PROFILE } else { "balanced" }
$env:BAIF_ALLOW_MODEL_DOWNLOAD = "0"
py -m uvicorn app:app --host 0.0.0.0 --port 8501
