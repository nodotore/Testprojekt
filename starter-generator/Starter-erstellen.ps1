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

.PARAMETER Ausschliessen
    Ordnernamen (mit * als Platzhalter), die nicht durchsucht werden.
    Standard: Claude_Backup. Darin früher erzeugte Starten.exe werden entfernt.

.PARAMETER ExeName
    Dateiname der erzeugten Start-EXE. Standard: Starten.exe

.PARAMETER Force
    Auch eine fremde (große) Datei mit dem EXE-Namen überschreiben.
    Eigene Start-EXEs werden bei jedem Lauf ohnehin aktualisiert.

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
    [string[]]$Ausschliessen = @('Claude_Backup'),
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

# Hilfsskripte, die nie als Startskript gelten.
$helperScripts = '^(build|publish|install|setup|exe_bauen|test|clean|deploy)'

# Skripte, die nur einen Platzhalter enthalten, zählen nicht als Startdatei.
function Test-RealScript([string]$Path) {
    $code = [IO.File]::ReadAllText($Path)
    return -not ($code -match 'Kein automatischer Startbefehl')
}

function Get-StartScript([string]$Dir, [string[]]$Names, [string[]]$Extensions) {
    foreach ($n in $Names) {
        $p = Join-Path $Dir $n
        if ((Test-Path -LiteralPath $p -PathType Leaf) -and (Test-RealScript $p)) { return $n }
    }
    $files = @(Get-ChildItem -LiteralPath $Dir -File | Where-Object {
        $Extensions -contains $_.Extension.ToLowerInvariant() -and
        $_.BaseName -notmatch $helperScripts -and (Test-RealScript $_.FullName) })
    if ($files.Count -eq 1) { return $files[0].Name }
    return $null
}

# Code ohne Kommentare und Bildschirmausgaben (echo "python -m venv ..."
# in einer Fehlermeldung soll nicht als "legt venv selbst an" zählen).
function Get-ActiveCode([string]$Path) {
    return ([IO.File]::ReadAllLines($Path) | Where-Object {
        $_ -notmatch '^\s*(@?echo\b|Write-(Host|Output|Warning|Error)\b|#|rem\b|::)' }) -join "`n"
}

function Find-PythonStart([string]$Dir) {
    $name = Split-Path -Leaf $Dir

    $f = Get-FirstExisting $Dir @('app.py', 'main.py', 'streamlit_app.py', 'run_app.py', 'run.py', 'start.py', 'gui.py', "$name.py")
    if ($f) {
        $code = [IO.File]::ReadAllText((Join-Path $Dir $f))
        $mode = if ($code -match '(?m)^\s*(import\s+streamlit|from\s+streamlit\s+import)') { 'streamlit' } else { 'python' }
        return @{ Mode = $mode; Target = $f }
    }

    # Paket mit __main__.py (auch im src-Layout) -> python -m paket
    foreach ($base in @($Dir, (Join-Path $Dir 'src'))) {
        if (-not (Test-Path -LiteralPath $base -PathType Container)) { continue }
        $pkgs = @(Get-ChildItem -LiteralPath $base -Directory | Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName '__main__.py') })
        if ($pkgs.Count -eq 1) { return @{ Mode = 'module'; Target = $pkgs[0].Name } }
    }

    # Einstiegspunkt aus pyproject.toml ([project.scripts] / [project.gui-scripts])
    $pyproject = Join-Path $Dir 'pyproject.toml'
    if (Test-Path -LiteralPath $pyproject -PathType Leaf) {
        $toml = [IO.File]::ReadAllText($pyproject)
        foreach ($section in 'gui-scripts', 'scripts') {
            $m = [regex]::Match($toml, "(?ms)^\[project\.$section\]\s*\n(.*?)(^\[|\z)")
            if ($m.Success) {
                $e = [regex]::Match($m.Groups[1].Value, '(?m)^\s*[\w.-]+\s*=\s*["'']([\w.]+):(\w+)["'']')
                if ($e.Success) { return @{ Mode = 'entry'; Target = "$($e.Groups[1].Value):$($e.Groups[2].Value)" } }
            }
        }
    }

    # Einziges Paket (Ordner mit __init__.py, auch unter src\) mit main.py/app.py/gui.py
    # -> python -m paket.main
    foreach ($base in @($Dir, (Join-Path $Dir 'src'))) {
        if (-not (Test-Path -LiteralPath $base -PathType Container)) { continue }
        $pkgs = @(Get-ChildItem -LiteralPath $base -Directory | Where-Object {
            $_.Name -notmatch '^(tests?|docs?|build|dist)$' -and
            (Test-Path -LiteralPath (Join-Path $_.FullName '__init__.py')) })
        if ($pkgs.Count -eq 1) {
            foreach ($file in 'main', 'app', 'gui', 'cli') {
                if (Test-Path -LiteralPath (Join-Path $pkgs[0].FullName "$file.py")) {
                    return @{ Mode = 'module'; Target = "$($pkgs[0].Name).$file" }
                }
            }
        }
    }

    # main.py/app.py in einem Unterordner app\ oder src\ -> python -m app.main
    foreach ($sub in 'app', 'src') {
        foreach ($file in 'main', 'app', '__main__') {
            if (Test-Path -LiteralPath (Join-Path $Dir "$sub\$file.py") -PathType Leaf) {
                if ($file -eq '__main__') { return @{ Mode = 'module'; Target = $sub } }
                return @{ Mode = 'module'; Target = "$sub.$file" }
            }
        }
    }

    $files = @(Get-ChildItem -LiteralPath $Dir -File | Where-Object {
        '.py', '.pyw' -contains $_.Extension.ToLowerInvariant() -and
        $_.BaseName -notmatch '^(test_|scratch|conftest|setup$)' })
    if ($files.Count -eq 1) { return @{ Mode = 'python'; Target = $files[0].Name } }
    return $null
}

