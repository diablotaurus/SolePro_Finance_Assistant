:: DebugDesktopApp.bat (с консолью для отладки)
@echo off
chcp 65001 > nul
echo ========================================
echo Запуск SolePro Finance Assistant (Отладка)
echo ========================================
echo.

:: Проверяем наличие Python 3.13
where python3.13 >nul 2>nul
if %errorlevel% equ 0 (
    echo Используется Python 3.13...
    python3.13 desktop/main.py
    goto :end
)

:: Используем py launcher
echo Используем py launcher для Python 3.13...
py -3.13 desktop/main.py

:end
echo.
pause