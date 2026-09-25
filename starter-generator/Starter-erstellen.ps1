<#
.SYNOPSIS
    Erstellt für jedes Projekt unter einem Grundordner eine Start-EXE.

.DESCRIPTION
    Durchsucht die Unterordner von -Root (Standard: Y:\claude) bis zur
    Tiefe -Tiefe, erkennt, wie das jeweilige Projekt gestartet wird, und
    legt im Projektordner eine "Starten.exe" an. Sobald ein Ordner als
    Projekt erkannt ist, wird darunter nicht weiter gesucht. Ein Doppelklick darauf startet das
    Projekt – ohne PowerShell-Kenntnisse und ohne Ausführungsrichtlinie.

    Die EXE enthält nur relative Pfade. Ein Projektordner kann deshalb
    samt EXE auf einen anderen Rechner/USB-Stick kopiert werden und
    startet dort genauso (vorausgesetzt Python/Node.js usw. sind dort
    installiert).

    Erkannt wird (in dieser Reihenfolge):
      1. start.ps1 / starten.ps1 / run.ps1 / launch.ps1
      2. start.bat / starten.bat / run.bat (bzw. .cmd)
      3. genau ein einziges .ps1- bzw. .bat/.cmd-Skript im Ordner
      4. package.json mit "start"- oder "dev"-Skript (npm)
      5. app.py / main.py / run.py / start.py / gui.py / <Ordnername>.py
         bzw. genau eine .py-Datei (Streamlit-Apps werden erkannt)
      6. index.html (wird im Standardbrowser geöffnet)

    Kompiliert wird mit dem in Windows 10/11 eingebauten C#-Compiler des
    .NET Framework 4 – es muss nichts zusätzlich installiert werden.

.PARAMETER Root
    Grundordner mit den Projekten. Standard: Y:\claude, falls vorhanden,
    sonst der übergeordnete Ordner dieses Skripts.

.PARAMETER Tiefe
    Wie viele Ordnerebenen unter -Root durchsucht werden. Standard: 4

.PARAMETER ExeName
    Dateiname der erzeugten Start-EXE. Standard: Starten.exe

.PARAMETER Force
    Bereits vorhandene Start-EXEs überschreiben (z. B. nach Änderungen).

.PARAMETER Vorschau
    Nur anzeigen, was erkannt würde – nichts erstellen.

.EXAMPLE
    .\Starter-erstellen.ps1
.EXAMPLE
    .\Starter-erstellen.ps1 -Root 'D:\Projekte' -Force
.EXAMPLE
    .\Starter-erstellen.ps1 -Vorschau
#>

[CmdletBinding()]
param(
    [string]$Root,
    [int]$Tiefe = 4,
    [string]$ExeName = 'Starten.exe',
    [switch]$Force,
    [switch]$Vorschau
)

$ErrorActionPreference = 'Stop'

if (-not $Root) {
    if (Test-Path -LiteralPath 'Y:\claude') { $Root = 'Y:\claude' }
    else { $Root = Split-Path -Parent $PSScriptRoot }
}
if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
    throw "Grundordner '$Root' nicht gefunden."
}
$Root = (Resolve-Path -LiteralPath $Root).Path

$csc = @(
    (Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'),
    (Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe')
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $csc -and -not $Vorschau) {
    throw 'Der C#-Compiler des .NET Framework 4 (csc.exe) wurde nicht gefunden.'
}

$template = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'Launcher.cs'))

function Get-FirstExisting([string]$Dir, [string[]]$Names) {
    foreach ($n in $Names) {
        if (Test-Path -LiteralPath (Join-Path $Dir $n) -PathType Leaf) { return $n }
    }
    return $null
}

function Get-Single([string]$Dir, [string[]]$Extensions) {
    $files = @(Get-ChildItem -LiteralPath $Dir -File |
        Where-Object { $Extensions -contains $_.Extension.ToLowerInvariant() })
    if ($files.Count -eq 1) { return $files[0].Name }
    return $null
}

