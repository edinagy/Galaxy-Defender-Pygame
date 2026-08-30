param(
    [string]$PythonExecutable = "python"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

& $PythonExecutable -m PyInstaller --noconfirm --clean GalaxyDefender.spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

$gameExecutable = Join-Path $projectRoot "dist\GalaxyDefender\GalaxyDefender.exe"
if (-not (Test-Path -LiteralPath $gameExecutable)) {
    throw "Build finished without GalaxyDefender.exe."
}

Write-Host "Build ready: $gameExecutable"

