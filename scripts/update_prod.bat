@echo off
"%SystemRoot%\System32\chcp.com" 65001 >nul 2>&1
title SolePro Finance Assistant - Update from GitHub
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0update_prod.ps1" %*
echo.
pause
