@echo off
rem Doppelklick-Variante von Starter-erstellen.ps1 (umgeht die
rem PowerShell-Ausfuehrungsrichtlinie). Parameter werden durchgereicht,
rem z. B.:  Starter-erstellen.bat -Force
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Starter-erstellen.ps1" %*
pause
