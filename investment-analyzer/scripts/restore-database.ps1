<#
.SYNOPSIS
    Stellt die Investment-Analysator-Datenbank aus einer zuvor erstellten
    Sicherung wieder her.

.DESCRIPTION
    Überschreibt die aktuelle Datenbankdatei vollständig mit dem Inhalt der
    angegebenen Sicherungsdatei (siehe BENUTZERHANDBUCH.md, Abschnitt
    "Datensicherung"). Der Investment-Analysator sollte dabei nicht laufen.
    Ohne Angabe eines Pfads werden zunächst die vorhandenen Sicherungen
    aufgelistet.

.PARAMETER BackupPfad
    Pfad zur Sicherungsdatei (siehe Ausgabe von backup-database.ps1 bzw.
    'python -m investment_analyzer.db.backup_cli auflisten').

.EXAMPLE
    .\scripts\restore-database.ps1
.EXAMPLE
    .\scripts\restore-database.ps1 "$env:USERPROFILE\InvestmentAnalyzer\backups\investment_analyzer-20260908T120000Z.db"
#>

param(
    [string]$BackupPfad
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -Path $ProjectRoot

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Keine virtuelle Umgebung gefunden -- bitte zuerst '.\start.ps1' ausführen."
    exit 1
}

if (-not $BackupPfad) {
    Write-Host "Kein Sicherungspfad angegeben -- vorhandene Sicherungen:" -ForegroundColor Yellow
    & $venvPython -m investment_analyzer.db.backup_cli auflisten
    Write-Host ""
    Write-Host "Aufruf mit Pfad: .\scripts\restore-database.ps1 <Sicherungsdatei>"
    exit 1
}

& $venvPython -m investment_analyzer.db.backup_cli wiederherstellen $BackupPfad
exit $LASTEXITCODE
