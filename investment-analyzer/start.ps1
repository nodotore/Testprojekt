<#
.SYNOPSIS
    Startet den Investment-Analysator unter Windows.

.DESCRIPTION
    Legt bei Bedarf eine virtuelle Python-Umgebung an (.venv), installiert/
    aktualisiert die Abhängigkeiten, führt die Datenbankmigrationen aus
    (Alembic) und startet danach die deutschsprachige Streamlit-Oberfläche.
    Erfordert Python 3.12 oder neuer (Auftrag §4).

.PARAMETER Dev
    Installiert zusätzlich die Entwicklungsabhängigkeiten (pytest, ruff,
    mypy) statt nur der Laufzeitabhängigkeiten.

.PARAMETER SkipMigrate
    Überspringt den Alembic-Migrationsschritt (z. B. für schnelle
    Neustarts während der Entwicklung, wenn sich das Schema nicht
    geändert hat).

.EXAMPLE
    .\start.ps1
.EXAMPLE
    .\start.ps1 -Dev
#>

[CmdletBinding()]
param(
    [switch]$Dev,
    [switch]$SkipMigrate
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            $v = & py -3.12 --version 2>&1
            if ($LASTEXITCODE -eq 0 -and $v -match "Python 3\.(1[2-9]|[2-9]\d)") {
                return [pscustomobject]@{ Exe = "py"; Args = @("-3.12") }
            }
        } catch { }
    }
    foreach ($exe in @("python3.12", "python")) {
        $cmd = Get-Command $exe -ErrorAction SilentlyContinue
        if ($cmd) {
            try {
                $v = & $exe --version 2>&1
                if ($v -match "Python 3\.(1[2-9]|[2-9]\d)") {
                    return [pscustomobject]@{ Exe = $exe; Args = @() }
                }
            } catch { }
        }
    }
    return $null
}

Write-Host "== Investment-Analysator: Start ==" -ForegroundColor Cyan

$py = Get-PythonCommand
if (-not $py) {
    Write-Error @"
Python 3.12 oder neuer wurde nicht gefunden.
Bitte von https://www.python.org/downloads/ installieren
(beim Installer den Haken bei 'Add python.exe to PATH' setzen)
und dieses Skript danach erneut ausführen.
"@
    exit 1
}

$venvPath = Join-Path $PSScriptRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Lege virtuelle Python-Umgebung an: $venvPath"
    $pyArgs = @($py.Args) + @("-m", "venv", $venvPath)
    & $py.Exe @pyArgs
}

if (-not (Test-Path $venvPython)) {
    Write-Error "Virtuelle Umgebung konnte nicht angelegt werden ($venvPython fehlt)."
    exit 1
}

Write-Host "Installiere/aktualisiere Abhängigkeiten..."
& $venvPython -m pip install --upgrade pip --quiet
if ($Dev) {
    & $venvPython -m pip install -e ".[dev]" --quiet
} else {
    & $venvPython -m pip install -e . --quiet
}
if ($LASTEXITCODE -ne 0) {
    Write-Error "Installation der Abhängigkeiten ist fehlgeschlagen."
    exit 1
}

if (-not $SkipMigrate) {
    Write-Host "Führe Datenbankmigrationen aus (Alembic)..."
    & $venvPython -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Datenbankmigration ist fehlgeschlagen. Programmstart abgebrochen."
        exit 1
    }
} else {
    Write-Host "Migrationsschritt übersprungen (-SkipMigrate)." -ForegroundColor Yellow
}

Write-Host "Starte Investment-Analysator (Streamlit)..." -ForegroundColor Cyan
& $venvPython -m streamlit run "src/investment_analyzer/ui/app.py"