function Find-StartMethod([string]$Dir) {
    $name = Split-Path -Leaf $Dir

    $f = Get-FirstExisting $Dir @('start.ps1', 'starten.ps1', 'run.ps1', 'launch.ps1')
    if ($f) { return @{ Mode = 'ps1'; Target = $f } }

    $f = Get-FirstExisting $Dir @('start.bat', 'start.cmd', 'starten.bat', 'starten.cmd', 'run.bat', 'run.cmd')
    if ($f) { return @{ Mode = 'bat'; Target = $f } }

    $f = Get-Single $Dir @('.ps1')
    if ($f) { return @{ Mode = 'ps1'; Target = $f } }

    $f = Get-Single $Dir @('.bat', '.cmd')
    if ($f) { return @{ Mode = 'bat'; Target = $f } }

    $pkgPath = Join-Path $Dir 'package.json'
    if (Test-Path -LiteralPath $pkgPath -PathType Leaf) {
        try {
            $pkg = [IO.File]::ReadAllText($pkgPath) | ConvertFrom-Json
            if ($pkg.scripts.start) { return @{ Mode = 'npm'; Target = 'start' } }
            if ($pkg.scripts.dev) { return @{ Mode = 'npm'; Target = 'dev' } }
        } catch {
            Write-Warning "$name`: package.json konnte nicht gelesen werden ($($_.Exception.Message))."
        }
    }

    $f = Get-FirstExisting $Dir @('app.py', 'main.py', 'streamlit_app.py', 'run.py', 'start.py', 'gui.py', "$name.py")
    if (-not $f) { $f = Get-Single $Dir @('.py', '.pyw') }
    if ($f) {
        $code = [IO.File]::ReadAllText((Join-Path $Dir $f))
        $mode = if ($code -match '(?m)^\s*(import\s+streamlit|from\s+streamlit\s+import)') { 'streamlit' } else { 'python' }
        return @{ Mode = $mode; Target = $f }
    }

    $f = Get-FirstExisting $Dir @('index.html', 'index.htm')
    if (-not $f) { $f = Get-Single $Dir @('.html', '.htm') }
    if ($f) { return @{ Mode = 'open'; Target = $f } }

    return $null
}

