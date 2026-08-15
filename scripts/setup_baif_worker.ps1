Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python 3.10 or 3.11 is required. Install it from python.org with the Python launcher, then run this setup again."
}

$PythonVersion = $null
foreach ($Candidate in @("3.11", "3.10")) {
    & py "-$Candidate" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == tuple(map(int, '$Candidate'.split('.'))) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $PythonVersion = $Candidate
        break
    }
}
if (-not $PythonVersion) {
    throw "VaaniSetu needs Python 3.10 or 3.11. Install one of those versions from python.org, then rerun this script."
}

$VenvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating the private VaaniSetu Python environment..."
    & py "-$PythonVersion" -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create the VaaniSetu Python environment." }
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue) -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Installing FFmpeg..."
    winget install --exact --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
}

if (-not (Get-Command git -ErrorAction SilentlyContinue) -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Git for release integrity checks..."
    winget install --exact --id Git.Git --accept-package-agreements --accept-source-agreements
}

if (-not (Get-Command tesseract -ErrorAction SilentlyContinue) -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Tesseract OCR..."
    winget install --exact --id tesseract-ocr.tesseract --accept-package-agreements --accept-source-agreements
}

& $VenvPython scripts\one_click_setup.py --profile balanced
if ($LASTEXITCODE -ne 0) { throw "VaaniSetu setup did not complete. Read the final message above, correct it, and rerun this script." }
Write-Host ""
Write-Host "VaaniSetu setup is complete."
Write-Host "Next: reopen PowerShell, run the Windows acceptance command in SETUP.md, then start VaaniSetu."
