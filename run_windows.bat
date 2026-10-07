@echo off
REM ==============================================================================
REM J.A.R.V.I.S. AI OS — Windows 1-Click Starter Batch (run_windows.bat)
REM Delegiert die Ausführung an den intelligenten Python/WSL2 Orchestrator run_windows.py
REM ==============================================================================

chcp 65001 >nul
title J.A.R.V.I.S. AI OS - Windows Starter

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python run_windows.py %*
    goto end
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py run_windows.py %*
    goto end
)

echo [!] Kein Python auf dem Windows-Host gefunden.
echo [*] Versuche direkten Start über WSL...
wsl -e bash -c "cd $(wslpath -a -u '%~dp0') && ./run.sh %*"

:end
