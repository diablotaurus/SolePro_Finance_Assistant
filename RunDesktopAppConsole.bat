@echo off
setlocal
set "ROOT=%~dp0"
if exist "%ROOT%.venv\Scripts\python.exe" (
  "%ROOT%.venv\Scripts\python.exe" "%ROOT%scripts\run_desktop.py"
) else (
  python "%ROOT%scripts\run_desktop.py"
)

:end
echo.
pause