"""
RunDesktopApp.pyw (без консоли, умный запуск)
Запуск десктопного приложения без консоли.
Расширение .pyw скрывает консоль в Windows.
"""
from __future__ import annotations

import os
import runpy
import site
import sys
import traceback
from pathlib import Path
from tkinter import Tk, messagebox


def _prepare_paths() -> Path:
    project_root = Path(__file__).resolve().parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    venv_site = project_root / ".venv" / "Lib" / "site-packages"
    if venv_site.exists():
        site.addsitedir(str(venv_site))
    os.chdir(project_root)
    return project_root


def _show_error(message: str) -> None:
    root = Tk()
    root.withdraw()
    messagebox.showerror("SolePro Desktop", message)
    root.destroy()


def main() -> None:
    _prepare_paths()
    try:
        runpy.run_module(
            "solepro.presentation.desktop.application",
            run_name="__main__",
        )
    except Exception:
        error_text = traceback.format_exc()
        _show_error(f"Не удалось запустить приложение.\n\n{error_text}")


if __name__ == "__main__":
    main()
