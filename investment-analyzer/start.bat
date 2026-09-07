@echo off
REM Investment-Analysator: einfacher Doppelklick-Start unter Windows.
REM Ruft start.ps1 mit gelockerter Ausführungsrichtlinie NUR für diesen
REM Prozess auf (ändert keine dauerhaften Systemeinstellungen).

setlocal
set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start.ps1" %*
if errorlevel 1 (
    echo.
    echo Der Start ist fehlgeschlagen. Siehe Meldungen oben.
    pause
)
endlocal
