<#
.SYNOPSIS
    Startet alle Projekte in diesem Ordner mit einem Aufruf: die Website
    samt beider PWAs (CD Musikfinder, Use-Case-Interview-App) und den
    Investment-Analysator.

.DESCRIPTION
    - Website/PWAs: startet einen lokalen Webserver (Python) im
      Projektordner und öffnet die Startseite im Standardbrowser. Ein
      echter Server ist nötig, damit Service Worker/Offline-Funktion
      zuverlässig funktionieren - über file:// im Browser geht das nicht.
      Von der Startseite aus sind CD Musikfinder und die Use-Case-App
      über die Navigation erreichbar.
    - Investment-Analysator: ruft investment-analyzer\start.bat auf
      (legt beim allerersten Start eine eigene virtuelle Python-Umgebung
      an, installiert Abhängigkeiten, migriert die Datenbank und öffnet
      danach die Streamlit-Oberfläche in einem eigenen Fenster). Details:
      investment-analyzer\README.md.

    Bereits laufende Server/Prozesse (erkannt am belegten Port) werden
    nicht doppelt gestartet. Zum Beenden: Alle-Projekte-stoppen.ps1
    ausführen, oder die geöffneten Fenster einfach schließen.

.PARAMETER WebsitePort
    Port für den lokalen Website-Server (Standard: 5500).

.EXAMPLE
    .\Alle-Projekte-starten.ps1
#>

[CmdletBinding()]
param(
    [int]$WebsitePort = 5500
)

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return [pscustomobject]@{ Exe = "py"; Args = @("-3") }
    }
    foreach ($exe in @("python3", "python")) {
        if (Get-Command $exe -ErrorAction SilentlyContinue) {
            return [pscustomobject]@{ Exe = $exe; Args = @() }
        }
    }
    return $null
}

function Test-PortInUse {
    param([int]$Port)
    try {
        return $null -ne (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    } catch {
        return $false
    }
}

Write-Host "== Alle Projekte werden gestartet ==" -ForegroundColor Cyan

# 1) Website + PWAs (CD Musikfinder, Use-Case-App über die Navigation erreichbar)
$py = Get-PythonCommand
if ($py) {
    if (Test-PortInUse -Port $WebsitePort) {
        Write-Host "Website-Server läuft bereits auf Port $WebsitePort." -ForegroundColor Yellow
    } else {
        Write-Host "Starte Website-Server auf http://localhost:$WebsitePort ..."
        $procArgs = @($py.Args) + @("-m", "http.server", "$WebsitePort")
        Start-Process -FilePath $py.Exe -ArgumentList $procArgs -WorkingDirectory $RepoRoot -WindowStyle Minimized | Out-Null
        Start-Sleep -Milliseconds 800
    }
    Start-Process "http://localhost:$WebsitePort/index.html"
} else {
    Write-Warning "Kein Python gefunden - Website wird stattdessen direkt als Datei geöffnet (Offline-Funktion/Service Worker funktioniert dann nicht zuverlässig)."
    Start-Process (Join-Path $RepoRoot "index.html")
}

# 2) Investment-Analysator (eigenes Fenster, eigene venv/Datenbank)
$iaDir = Join-Path $RepoRoot "investment-analyzer"
$iaStartBat = Join-Path $iaDir "start.bat"
if (Test-Path $iaStartBat) {
    if (Test-PortInUse -Port 8501) {
        Write-Host "Investment-Analysator läuft vermutlich bereits (Port 8501 belegt)." -ForegroundColor Yellow
    } else {
        Write-Host "Starte Investment-Analysator (eigenes Fenster, erster Start kann einige Minuten dauern) ..."
        Start-Process -FilePath $iaStartBat -WorkingDirectory $iaDir | Out-Null
    }
} else {
    Write-Warning "investment-analyzer\start.bat nicht gefunden - übersprungen."
}

Write-Host ""
Write-Host "Fertig." -ForegroundColor Green
Write-Host " - Website:               http://localhost:$WebsitePort/index.html"
Write-Host " - CD Musikfinder:        http://localhost:$WebsitePort/cd-musikfinder.html"
Write-Host " - Use-Case-Interview:    http://localhost:$WebsitePort/use-case-app.html"
Write-Host " - Investment-Analysator: eigenes Fenster, öffnet unter http://localhost:8501"
Write-Host ""
Write-Host "Zum Beenden: .\Alle-Projekte-stoppen.ps1 ausführen, oder die geöffneten Fenster schließen."