function ConvertTo-CSharpLiteral([string]$s) {
    return $s.Replace('\', '\\').Replace('"', '\"')
}

function New-StarterExe([string]$Dir, [hashtable]$Method, [string]$ExePath) {
    $source = $template.Replace('@@MODE@@', (ConvertTo-CSharpLiteral $Method.Mode))
    $source = $source.Replace('@@TARGET@@', (ConvertTo-CSharpLiteral $Method.Target))
    $source = $source.Replace('@@TITLE@@', (ConvertTo-CSharpLiteral (Split-Path -Leaf $Dir)))

    $work = Join-Path ([IO.Path]::GetTempPath()) ('starter_' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $work | Out-Null
    try {
        $srcFile = Join-Path $work 'Launcher.cs'
        $tmpExe = Join-Path $work 'Starter.exe'
        [IO.File]::WriteAllText($srcFile, $source, (New-Object Text.UTF8Encoding($true)))

        # Webseiten ohne Konsolenfenster öffnen, alles andere mit Konsole,
        # damit Ausgaben und Fehlermeldungen sichtbar sind.
        $kind = if ($Method.Mode -eq 'open') { 'winexe' } else { 'exe' }
        $cscArgs = @('/nologo', '/optimize+', '/nowarn:162', "/target:$kind",
            '/r:System.Windows.Forms.dll', "/out:$tmpExe")
        $icon = Get-ChildItem -LiteralPath $Dir -Filter '*.ico' -File | Select-Object -First 1
        if ($icon) { $cscArgs += "/win32icon:$($icon.FullName)" }
        $cscArgs += $srcFile

        $output = & $csc @cscArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Kompilieren fehlgeschlagen:`n$($output -join "`n")"
        }
        Copy-Item -LiteralPath $tmpExe -Destination $ExePath -Force
    } finally {
        Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Ordner, in denen nie nach Projekten gesucht wird.
$skipNames = @('node_modules', 'venv', 'env', '__pycache__', 'site-packages',
    'dist', 'build', 'bin', 'obj', 'target', 'Lib', 'Scripts', 'Include')

# Merkmale eines Projektordners (auch ohne erkannte Startdatei): darunter
# nicht weitersuchen, sonst würden z. B. src\-Unterordner als Projekt gelten.
function Test-ProjectRoot([string]$Dir) {
    foreach ($n in '.git', 'pyproject.toml', 'requirements.txt', 'setup.py', 'package.json') {
        if (Test-Path -LiteralPath (Join-Path $Dir $n)) { return $true }
    }
    return [bool](Get-ChildItem -LiteralPath $Dir -File -ErrorAction SilentlyContinue |
        Where-Object { '.sln', '.csproj' -contains $_.Extension.ToLowerInvariant() } |
        Select-Object -First 1)
}

function Find-Projects([string]$Dir, [int]$Depth) {
    $children = Get-ChildItem -LiteralPath $Dir -Directory -ErrorAction SilentlyContinue | Sort-Object Name
    foreach ($child in $children) {
        if ($child.Name.StartsWith('.') -or $skipNames -contains $child.Name -or
            $child.FullName -eq $PSScriptRoot -or
            ($child.Attributes -band [IO.FileAttributes]::ReparsePoint)) { continue }

        $method = $null
        try { $method = Find-StartMethod $child.FullName } catch {
            Write-Warning "$($child.FullName): $($_.Exception.Message)"
        }
        if ($method -or (Test-ProjectRoot $child.FullName)) {
            [pscustomobject]@{ Dir = $child.FullName; Method = $method }
        } elseif ($Depth -lt $Tiefe) {
            Find-Projects $child.FullName ($Depth + 1)
        }
    }
}

$modeText = @{
    ps1       = 'PowerShell-Skript'
    bat       = 'Batch-Datei'
    npm       = 'npm'
    python    = 'Python'
    streamlit = 'Streamlit'
    open      = 'im Browser öffnen'
}

Write-Host "Grundordner: $Root"
Write-Host ''

$results = foreach ($project in Find-Projects $Root 1) {
    $method = $project.Method
    $exePath = Join-Path $project.Dir $ExeName
    $row = [pscustomobject]@{
        Projekt  = $project.Dir.Substring($Root.TrimEnd('\').Length).TrimStart('\', '/')
        Startart = if ($method) { "$($modeText[$method.Mode]): $($method.Target)" } else { '-' }
        Ergebnis = ''
    }

    if (-not $method) {
        $row.Ergebnis = 'übersprungen (keine Startdatei erkannt)'
    } elseif ($Vorschau) {
        $row.Ergebnis = if (Test-Path -LiteralPath $exePath) { 'EXE vorhanden' } else { 'würde erstellt' }
    } elseif ((Test-Path -LiteralPath $exePath) -and -not $Force) {
        $row.Ergebnis = 'EXE vorhanden (mit -Force neu erstellen)'
    } else {
        try {
            New-StarterExe $project.Dir $method $exePath
            $row.Ergebnis = "$ExeName erstellt"
        } catch {
            $row.Ergebnis = "FEHLER: $($_.Exception.Message)"
        }
    }
    $row
}

if ($results) {
    $results | Format-Table -AutoSize -Wrap | Out-String -Width 300 | Write-Host
} else {
    Write-Host "Unter $Root wurde bis zur Tiefe $Tiefe kein Projekt gefunden."
    Write-Host 'Tipp: mit -Tiefe 6 tiefer suchen oder -Root auf einen Unterordner setzen.'
}
