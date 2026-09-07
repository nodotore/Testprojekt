<#
.SYNOPSIS
    Installiert Entwicklungsabhängigkeiten (falls nötig) und führt
    ruff, mypy und die pytest-Testsuite aus.

.EXAMPLE
    .\scripts\run-tests.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -Path $ProjectRoot

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Keine virtuelle Umgebung gefunden — führe zuerst 'start.ps1 -Dev' aus." -ForegroundColor Yellow
    & (Join-Path $ProjectRoot "start.ps1") -Dev -SkipMigrate
}

Write-Host "== ruff (Lint) ==" -ForegroundColor Cyan
& $venvPython -m ruff check .

Write-Host "== mypy (Typprüfung) ==" -ForegroundColor Cyan
& $venvPython -m mypy src

Write-Host "== pytest (Tests) ==" -ForegroundColor Cyan
& $venvPython -m pytest -v
