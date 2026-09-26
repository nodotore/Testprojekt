<#
.SYNOPSIS
    Richtet ein, dass alle Projekte automatisch bei jeder Windows-Anmeldung
    starten (optional - nur ausführen, wenn das wirklich gewünscht ist).

.DESCRIPTION
    Legt eine Verknüpfung auf Alle-Projekte-starten.bat im persönlichen
    Autostart-Ordner des aktuell angemeldeten Windows-Benutzers an
    (shell:startup). Wirkt sich nur auf dieses Windows-Benutzerkonto aus,
    nicht systemweit, und erfordert keine Administratorrechte.

    Rückgängig machen: scripts\windows\Autostart-entfernen.ps1 ausführen.

.EXAMPLE
    .\scripts\windows\Autostart-einrichten.ps1
#>

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$TargetBat = Join-Path $RepoRoot "Alle-Projekte-starten.bat"

if (-not (Test-Path $TargetBat)) {
    Write-Error "Alle-Projekte-starten.bat wurde nicht gefunden unter: $TargetBat"
    exit 1
}

$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "Alle-Projekte-starten.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $TargetBat
$shortcut.WorkingDirectory = $RepoRoot
$shortcut.WindowStyle = 7  # 7 = minimiert
$shortcut.Description = "Startet automatisch alle Projekte (Website, PWAs, Investment-Analysator)"
$shortcut.Save()

Write-Host "Autostart eingerichtet: $ShortcutPath" -ForegroundColor Green
Write-Host "Alle Projekte starten ab der nächsten Windows-Anmeldung automatisch."
Write-Host "Zum Entfernen: scripts\windows\Autostart-entfernen.ps1 ausführen."
