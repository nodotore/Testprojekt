<#
.SYNOPSIS
    Entfernt den automatischen Start aller Projekte bei Windows-Anmeldung
    (Gegenstück zu Autostart-einrichten.ps1).

.EXAMPLE
    .\scripts\windows\Autostart-entfernen.ps1
#>

$ErrorActionPreference = "Stop"

$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "Alle-Projekte-starten.lnk"

if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
    Write-Host "Autostart entfernt." -ForegroundColor Green
} else {
    Write-Host "Kein Autostart-Eintrag gefunden (bereits entfernt?)." -ForegroundColor Yellow
}
