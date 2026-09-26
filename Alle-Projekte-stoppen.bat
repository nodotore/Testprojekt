@echo off
REM Doppelklick-Stopp fuer alle Projekte unter Windows.

setlocal
set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Alle-Projekte-stoppen.ps1" %*
if errorlevel 1 (
    echo.
    echo Das Stoppen ist fehlgeschlagen. Siehe Meldungen oben.
    pause
)
endlocal
