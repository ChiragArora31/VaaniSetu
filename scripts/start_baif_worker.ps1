param(
    [ValidateSet("127.0.0.1", "0.0.0.0")]
    [string]$HostAddress = "127.0.0.1",
    [ValidateRange(1024, 65535)]
    [int]$Port = 8501
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:BAIF_MODEL_PROFILE = if ($env:BAIF_MODEL_PROFILE) { $env:BAIF_MODEL_PROFILE } else { "balanced" }
$env:BAIF_ALLOW_MODEL_DOWNLOAD = "0"
$env:BAIF_WHISPER_DEVICE = "cpu"
$env:BAIF_WHISPER_COMPUTE_TYPE = "int8"
$EspeakCommand = Get-Command espeak-ng -ErrorAction SilentlyContinue
if (-not $env:BAIF_ESPEAK_BINARY -and $EspeakCommand) {
    $env:BAIF_ESPEAK_BINARY = $EspeakCommand.Source
}
if (-not $env:BAIF_ESPEAK_BINARY) {
    $EspeakCandidates = @(
        (Join-Path $env:ProgramFiles "eSpeak NG\espeak-ng.exe"),
        $(if (${env:ProgramFiles(x86)}) { Join-Path ${env:ProgramFiles(x86)} "eSpeak NG\espeak-ng.exe" })
    ) | Where-Object { $_ -and (Test-Path $_ -PathType Leaf) }
    if ($EspeakCandidates) { $env:BAIF_ESPEAK_BINARY = $EspeakCandidates[0] }
}
$VenvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    throw "VaaniSetu is not set up yet. Run .\scripts\setup_baif_worker.ps1 once, then start again."
}
& $VenvPython scripts\operations.py migrate
if ($LASTEXITCODE -ne 0) { throw "VaaniSetu could not prepare its local data. See the message above." }
if ($HostAddress -eq "0.0.0.0") {
    Write-Warning "LAN mode is enabled. Use it only on a BAIF-approved private network; never expose this port to the public internet."
}
$DisplayHost = if ($HostAddress -eq "0.0.0.0") { "<this-computer-IP>" } else { $HostAddress }
Write-Host "VaaniSetu is starting at http://${DisplayHost}:$Port"
Write-Host "Keep this window open while VaaniSetu is in use. Press Ctrl+C to stop it safely."
& $VenvPython -m uvicorn app:app --host $HostAddress --port $Port
