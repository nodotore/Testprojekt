<#
.SYNOPSIS
    Beendet alle über Alle-Projekte-starten.ps1 gestarteten Server
    (Website-Server und Investment-Analysator).

.DESCRIPTION
    Findet die Prozesse anhand des von ihnen belegten Ports (statt sich
    auf gemerkte Prozess-IDs zu verlassen) und beendet genau diese -
    unabhängig davon, ob sie direkt oder über start.bat/cmd.exe gestartet
    wurden.

.EXAMPLE
    .\Alle-Projekte-stoppen.ps1
#>

[CmdletBinding()]
param(
    [int]$WebsitePort = 5500,
    [int]$StreamlitPort = 8501
)

function Stop-ByPort {
    param(
        [int]$Port,
        [string]$Label
    )

    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    } catch {
        $conns = $null
    }

    if (-not $conns) {
        Write-Host "$Label läuft nicht (Port $Port frei)." -ForegroundColor Yellow
        return
    }

    $processIds = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        try {
            $proc = Get-Process -Id $processId -ErrorAction Stop
            Write-Host "Beende $Label (PID $processId, $($proc.ProcessName)) ..."
            Stop-Process -Id $processId -Force
        } catch {
            Write-Warning "Konnte Prozess $processId (${Label}) nicht beenden: $_"
        }
    }
}

Write-Host "== Alle Projekte werden gestoppt ==" -ForegroundColor Cyan
Stop-ByPort -Port $WebsitePort -Label "Website-Server"
Stop-ByPort -Port $StreamlitPort -Label "Investment-Analysator"
Write-Host "Fertig." -ForegroundColor Green
