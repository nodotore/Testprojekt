<#
.SYNOPSIS
    Prüft jedes Projekt einzeln und schreibt einen Bericht (Diagnose.txt).

.DESCRIPTION
    Erstellt zuerst mit Starter-erstellen.ps1 alle Start-EXEs neu (damit
    immer die aktuelle Version geprüft wird), richtet dann je Projekt die
    Python-Umgebung ohne Zeitlimit ein und startet es erst danach.
    Sammelt Angaben zur Umgebung (Python, Node.js, PowerShell, ...),
    startet danach jede gefundene Starten.exe einzeln für einige Sekunden,
    zeichnet alle Ausgaben und Fehlermeldungen auf und beendet das
    Programm wieder. Projektordner ohne Starten.exe werden mit ihrem
    Dateiinhalt aufgelistet, damit man sieht, wie sie gestartet werden.

    Der Bericht landet in Diagnose.txt neben diesem Skript.

.PARAMETER Root
    Grundordner. Standard: Y:\claude, falls vorhanden, sonst der
    übergeordnete Ordner dieses Skripts.

.PARAMETER Sekunden
    Wie lange jedes Programm laufen darf, bevor es wieder beendet wird.
    Läuft es nach dieser Zeit noch, gilt es als erfolgreich gestartet.

.PARAMETER EinrichtenMinuten
    Höchstdauer für das Einrichten (Python-Pakete installieren) je Projekt.

.PARAMETER OhneStarttest
    Nur Umgebung und Ordnerinhalte erfassen, keine Programme starten.
#>

[CmdletBinding()]
param(
    [string]$Root,
    [int]$Sekunden = 20,
    [switch]$OhneStarttest,
    [int]$EinrichtenMinuten = 30,
    [string]$ExeName = 'Starten.exe'
)

$ErrorActionPreference = 'Continue'

if (-not $Root) {
    if (Test-Path -LiteralPath 'Y:\claude') { $Root = 'Y:\claude' }
    else { $Root = Split-Path -Parent $PSScriptRoot }
}
$Root = (Resolve-Path -LiteralPath $Root).Path
$report = Join-Path $PSScriptRoot 'Diagnose.txt'
$lines = New-Object System.Collections.Generic.List[string]

function Add([string]$text = '') {
    $lines.Add($text)
    Write-Host $text
}

function Get-ToolInfo([string]$exe, [string]$versionArg) {
    $cmd = Get-Command $exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $cmd) { return 'NICHT GEFUNDEN' }
    $path = $cmd.Source
    if ($path -match 'WindowsApps') {
        return "$path  (nur Microsoft-Store-Platzhalter, kein echtes Programm!)"
    }
    $ver = ''
    try { $ver = (& $path $versionArg 2>&1 | Select-Object -First 1) -join '' } catch { $ver = $_.Exception.Message }
    return "$path  ->  $ver"
}

function Get-Listing([string]$dir) {
    Get-ChildItem -LiteralPath $dir -Force -ErrorAction SilentlyContinue | Sort-Object { -not $_.PSIsContainer }, Name |
        ForEach-Object { if ($_.PSIsContainer) { "      [$($_.Name)]" } else { "      $($_.Name)" } }
}

function Test-Blocked([string]$path) {
    try { return [bool](Get-Item -LiteralPath $path -Stream 'Zone.Identifier' -ErrorAction Stop) }
    catch { return $false }
}

function Get-Relative([string]$path) {
    return $path.Substring($Root.TrimEnd('\').Length).TrimStart('\')
}

Add "Diagnose vom $(Get-Date -Format 'dd.MM.yyyy HH:mm')"
Add "Grundordner: $Root"
Add ''
Add '=== Umgebung ==='
Add "Windows:        $([Environment]::OSVersion.VersionString)"
Add "PowerShell:     $($PSVersionTable.PSVersion)"
Add "Ausführungsrichtlinie: $(Get-ExecutionPolicy)"
Add "python:         $(Get-ToolInfo 'python.exe' '--version')"
Add "py:             $(Get-ToolInfo 'py.exe' '--version')"
Add "node:           $(Get-ToolInfo 'node.exe' '--version')"
Add "npm:            $(Get-ToolInfo 'npm.cmd' '--version')"
Add "git:            $(Get-ToolInfo 'git.exe' '--version')"
$blocked = @(Get-ChildItem -LiteralPath $PSScriptRoot -File | Where-Object { Test-Blocked $_.FullName })
Add "Gesperrte Dateien (aus dem Internet) im Werkzeug-Ordner: $($blocked.Count)"
Add ''

# Start-EXEs mit genau dieser Werkzeug-Version neu erstellen.
$StarterVersion = ([regex]::Match([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'Starter-erstellen.ps1')),
    "StarterVersion = '([\d.]+)'")).Groups[1].Value
Add "Werkzeug-Ordner: $PSScriptRoot (Version $StarterVersion)"
Add ''
Add '=== Start-EXEs neu erstellen ==='
Write-Host 'Erstelle Start-EXEs neu ...' -ForegroundColor Cyan
try {
    $gen = & (Join-Path $PSScriptRoot 'Starter-erstellen.ps1') -Root $Root -ExeName $ExeName -PassThru
    ($gen | Format-Table -AutoSize -Wrap | Out-String -Width 300) -split "`r?`n" |
        Where-Object { $_.Trim() } | ForEach-Object { Add $_ }
} catch {
    Add "FEHLER beim Erstellen: $($_.Exception.Message)"
}
Add ''

# Alle Starten.exe finden (bis 6 Ebenen tief, ohne node_modules/.venv).
$skip = '\\(node_modules|\.venv|venv|\.git|__pycache__|site-packages)(\\|$)'
$allDirs = @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Depth 5 -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch $skip -and $_.FullName -ne $PSScriptRoot })
$exeDirs = @($allDirs | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName $ExeName) })