function Find-StartMethod([string]$Dir) {
    $name = Split-Path -Leaf $Dir

    $f = Get-StartScript $Dir @('start.ps1', 'starten.ps1', 'run.ps1', 'launch.ps1') @('.ps1')
    if ($f) { return @{ Mode = 'ps1'; Target = $f } }

    $f = Get-StartScript $Dir @('start.bat', 'start.cmd', 'starten.bat', 'starten.cmd', 'run.bat', 'run.cmd') @('.bat', '.cmd')
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

    $py = Find-PythonStart $Dir
    if ($py) { return $py }

    $f = Get-FirstExisting $Dir @('index.html', 'index.htm')
    if (-not $f) { $f = Get-Single $Dir @('.html', '.htm') }
    if ($f) { return @{ Mode = 'open'; Target = $f } }

    # Fertiges Programm in Programm\ oder dist\ (z. B. mit PyInstaller gebaut)
    foreach ($sub in 'Programm', 'dist') {
        $subDir = Join-Path $Dir $sub
        if (-not (Test-Path -LiteralPath $subDir -PathType Container)) { continue }
        $exes = @(Get-ChildItem -LiteralPath $subDir -Filter '*.exe' -File -Recurse -Depth 1 -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ne $ExeName -and $_.Name -notmatch '^(unins|setup|install)' })
        if ($exes.Count -eq 1) {
            return @{ Mode = 'open'; Target = $exes[0].FullName.Substring($Dir.TrimEnd('\').Length + 1) }
        }
    }

    return $null
}

# Wie viel sich die EXE um die Python-Umgebung (.venv) kümmern soll.
function Get-SetupLevel([string]$Dir, [hashtable]$Method) {
    $isPython = (Test-Path -LiteralPath (Join-Path $Dir 'requirements.txt')) -or
                (Test-Path -LiteralPath (Join-Path $Dir 'pyproject.toml'))
    if ($Method.Mode -in 'python', 'streamlit', 'module', 'entry') {
        if ($isPython) { return 'full' } else { return 'none' }
    }
    if ($Method.Mode -in 'ps1', 'bat') {
        $code = Get-ActiveCode (Join-Path $Dir $Method.Target)
        if ($code -notmatch 'venv') { return 'none' }
        # Mit requirements.txt/pyproject.toml: Umgebung samt Paketen sicherstellen
        # (manche Skripte legen die .venv an, installieren aber nichts).
        # Sonst nur eine defekte .venv entfernen, damit das Skript sie neu anlegt.
        if ($isPython) { return 'full' } else { return 'repair' }
    }
    return 'none'
}

function ConvertTo-CSharpLiteral([string]$s) {
    return $s.Replace('\', '\\').Replace('"', '\"')
}

function New-StarterExe([string]$Dir, [hashtable]$Method, [string]$ExePath) {
    $source = $template.Replace('@@MODE@@', (ConvertTo-CSharpLiteral $Method.Mode))
    $source = $source.Replace('@@TARGET@@', (ConvertTo-CSharpLiteral $Method.Target))
    $source = $source.Replace('@@TITLE@@', (ConvertTo-CSharpLiteral (Split-Path -Leaf $Dir)))
    $source = $source.Replace('@@SETUP@@', $Method.Setup)
    $source = $source.Replace('@@ASKFILE@@', $(if ($Method.AskFile) { '1' } else { '0' }))

    $work = Join-Path ([IO.Path]::GetTempPath()) ('starter_' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $work | Out-Null
    try {
        $srcFile = Join-Path $work 'Launcher.cs'
        $tmpExe = Join-Path $work 'Starter.exe'
        [IO.File]::WriteAllText($srcFile, $source, (New-Object Text.UTF8Encoding($true)))

        # Webseiten ohne Konsolenfenster öffnen, alles andere mit Konsole,
        # damit Ausgaben und Fehlermeldungen sichtbar sind.
        $kind = if ($Method.Mode -eq 'open') { 'winexe' } else { 'exe' }
        $cscArgs = @('/nologo', '/optimize+', '/nowarn:162,429', "/target:$kind",
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

# Entfernt in ausgeschlossenen Ordnern die früher erzeugten Start-EXEs
# (nur Dateien mit dem EXE-Namen, die klein genug für einen Starter sind).
function Remove-OldStarters([string]$Dir) {
    Get-ChildItem -LiteralPath $Dir -Filter $ExeName -File -Recurse -Depth 6 -ErrorAction SilentlyContinue |
        Where-Object { $_.Length -lt 64KB } | ForEach-Object {
            if ($Vorschau) {
                Write-Host "Würde entfernt (ausgeschlossener Ordner): $($_.FullName)"
            } else {
                Remove-Item -LiteralPath $_.FullName -Force
                Write-Host "Entfernt (ausgeschlossener Ordner): $($_.FullName)"
            }
        }
}

function Find-Projects([string]$Dir, [int]$Depth) {
    $children = Get-ChildItem -LiteralPath $Dir -Directory -ErrorAction SilentlyContinue | Sort-Object Name
    foreach ($child in $children) {
        if (@($Ausschliessen | Where-Object { $child.Name -like $_ }).Count) {
            Remove-OldStarters $child.FullName
            continue
        }
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
    module    = 'Python-Modul'
    entry     = 'Python-Einstieg'
    open      = 'öffnen'
}

Write-Host "Grundordner: $Root"
Write-Host ''

$results = foreach ($project in Find-Projects $Root 1) {
    $method = $project.Method
    if ($method) {
        $method.Setup = Get-SetupLevel $project.Dir $method
        # Skript erwartet eine Datei als Argument (Drag & Drop auf die .bat)?
        if ($method.Mode -in 'bat', 'ps1') {
            $code = Get-ActiveCode (Join-Path $project.Dir $method.Target)
            $method.AskFile = $code -match '%~?1|\$args\[0\]'
        }
    }
    $exePath = Join-Path $project.Dir $ExeName
    $row = [pscustomobject]@{
        Projekt  = $project.Dir.Substring($Root.TrimEnd('\').Length).TrimStart('\', '/')
        Startart = if ($method) {
            "$($modeText[$method.Mode]): $($method.Target)" + $(if ($method.AskFile) { ' (fragt nach Datei)' }) + $(switch ($method.Setup) {
                'full' { ' (+ .venv einrichten)' } 'repair' { ' (+ defekte .venv reparieren)' } default { '' } })
        } else { '-' }
        Ergebnis = ''
    }

    if (-not $method) {
        $row.Ergebnis = 'übersprungen (keine Startdatei erkannt)'
        # Eine früher erzeugte EXE würde sonst mit veralteter Startart weiterlaufen.
        if ((Test-Path -LiteralPath $exePath) -and (Get-Item -LiteralPath $exePath).Length -lt 64KB) {
            if (-not $Vorschau) { Remove-Item -LiteralPath $exePath -Force }
            $row.Ergebnis += ', alte EXE entfernt'
        }
    } elseif ($Vorschau) {
        $row.Ergebnis = if (Test-Path -LiteralPath $exePath) { 'EXE vorhanden' } else { 'würde erstellt' }
    } elseif ((Test-Path -LiteralPath $exePath) -and -not $Force -and (Get-Item -LiteralPath $exePath).Length -ge 64KB) {
        # Große Datei gleichen Namens stammt nicht von diesem Werkzeug.
        $row.Ergebnis = 'fremde EXE gleichen Namens vorhanden (mit -Force überschreiben)'
    } else {
        try {
            $existed = Test-Path -LiteralPath $exePath
            New-StarterExe $project.Dir $method $exePath
            $row.Ergebnis = if ($existed) { "$ExeName aktualisiert" } else { "$ExeName erstellt" }
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
