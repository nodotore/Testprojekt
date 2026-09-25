@echo off
rem Prueft jedes Projekt einzeln und schreibt Diagnose.txt.
rem Parameter werden durchgereicht, z. B.:  Diagnose.bat -Sekunden 30
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Diagnose.ps1" %*
pause
