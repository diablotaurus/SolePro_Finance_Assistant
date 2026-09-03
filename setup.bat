@echo off
"%SystemRoot%\System32\chcp.com" 65001 >nul 2>&1
title SolePro Finance Assistant - Setup
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1" %*
echo.
pause
