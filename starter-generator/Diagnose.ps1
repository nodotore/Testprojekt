<#
.SYNOPSIS
    Prüft jedes Projekt einzeln und schreibt einen Bericht (Diagnose.txt).

.DESCRIPTION
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

.PARAMETER OhneStarttest
    Nur Umgebung und Ordnerinhalte erfassen, keine Programme starten.
#>

[CmdletBinding()]
param(
    [string]$Root,
    [int]$Sekunden = 20,
    [switch]$OhneStarttest,
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

# Alle Starten.exe finden (bis 6 Ebenen tief, ohne node_modules/.venv).
$skip = '\\(node_modules|\.venv|venv|\.git|__pycache__|site-packages)(\\|$)'
$allDirs = @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Depth 5 -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch $skip -and $_.FullName -ne $PSScriptRoot })
$exeDirs = @($allDirs | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName $ExeName) })

$index = 0
foreach ($dir in $exeDirs) {
    $index++
    Add "=== [$index/$($exeDirs.Count)] $(Get-Relative $dir.FullName) ==="
    Add '   Inhalt:'
    Get-Listing $dir.FullName | ForEach-Object { Add $_ }
    if (Test-Blocked (Join-Path $dir.FullName $ExeName)) { Add "   ACHTUNG: $ExeName ist als 'aus dem Internet' gesperrt." }

    if ($OhneStarttest) { Add ''; continue }

    Write-Host "   Starte für $Sekunden Sekunden ..." -ForegroundColor Cyan
    try {
        $psi = New-Object Diagnostics.ProcessStartInfo (Join-Path $dir.FullName $ExeName)
        $psi.WorkingDirectory = $dir.FullName
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardInput = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $p = [Diagnostics.Process]::Start($psi)
        $p.StandardInput.Close()   # Eingabe leer: "Taste drücken" blockiert nicht
        $outTask = $p.StandardOutput.ReadToEndAsync()
        $errTask = $p.StandardError.ReadToEndAsync()
        if ($p.WaitForExit($Sekunden * 1000)) {
            Add "   ERGEBNIS: nach kurzer Zeit beendet, Fehlercode $($p.ExitCode)"
        } else {
            Add "   ERGEBNIS: läuft nach $Sekunden s noch (Start vermutlich erfolgreich) - wird beendet"
            & taskkill.exe /PID $p.Id /T /F 2>&1 | Out-Null
        }
        [void]$outTask.Wait(5000)
        [void]$errTask.Wait(5000)
        $text = ''
        if ($outTask.IsCompleted) { $text += $outTask.Result }
        if ($errTask.IsCompleted) { $text += "`n" + $errTask.Result }
        $output = @($text -split "`r?`n" | Where-Object { $_.Trim() })
        if ($output.Count -gt 40) {
            Add "   Ausgabe (letzte 40 von $($output.Count) Zeilen):"
            $output = $output[-40..-1]
        } else {
            Add '   Ausgabe:'
        }
        if ($output.Count -eq 0) { Add '      (keine)' }
        $output | ForEach-Object { Add "      $_" }
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
