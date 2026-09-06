param(
    [switch]$InstallApprovedSystemTools
)

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

$CppBuildToolsComponent = "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"
$HasCppBuildTools = [bool](Get-Command cl.exe -ErrorAction SilentlyContinue)
$VsWhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
if (-not $HasCppBuildTools -and (Test-Path $VsWhere)) {
    $CppInstallPath = & $VsWhere -latest -products * -requires $CppBuildToolsComponent -property installationPath
    $HasCppBuildTools = -not [string]::IsNullOrWhiteSpace(($CppInstallPath | Select-Object -First 1))
}
if (-not $HasCppBuildTools) {
    throw @"
Microsoft C++ Build Tools are required to install IndicTransToolkit.
Install Microsoft C++ Build Tools and select the "Desktop development with C++" workload, including the MSVC x64/x86 compiler and a Windows SDK.
Official installer guidance: https://learn.microsoft.com/en-us/cpp/overview/acquire-msvc?view=msvc-170
After installation, close and reopen PowerShell, then run this setup script again. The Visual C++ Redistributable alone is not sufficient.
"@
}
Write-Host "Microsoft C++ Build Tools prerequisite found."

$VenvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating the private VaaniSetu Python environment..."
    & py "-$PythonVersion" -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create the VaaniSetu Python environment." }
}

$EspeakPaths = @(
    (Join-Path $env:ProgramFiles "eSpeak NG\espeak-ng.exe"),
    $(if (${env:ProgramFiles(x86)}) { Join-Path ${env:ProgramFiles(x86)} "eSpeak NG\espeak-ng.exe" })
) | Where-Object { $_ }
$SystemTools = @(
    @{ Command = "ffmpeg"; Package = "Gyan.FFmpeg"; Label = "FFmpeg" },
    @{ Command = "git"; Package = "Git.Git"; Label = "Git" },
    @{ Command = "tesseract"; Package = "tesseract-ocr.tesseract"; Label = "Tesseract OCR" },
    @{ Command = "espeak-ng"; Package = "eSpeak-NG.eSpeak-NG"; Label = "eSpeak NG translated speech"; AlternatePaths = $EspeakPaths }
)
$MissingSystemTools = @($SystemTools | Where-Object {
    $CommandMissing = -not (Get-Command $_.Command -ErrorAction SilentlyContinue)
    $AlternateMissing = -not $_.ContainsKey("AlternatePaths") -or -not ($_.AlternatePaths | Where-Object { Test-Path $_ -PathType Leaf })
    $CommandMissing -and $AlternateMissing
})
if ($MissingSystemTools.Count -gt 0 -and -not $InstallApprovedSystemTools) {
    $MissingLabels = ($MissingSystemTools | ForEach-Object { $_.Label }) -join ", "
    throw @"
Missing required system tools: $MissingLabels.
Install them only through an IT/organiser-approved method. After approval, either install them manually or rerun this script with -InstallApprovedSystemTools to use Windows Package Manager.
Do not use that switch on a shared Hackathon laptop without explicit organiser approval.
"@
}
if ($MissingSystemTools.Count -gt 0) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "Windows Package Manager is unavailable. Ask IT/the organiser to install the approved system prerequisites, then rerun setup."
    }
    foreach ($Tool in $MissingSystemTools) {
        Write-Host "Installing approved prerequisite: $($Tool.Label)..."
        & winget install --exact --id $Tool.Package --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { throw "Could not install $($Tool.Label)." }
    }
    Write-Host "Approved system tools were installed. Reopen PowerShell after setup so their command paths are refreshed."
}

& $VenvPython scripts\one_click_setup.py --profile balanced
if ($LASTEXITCODE -ne 0) { throw "VaaniSetu setup did not complete. Read the final message above, correct it, and rerun this script." }
Write-Host ""
Write-Host "VaaniSetu setup is complete."
Write-Host "Next: reopen PowerShell, run the Windows acceptance command in SETUP.md, then start VaaniSetu."
