# RunDesktopApp_Diag.py (с диагностикой)
from pathlib import Path
import sys
import traceback
import os

def setup_paths():
    """Настройка путей с диагностикой"""
    try:
        # Получаем корень проекта
        project_root = Path(__file__).parent
        print(f"Текущий скрипт: {__file__}")
        print(f"Корень проекта: {project_root}")
        print(f"Рабочая директория: {os.getcwd()}")
        
        # Добавляем путь к проекту
        sys.path.append(str(project_root))
        print("Пути Python:")
        for p in sys.path:
            print(f"  - {p}")
        print("-" * 50)
        
        return project_root
    except Exception as e:
        print(f"Ошибка при настройке путей: {e}")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
        sys.exit(1)

def run_application():
    """Запуск приложения с обработкой ошибок"""
    try:
        print("Импортируем модули...")
        from desktop.main import main
        
        print("Запускаем приложение...")
        main()
        
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("\nПроверьте пути импорта:")
        print(f"1. desktop.main существует? {Path(__file__).parent / 'desktop' / 'main.py'}")
        print(f"2. desktop.main.py содержит функцию main?")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
        
    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    # Настраиваем пути
    setup_paths()
    
    # Запускаем приложение
    run_application()