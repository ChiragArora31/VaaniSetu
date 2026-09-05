param(
    [Parameter(Mandatory = $true)]
    [string]$VideosPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:BAIF_ALLOW_MODEL_DOWNLOAD = "0"
$env:BAIF_WHISPER_DEVICE = "cpu"
$env:BAIF_WHISPER_COMPUTE_TYPE = "int8"

$VenvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    throw "VaaniSetu is not set up. Run .\scripts\setup_baif_worker.ps1 first."
}
if (-not (Test-Path $VideosPath -PathType Container)) {
    throw "BAIF video folder was not found: $VideosPath"
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required for source-integrity checks. Install Git, reopen PowerShell, and run acceptance again."
}

$EvidenceDir = Join-Path (Get-Location) "outputs\windows_acceptance"
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
$LogPath = Join-Path $EvidenceDir "acceptance.log"
$Failed = New-Object System.Collections.Generic.List[string]

function Invoke-AcceptanceCheck {
    param([string]$Name, [scriptblock]$Action)
    Write-Host ""
    Write-Host "=== $Name ==="
    & $Action
    if ($LASTEXITCODE -ne 0) {
        $Failed.Add($Name)
        Write-Host "FAILED: $Name" -ForegroundColor Red
    } else {
        Write-Host "PASSED: $Name" -ForegroundColor Green
    }
}

Start-Transcript -Path $LogPath -Force | Out-Null
try {
    $Computer = Get-CimInstance Win32_ComputerSystem
    $OperatingSystem = Get-CimInstance Win32_OperatingSystem
    $Processor = Get-CimInstance Win32_Processor | Select-Object -First 1
    $Machine = [ordered]@{
        generated_at = (Get-Date).ToUniversalTime().ToString("o")
        computer_model = $Computer.Model
        memory_gb = [Math]::Round($Computer.TotalPhysicalMemory / 1GB, 1)
        operating_system = $OperatingSystem.Caption
        os_version = $OperatingSystem.Version
        cpu = $Processor.Name
        logical_processors = $Computer.NumberOfLogicalProcessors
        release_commit = (& git rev-parse HEAD 2>$null)
    }
    $Machine | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $EvidenceDir "machine.json")

    Invoke-AcceptanceCheck "Dependency integrity" { & $VenvPython -m pip check }
    Invoke-AcceptanceCheck "Automated tests" { & $VenvPython -m unittest discover -s tests -v }
    Invoke-AcceptanceCheck "Release policy" { & $VenvPython scripts\release_check.py }
    Invoke-AcceptanceCheck "Production preflight" {
        & $VenvPython scripts\operations.py preflight --output (Join-Path $EvidenceDir "preflight_report.json")
    }
    Invoke-AcceptanceCheck "Model inventory" {
        & $VenvPython scripts\operations.py model-inventory (Join-Path $EvidenceDir "model_inventory.json")
    }
    Invoke-AcceptanceCheck "BAIF video compatibility" {
        & $VenvPython scripts\validate_baif_samples.py $VideosPath --output (Join-Path $EvidenceDir "baif_sample_validation.json")
    }
} finally {
    Stop-Transcript | Out-Null
}

$Summary = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    status = if ($Failed.Count -eq 0) { "passed" } else { "failed" }
    failed_checks = @($Failed)
    evidence_directory = $EvidenceDir
    next_step = if ($Failed.Count -eq 0) {
        "Start VaaniSetu, complete the manual trainer/field UAT in the onboarding runbook, then run the shortest BAIF video."
    } else {
        "Resolve every failed check and rerun this script before accepting BAIF jobs."
    }
}
$Summary | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $EvidenceDir "acceptance_summary.json")
$Summary | ConvertTo-Json

if ($Failed.Count -ne 0) {
    exit 1
}
