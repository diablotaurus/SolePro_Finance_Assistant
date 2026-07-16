"""
Менеджер контрагентов.
"""
from typing import List, Optional
from uuid import UUID

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHeaderView,
)

from .counterparty_dialog import CounterpartyDialog
from ...controllers.main_controller import MainController
from ...ui_settings import DesktopUiSettings, TableUiConfigurator
from .....core.application.dto.counterparty_dto import CounterpartyResponseDTO


class CounterpartyManagerDialog(QDialog):
    """
    Диалог управления контрагентами.
    """

    def __init__(self, controller: MainController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.counterparties: List[CounterpartyResponseDTO] = []
        self.ui_settings = DesktopUiSettings(__file__, project_root_parent_index=6)
        self.table_ui = TableUiConfigurator(self.ui_settings)
        self.setup_ui()
        self.load_data()

    def setup_ui(self) -> None:
        self.setWindowTitle("Контрагенты")
        self.setMinimumSize(
            self.ui_settings.get_int("dialog_counterparty_manager_min_width", 900),
            self.ui_settings.get_int("dialog_counterparty_manager_min_height", 500),
        )

        layout = QVBoxLayout(self)

        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Введите имя или описание")
        search_layout.addWidget(self.search_edit)

        self.search_btn = QPushButton("Найти")
        self.search_btn.clicked.connect(self.on_search)
        search_layout.addWidget(self.search_btn)

        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.clicked.connect(self.on_clear)
        search_layout.addWidget(self.clear_btn)

        layout.addLayout(search_layout)

        # Таблица
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Наименование контрагента", "Транзакции", "Сумма", "Контакты"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        contacts_width = self.ui_settings.get_int(
            "counterparty_contacts_column_width",
            170
        )
        self.table.setColumnWidth(3, contacts_width)
        self.table.doubleClicked.connect(self.on_edit)
        layout.addWidget(self.table)

        self.table_ui.apply_vertical_header(self.table, "counterpartyVerticalHeader")
        self.table_ui.apply_row_heights(
            self.table,
            row_padding_fallback=16,
        )

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.on_add)
        buttons_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("Редактировать")
        self.edit_btn.clicked.connect(self.on_edit)
        buttons_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.on_delete)
        buttons_layout.addWidget(self.delete_btn)

        buttons_layout.addStretch()

        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.load_data)
        buttons_layout.addWidget(self.refresh_btn)

        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_btn)

        layout.addLayout(buttons_layout)

    def load_data(self, search_query: Optional[str] = None) -> None:
        result = self.controller.load_counterparties(search_query=search_query)
        self.counterparties = result.counterparties
        self.table.setRowCount(len(self.counterparties))

        for row, counterparty in enumerate(self.counterparties):
            self.table.setItem(row, 0, QTableWidgetItem(counterparty.name))
            self.table.setItem(row, 1, QTableWidgetItem(str(counterparty.transaction_count)))
            self.table.setItem(row, 2, QTableWidgetItem(f"{counterparty.total_income:,.2f}"))
            contact = counterparty.contact_info or ""
            self.table.setItem(row, 3, QTableWidgetItem(contact))

        self.table_ui.apply_row_heights(
            self.table,
            row_padding_fallback=16,
        )

    def get_selected_counterparty(self) -> Optional[CounterpartyResponseDTO]:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.counterparties):
            return None
        return self.counterparties[row]

    def on_search(self) -> None:
        query = self.search_edit.text().strip()
        self.load_data(search_query=query or None)

    def on_clear(self) -> None:
        self.search_edit.clear()
        self.load_data()

    def on_add(self) -> None:
        dialog = CounterpartyDialog(parent=self)
        dialog.counterparty_saved.connect(self.on_counterparty_saved)
        dialog.exec()

    def on_edit(self) -> None:
        counterparty = self.get_selected_counterparty()
        if not counterparty:
            QMessageBox.warning(self, "Предупреждение", "Выберите контрагента для редактирования")
            return
        dialog = CounterpartyDialog(counterparty=counterparty, parent=self)
        dialog.counterparty_saved.connect(self.on_counterparty_saved)
        dialog.exec()

    def on_delete(self) -> None:
        counterparty = self.get_selected_counterparty()
        if not counterparty:
            QMessageBox.warning(self, "Предупреждение", "Выберите контрагента для удаления")
            return
        message = f"Удалить контрагента '{counterparty.name}'?"
        if counterparty.transaction_count > 0:
            message += (
                f"\n\nУ контрагента {counterparty.transaction_count} транзакц.: "
                "они сохранятся, но останутся без контрагента."
            )
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        success = self.controller.delete_counterparty(UUID(str(counterparty.id)))
        if success:
            self.load_data()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось удалить контрагента")

    def on_counterparty_saved(self, data: dict) -> None:
        counterparty_data = data["data"]
        is_edit = data["is_edit"]
        if is_edit:
            counterparty_id = data["counterparty_id"]
            self.controller.update_counterparty(UUID(str(counterparty_id)), counterparty_data)
        else:
            self.controller.add_counterparty(counterparty_data)
        self.load_data()
