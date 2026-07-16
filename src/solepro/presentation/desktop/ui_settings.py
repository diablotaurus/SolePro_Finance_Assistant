"""
UI settings helpers for desktop presentation layer.
"""
from __future__ import annotations

import configparser
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QTableWidget


class DesktopUiSettings:
    """Provides access to values from settings/settings.ini."""

    def __init__(self, module_file: str, project_root_parent_index: int):
        self._config = configparser.ConfigParser()
        self._settings_path = self._resolve_settings_path(
            module_file=module_file,
            project_root_parent_index=project_root_parent_index,
        )
        if self._settings_path.exists():
            self._config.read(self._settings_path, encoding="utf-8")
        if "ui" not in self._config:
            self._config["ui"] = {}

    def get_int(self, key: str, fallback: int) -> int:
        return self._config.getint("ui", key, fallback=fallback)

    def get_str(self, key: str, fallback: str) -> str:
        return self._config.get("ui", key, fallback=fallback)

    def set_int(self, key: str, value: int) -> None:
        self._config["ui"][key] = str(value)

    def set_str(self, key: str, value: str) -> None:
        self._config["ui"][key] = value

    def save(self) -> None:
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        with self._settings_path.open("w", encoding="utf-8") as settings_file:
            self._config.write(settings_file)

    @staticmethod
    def _resolve_settings_path(module_file: str, project_root_parent_index: int) -> Path:
        resolved = Path(module_file).resolve()

        # Основной способ: подняться до корня проекта по маркеру
        # pyproject.toml — устойчиво к переносу модулей между подпапками.
        for parent in resolved.parents:
            if (parent / "pyproject.toml").exists():
                candidate = parent / "settings" / "settings.ini"
                if candidate.exists():
                    return candidate
                break

        # Фолбэк: исторический фиксированный индекс родителя.
        parents = resolved.parents
        if project_root_parent_index < len(parents):
            settings_path = parents[project_root_parent_index] / "settings" / "settings.ini"
            if settings_path.exists():
                return settings_path

        return Path.cwd() / "settings" / "settings.ini"


class TableUiConfigurator:
    """Applies shared table UI settings to QTableWidget instances."""

    def __init__(self, settings: DesktopUiSettings):
        self._settings = settings

    def apply_vertical_header(
        self,
        table: QTableWidget,
        object_name: str,
        font_family_key: str = "table_header_font_family",
        font_family_fallback: str = "Segoe UI",
        font_size_key: str = "vertical_header_font_size",
        font_size_fallback: int = 11,
        width_key: str = "vertical_header_width",
        width_fallback: int = 36,
    ) -> None:
        font_family = self._settings.get_str(font_family_key, font_family_fallback)
        font_size = self._settings.get_int(font_size_key, font_size_fallback)
        header = table.verticalHeader()
        header_font = header.font()
        header_font.setFamily(font_family)
        header_font.setPointSize(font_size)
        header.setFont(header_font)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setObjectName(object_name)
        header.setStyleSheet(
            (
                f'QHeaderView#{object_name} {{ '
                f"background-color: transparent; "
                f"border: none; "
                f"}} "
                f'QHeaderView#{object_name}::section {{ '
                f'font-family: "{font_family}"; '
                f"font-size: {font_size}pt; "
                f"}}"
            )
        )
        width = self._settings.get_int(width_key, width_fallback)
        header.setFixedWidth(width)

    def apply_row_heights(
        self,
        table: QTableWidget,
        row_padding_key: str = "vertical_header_row_padding",
        row_padding_fallback: int = 28,
    ) -> None:
        header_metrics = QFontMetrics(table.verticalHeader().font())
        row_padding = self._settings.get_int(row_padding_key, row_padding_fallback)
        row_height = header_metrics.height() + row_padding
        table.verticalHeader().setMinimumSectionSize(row_height)
        table.verticalHeader().setDefaultSectionSize(row_height)