# Startet die EXE unsichtbar, sammelt alle Ausgaben und beendet sie nach
# $Seconds Sekunden (samt Unterprozessen), falls sie dann noch läuft.
function Invoke-Captured([string]$Exe, [string]$WorkDir, [int]$Seconds, [hashtable]$Env) {
    $psi = New-Object Diagnostics.ProcessStartInfo $Exe
    $psi.WorkingDirectory = $WorkDir
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    foreach ($k in $Env.Keys) { $psi.EnvironmentVariables[$k] = $Env[$k] }
    $p = [Diagnostics.Process]::Start($psi)
    $p.StandardInput.Close()   # Eingabe leer: "Taste drücken" blockiert nicht
    $outTask = $p.StandardOutput.ReadToEndAsync()
    $errTask = $p.StandardError.ReadToEndAsync()
    $finished = $p.WaitForExit($Seconds * 1000)
    if (-not $finished) { & taskkill.exe /PID $p.Id /T /F 2>&1 | Out-Null }
    [void]$outTask.Wait(5000)
    [void]$errTask.Wait(5000)
    $text = ''
    if ($outTask.IsCompleted) { $text += $outTask.Result }
    if ($errTask.IsCompleted) { $text += "`n" + $errTask.Result }
    return @{
        Finished = $finished
        ExitCode = $(if ($finished) { $p.ExitCode } else { $null })
        Output   = @($text -split "`r?`n" | Where-Object { $_.Trim() })
    }
}

function Add-Output([string[]]$Output, [int]$Max = 40) {
    if ($Output.Count -gt $Max) {
        Add "   Ausgabe (letzte $Max von $($Output.Count) Zeilen):"
        $Output = $Output[-$Max..-1]
    } else {
        Add '   Ausgabe:'
    }
    if ($Output.Count -eq 0) { Add '      (keine)' }
    $Output | ForEach-Object { Add "      $_" }
}

$index = 0
foreach ($dir in $exeDirs) {
    $index++
    $exe = Join-Path $dir.FullName $ExeName
    Add "=== [$index/$($exeDirs.Count)] $(Get-Relative $dir.FullName) ==="
    Add '   Inhalt:'
    Get-Listing $dir.FullName | ForEach-Object { Add $_ }
    if (Test-Blocked $exe) { Add "   ACHTUNG: $ExeName ist als 'aus dem Internet' gesperrt." }
    $ver = (Get-Item -LiteralPath $exe).VersionInfo.FileVersion
    if ($ver -ne $StarterVersion) {
        Add "   ACHTUNG: veraltete $ExeName (Version '$ver', aktuell $StarterVersion) - Neuerstellung fehlgeschlagen?"
    }

    if ($OhneStarttest) { Add ''; continue }

    try {
        # 1. Python-Umgebung einrichten, ohne Zeitdruck (erster Start kann dauern).
        Write-Host "   Richte ein (Python-Pakete o. ä., kann einige Minuten dauern) ..." -ForegroundColor Cyan
        $r = Invoke-Captured $exe $dir.FullName (60 * $EinrichtenMinuten) @{ STARTER_NUR_EINRICHTEN = '1' }
        if (-not $r.Finished) {
            Add "   EINRICHTEN: nach $EinrichtenMinuten Minuten abgebrochen"
            Add-Output $r.Output
        } elseif ($r.ExitCode -ne 0) {
            Add "   EINRICHTEN: FEHLGESCHLAGEN (Fehlercode $($r.ExitCode))"
            Add-Output $r.Output
        } elseif ($r.Output.Count) {
            Add '   EINRICHTEN: ok'
        }

        # 2. Starttest
        Write-Host "   Starte für $Sekunden Sekunden ..." -ForegroundColor Cyan
        $r = Invoke-Captured $exe $dir.FullName $Sekunden @{ STARTER_DIAGNOSE = '1' }
        if ($r.Finished) {
            Add "   ERGEBNIS: nach kurzer Zeit beendet, Fehlercode $($r.ExitCode)"
        } else {
            Add "   ERGEBNIS: läuft nach $Sekunden s noch (Start erfolgreich) - wird beendet"
        }
        Add-Output $r.Output
    } catch {
        Add "   ERGEBNIS: konnte nicht gestartet werden: $($_.Exception.Message)"
    }
    Add ''
}

# Ordner (bis 2 Ebenen) ohne Starten.exe darin oder darunter.
$withoutExe = @($allDirs | Where-Object {
    $p = $_.FullName + '\'
    (Get-Relative $_.FullName).Split('\').Count -le 2 -and
    -not ($exeDirs | Where-Object { ($_.FullName + '\').StartsWith($p) -or $p.StartsWith($_.FullName + '\') })
})
if ($withoutExe.Count) {
    Add '=== Ordner ohne Starten.exe ==='
    foreach ($d in $withoutExe) {
        Add "--- $(Get-Relative $d.FullName)"
        Get-Listing $d.FullName | ForEach-Object { Add $_ }
    }
}

[IO.File]::WriteAllLines($report, $lines, (New-Object Text.UTF8Encoding($true)))
Write-Host ''
Write-Host "Bericht gespeichert: $report" -ForegroundColor Green
Write-Host 'Bitte diese Datei an Claude schicken.'
