Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python 3.10 or 3.11 is required. Install Python, then run this setup again."
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue) -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Installing FFmpeg..."
    winget install --exact --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
}

if (-not (Get-Command tesseract -ErrorAction SilentlyContinue) -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Tesseract OCR..."
    winget install --exact --id tesseract-ocr.tesseract --accept-package-agreements --accept-source-agreements
}

py scripts\one_click_setup.py --profile balanced
Write-Host ""
Write-Host "VaaniSetu setup is complete. Start it with scripts\start_baif_worker.ps1"
