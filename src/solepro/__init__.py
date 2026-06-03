"""
SolePro Finance Assistant - современная система учета финансов для ИП.

Основной пакет приложения, построенного на принципах Clean Architecture.
"""

try:
    from importlib.metadata import version as _pkg_version
except ImportError:  # pragma: no cover - Python < 3.8
    _pkg_version = None

__version__ = "unknown"
if _pkg_version is not None:
    try:
        __version__ = _pkg_version("solepro-finance-assistant")
    except Exception:
        __version__ = "unknown"

if __version__ == "unknown":
    try:
        from pathlib import Path
        import tomllib

        _project_root = Path(__file__).resolve().parents[2]
        _pyproject_path = _project_root / "pyproject.toml"
        if _pyproject_path.exists():
            _pyproject_data = tomllib.loads(_pyproject_path.read_text(encoding="utf-8"))
            __version__ = _pyproject_data.get("project", {}).get("version", "unknown")
    except Exception:
        __version__ = "unknown"
__author__ = "Diablotaurus"
__description__ = "Финансовый ассистент для индивидуальных предпринимателей"

# Note: avoid star-imports here to keep package import side-effect free.
