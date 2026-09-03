"""
Smoke тесты для Desktop UI.
"""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from solepro.core.application.dto.counterparty_dto import CounterpartyListDTO
from solepro.core.application.dto.statistics_dto import StatisticsDTO
from solepro.core.application.dto.transaction_dto import TransactionListDTO
from solepro.presentation.desktop.controllers.coordinators import (
    CounterpartyCoordinator,
    TransactionCoordinator,
)
from solepro.presentation.desktop.controllers.main_controller import MainController

pytestmark = pytest.mark.ui


class _DummyUseCase:
    def __init__(self, result=None):
        self._result = result

    def execute(self, *args, **kwargs):
        return self._result


class _DummyExportService:
    def export_to_excel(self, transactions, filepath):
        return None


def _build_controller() -> MainController:
    transaction_coordinator = TransactionCoordinator(
        add_transaction_use_case=_DummyUseCase(),
        update_transaction_use_case=_DummyUseCase(),
        delete_transaction_use_case=_DummyUseCase(),
        get_transaction_use_case=_DummyUseCase(),
        list_transactions_use_case=_DummyUseCase(TransactionListDTO()),
        search_transactions_use_case=_DummyUseCase(TransactionListDTO()),
        get_transaction_statistics_use_case=_DummyUseCase(StatisticsDTO()),
    )
    counterparty_coordinator = CounterpartyCoordinator(
        add_counterparty_use_case=_DummyUseCase(),
        update_counterparty_use_case=_DummyUseCase(),
        delete_counterparty_use_case=_DummyUseCase(),
        list_counterparties_use_case=_DummyUseCase(CounterpartyListDTO()),
        search_counterparties_use_case=_DummyUseCase(CounterpartyListDTO()),
        get_counterparty_statistics_use_case=_DummyUseCase([]),
    )
    return MainController(
        transaction_coordinator=transaction_coordinator,
        counterparty_coordinator=counterparty_coordinator,
        transaction_export_service=_DummyExportService(),
    )


def test_main_window_smoke(qtbot, qapp, monkeypatch):
    """Тест главного окна с использованием qtbot из pytest-qt"""
    from solepro.presentation.desktop.main_window import MainWindow
    from PyQt6.QtWidgets import QMessageBox

    monkeypatch.setattr(MainWindow, "load_initial_data", lambda self: None)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    controller = _build_controller()
    window = MainWindow(controller)
    
    # Добавляем окно в qtbot для управления
    qtbot.add_widget(window)
    
    # Показываем окно и ждем немного
    window.show()
    qtbot.wait(100)  # Ждем 100 мс
    
    # Закрываем окно
    window.close()
    
    # Убеждаемся, что окно закрыто
    assert window.isHidden()


def test_dialogs_smoke(qtbot, qapp):
    """Тест диалогов с использованием qtbot из pytest-qt"""
    from solepro.presentation.desktop.views.dialogs.counterparty_dialog import CounterpartyDialog
    from solepro.presentation.desktop.views.dialogs.counterparty_manager_dialog import (
        CounterpartyManagerDialog,
    )
    from solepro.presentation.desktop.views.dialogs.transaction_dialog import TransactionDialog

    # Тестируем CounterpartyDialog
    dialog = CounterpartyDialog()
    qtbot.add_widget(dialog)
    dialog.show()
    qtbot.wait(50)
    dialog.close()
    
    # Тестируем TransactionDialog
    transaction_dialog = TransactionDialog()
    qtbot.add_widget(transaction_dialog)
    transaction_dialog.show()
    qtbot.wait(50)
    transaction_dialog.close()
    
    # Тестируем CounterpartyManagerDialog
    controller = _build_controller()
    manager_dialog = CounterpartyManagerDialog(controller)
    qtbot.add_widget(manager_dialog)
    manager_dialog.show()
    qtbot.wait(50)
    manager_dialog.close()


def test_edit_dialogs_can_clear_optional_text(qtbot, qapp):
    from datetime import datetime
    from decimal import Decimal
    from uuid import uuid4

    from solepro.core.application.dto.counterparty_dto import CounterpartyResponseDTO
    from solepro.core.application.dto.transaction_dto import TransactionResponseDTO
    from solepro.presentation.desktop.views.dialogs.counterparty_dialog import CounterpartyDialog
    from solepro.presentation.desktop.views.dialogs.transaction_dialog import TransactionDialog

    now = datetime.now()
    counterparty = CounterpartyResponseDTO(
        id=uuid4(),
        name="Test",
        description="Old description",
        contact_info="Old contact",
        created_at=now,
        updated_at=now,
    )
    counterparty_dialog = CounterpartyDialog(counterparty=counterparty)
    qtbot.add_widget(counterparty_dialog)
    counterparty_dialog.description_edit.clear()
    counterparty_dialog.contact_edit.clear()

    counterparty_dto = counterparty_dialog.get_counterparty_data()

    assert counterparty_dto.description == ""
    assert counterparty_dto.contact_info == ""

    transaction = TransactionResponseDTO(
        id=uuid4(),
        date=now,
        income=Decimal("10"),
        expense=Decimal("0"),
        tax=Decimal("0"),
        profit=Decimal("10"),
        note="Old note",
        created_at=now,
        updated_at=now,
    )
    transaction_dialog = TransactionDialog(transaction=transaction)
    qtbot.add_widget(transaction_dialog)
    transaction_dialog.note_edit.clear()

    transaction_dto = transaction_dialog.get_transaction_data()

    assert transaction_dto.note == ""
