:: setup.bat - установка зависимостей для всех версий Python
@echo off
chcp 65001 > nul
echo ========================================
echo        Установка зависимостей для 
echo        SolePro Finance Assistant
echo ========================================
echo.

echo Устанавливаем для Python 3.13 (основная версия)...
py -3.13 -m pip install -r requirements.txt

echo.
echo Устанавливаем для Python 3.14 (на случай запуска по умолчанию)...
py -3.14 -m pip install -r requirements.txt

echo.
echo Готово!
echo.
echo Теперь можно запустить приложение:
echo - Двойной клик по RunDesktopApp.pyw (без консоли)
echo - Или запустите DebugDesktopApp.bat (с консолью)
echo.
pause