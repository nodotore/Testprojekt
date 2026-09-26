@echo off
REM Doppelklick-Start fuer alle Projekte unter Windows.
REM Ruft Alle-Projekte-starten.ps1 mit gelockerter Ausfuehrungsrichtlinie
REM NUR fuer diesen Prozess auf (aendert keine dauerhaften Systemeinstellungen).

setlocal
set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Alle-Projekte-starten.ps1" %*
if errorlevel 1 (
    echo.
    echo Der Start ist fehlgeschlagen. Siehe Meldungen oben.
    pause
)
endlocal
