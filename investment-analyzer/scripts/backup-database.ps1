<#
.SYNOPSIS
    Erstellt eine Sicherung der lokalen Investment-Analysator-Datenbank.

.DESCRIPTION
    Kopiert die aktuelle SQLite-Datenbankdatei als zeitgestempelte Kopie
    nach %USERPROFILE%\InvestmentAnalyzer\backups (siehe BENUTZERHANDBUCH.md,
    Abschnitt "Datensicherung"). Für eine konsistente Sicherung sollte der
    Investment-Analysator dabei nicht laufen (keine offene Schreibverbindung
    zur Datenbank).

.EXAMPLE
    .\scripts\backup-database.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -Path $ProjectRoot

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Keine virtuelle Umgebung gefunden -- bitte zuerst '.\start.ps1' ausführen."
    exit 1
}

& $venvPython -m investment_analyzer.db.backup_cli sichern
exit $LASTEXITCODE
