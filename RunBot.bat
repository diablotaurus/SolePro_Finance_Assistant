@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PYTHONPATH=%ROOT%src"
if exist "%ROOT%.venv\Scripts\python.exe" (
  "%ROOT%.venv\Scripts\python.exe" -m solepro.presentation.telegram.bot
) else (
  python -m solepro.presentation.telegram.bot
)
pause
