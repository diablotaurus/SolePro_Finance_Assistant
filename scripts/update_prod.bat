@echo off
chcp 65001 >nul
title SolePro Finance Assistant - обновление прод-версии с GitHub
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update_prod.ps1" %*
echo.
pause
