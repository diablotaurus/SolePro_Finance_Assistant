@echo off
"%SystemRoot%\System32\chcp.com" 65001 >nul 2>&1
title SolePro Finance Assistant - Update from GitHub
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update_prod.ps1" %*
echo.
pause
