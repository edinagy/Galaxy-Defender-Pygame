param(
    [string]$PythonExecutable = "python"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

& (Join-Path $PSScriptRoot "build_windows.ps1") -PythonExecutable $PythonExecutable
if ($LASTEXITCODE -ne 0) {
    throw "Windows build failed."
}

$releaseFolder = Join-Path $projectRoot "release"
$releaseBuildFolder = Join-Path $releaseFolder "GalaxyDefender-1.0.0-Windows"
$archivePath = Join-Path $releaseFolder "GalaxyDefender-1.0.0-Windows.zip"
$buildContents = Join-Path $projectRoot "dist\GalaxyDefender\*"

New-Item -ItemType Directory -Path $releaseFolder -Force | Out-Null
New-Item -ItemType Directory -Path $releaseBuildFolder -Force | Out-Null
Copy-Item -Path $buildContents -Destination $releaseBuildFolder -Recurse -Force
Compress-Archive -Path (Join-Path $releaseBuildFolder "*") -DestinationPath $archivePath -Force

if (-not (Test-Path -LiteralPath $archivePath)) {
    throw "Release archive was not created."
}

Write-Host "Release archive ready: $archivePath"
