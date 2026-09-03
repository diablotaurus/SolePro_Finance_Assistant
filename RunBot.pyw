"""Run the Telegram bot without a console window on Windows."""
from __future__ import annotations

import os
import runpy
import site
import sys
from pathlib import Path


def _prepare_paths() -> None:
    project_root = Path(__file__).resolve().parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    venv_site = project_root / ".venv" / "Lib" / "site-packages"
    if venv_site.exists():
        site.addsitedir(str(venv_site))
    os.chdir(project_root)


def main() -> None:
    _prepare_paths()
    runpy.run_module("solepro.presentation.telegram.bot", run_name="__main__")


if __name__ == "__main__":
    main()
