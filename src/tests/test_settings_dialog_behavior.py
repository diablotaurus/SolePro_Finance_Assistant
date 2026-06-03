"""
UI behavior tests for SettingsDialog.
"""
from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QApplication, QDialogButtonBox, QLineEdit, QScrollArea, QSpinBox, QTabWidget

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytestmark = pytest.mark.ui


class _FakeUiSettings:
    def __init__(self, *args, **kwargs):
        self._values: dict[str, str] = {}

    def get_int(self, key: str, fallback: int) -> int:
        value = self._values.get(key)
        if value is None:
            return fallback
        try:
            return int(value)
        except ValueError:
            return fallback

    def get_str(self, key: str, fallback: str) -> str:
        return self._values.get(key, fallback)

    def set_int(self, key: str, value: int) -> None:
        self._values[key] = str(value)

    def set_str(self, key: str, value: str) -> None:
        self._values[key] = value

    def save(self) -> None:
        return None


def _build_wheel_event(widget, delta: int = 120) -> QWheelEvent:
    center = widget.rect().center()
    local_pos = QPointF(center)
    global_pos = QPointF(widget.mapToGlobal(center))
    return QWheelEvent(
        local_pos,
        global_pos,
        QPoint(0, 0),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate,
        False,
    )


def _make_dialog(monkeypatch):
    from solepro.presentation.desktop.views.dialogs import settings_dialog as settings_dialog_module

    monkeypatch.setattr(settings_dialog_module, "DesktopUiSettings", _FakeUiSettings)
    return settings_dialog_module.SettingsDialog()


def test_spinbox_wheel_without_focus_does_not_change_value(qtbot, monkeypatch):
    dialog = _make_dialog(monkeypatch)
    qtbot.add_widget(dialog)
    dialog.show()

    spinbox = dialog.main_window_width
    assert isinstance(spinbox, QSpinBox)
    initial_value = spinbox.value()

    # Keep focus away from spinbox and send wheel event to spinbox.
    focus_holder = dialog.findChild(QLineEdit)
    assert focus_holder is not None
    focus_holder.setFocus()
    QApplication.processEvents()
    assert not spinbox.hasFocus()

    event = _build_wheel_event(spinbox, delta=120)
    QApplication.sendEvent(spinbox, event)

    assert spinbox.value() == initial_value


def test_spinbox_wheel_with_focus_changes_value(qtbot, monkeypatch):
    dialog = _make_dialog(monkeypatch)
    qtbot.add_widget(dialog)
    dialog.show()

    spinbox = dialog.main_window_width
    initial_value = spinbox.value()
    spinbox.setFocus()
    QApplication.processEvents()
    assert spinbox.hasFocus()

    event = _build_wheel_event(spinbox, delta=120)
    QApplication.sendEvent(spinbox, event)

    assert spinbox.value() == initial_value + spinbox.singleStep()


def test_general_tab_uses_scroll_and_buttons_are_visible(qtbot, monkeypatch):
    dialog = _make_dialog(monkeypatch)
    qtbot.add_widget(dialog)
    dialog.show()

    tabs = dialog.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.tabText(0) == "Главное окно"

    general_scroll = dialog.findChild(QScrollArea)
    assert general_scroll is not None
    assert general_scroll.widgetResizable() is True

    buttons = dialog.findChild(QDialogButtonBox)
    assert buttons is not None
    save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
    cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
    assert save_button is not None and save_button.isVisible()
    assert cancel_button is not None and cancel_button.isVisible()


def test_totals_color_preview_updates_with_hex_input(qtbot, monkeypatch):
    dialog = _make_dialog(monkeypatch)
    qtbot.add_widget(dialog)
    dialog.show()

    field = dialog.totals_card_background
    preview = dialog._color_previews.get(field)
    assert preview is not None
    assert preview.width() == 30
    assert preview.height() == 30

    field.setText("#123abc")
    QApplication.processEvents()
    assert "#123abc" in preview.styleSheet()

    field.setText("invalid")
    QApplication.processEvents()
    assert "#ffffff" in preview.styleSheet()


def test_palette_color_preview_created_and_updates(qtbot, monkeypatch):
    dialog = _make_dialog(monkeypatch)
    qtbot.add_widget(dialog)
    dialog.show()

    field = dialog.color_income
    preview = dialog._color_previews.get(field)
    assert preview is not None
    assert preview.width() == 30
    assert preview.height() == 30

    field.setText("#00ff00")
    QApplication.processEvents()
    assert "#00ff00" in preview.styleSheet()
