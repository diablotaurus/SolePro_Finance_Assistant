"""
Tests for desktop UI settings helpers.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QTableWidget

from solepro.presentation.desktop.ui_settings import DesktopUiSettings, TableUiConfigurator


def test_desktop_ui_settings_reads_existing_project_settings(tmp_path):
    project_root = tmp_path / "project"
    module_dir = project_root / "src" / "module"
    module_dir.mkdir(parents=True, exist_ok=True)
    module_file = module_dir / "fake_module.py"
    module_file.write_text("# test", encoding="utf-8")

    settings_dir = project_root / "settings"
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_file = settings_dir / "settings.ini"
    settings_file.write_text("[ui]\nmain_window_width = 1777\n", encoding="utf-8")

    settings = DesktopUiSettings(str(module_file), project_root_parent_index=2)

    assert settings.get_int("main_window_width", 1400) == 1777


def test_desktop_ui_settings_fallback_to_cwd_and_save(tmp_path, monkeypatch):
    cwd = tmp_path / "runtime"
    cwd.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(cwd)

    module_file = tmp_path / "external" / "fake_module.py"
    module_file.parent.mkdir(parents=True, exist_ok=True)
    module_file.write_text("# test", encoding="utf-8")

    settings = DesktopUiSettings(str(module_file), project_root_parent_index=1)
    settings.set_int("main_window_height", 901)
    settings.set_str("table_font_family", "Segoe UI")
    settings.save()

    saved_path = cwd / "settings" / "settings.ini"
    assert saved_path.exists()

    content = saved_path.read_text(encoding="utf-8")
    assert "[ui]" in content
    assert "main_window_height = 901" in content
    assert "table_font_family = Segoe UI" in content

    loaded = DesktopUiSettings(str(module_file), project_root_parent_index=1)
    assert loaded.get_int("main_window_height", 800) == 901
    assert loaded.get_str("table_font_family", "Default") == "Segoe UI"


class _SettingsStub:
    def __init__(self):
        self.values = {
            "table_header_font_family": "Segoe UI",
            "vertical_header_font_size": 12,
            "vertical_header_width": 44,
            "vertical_header_row_padding": 20,
        }

    def get_str(self, key, fallback):
        return self.values.get(key, fallback)

    def get_int(self, key, fallback):
        return self.values.get(key, fallback)


def test_table_ui_configurator_applies_vertical_header(qapp):
    table = QTableWidget(3, 2)
    configurator = TableUiConfigurator(_SettingsStub())

    configurator.apply_vertical_header(table, object_name="test_vertical_header")

    header = table.verticalHeader()
    assert header.objectName() == "test_vertical_header"
    assert header.font().family() == "Segoe UI"
    assert header.font().pointSize() == 12
    assert header.defaultAlignment() == Qt.AlignmentFlag.AlignCenter
    assert header.width() == 44


def test_table_ui_configurator_applies_row_heights(qapp):
    table = QTableWidget(2, 2)
    configurator = TableUiConfigurator(_SettingsStub())
    configurator.apply_vertical_header(table, object_name="test_vertical_header")

    metrics = QFontMetrics(table.verticalHeader().font())
    expected = metrics.height() + 20
    configurator.apply_row_heights(table)

    header = table.verticalHeader()
    assert header.minimumSectionSize() == expected
    assert header.defaultSectionSize() == expected

