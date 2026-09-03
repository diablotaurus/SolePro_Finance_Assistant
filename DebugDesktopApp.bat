@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"
if exist "%ROOT%.venv\Scripts\python.exe" (
    "%ROOT%.venv\Scripts\python.exe" "%ROOT%scripts\run_desktop.py"
) else (
    py -3.13 "%ROOT%scripts\run_desktop.py"
)
pause
