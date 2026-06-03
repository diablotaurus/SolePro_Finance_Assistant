"""
Таблица для отображения транзакций.
"""
from typing import List, Optional

from PyQt6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMenu,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction, QFont

from .....core.application.dto.transaction_dto import TransactionResponseDTO
from ...ui_settings import DesktopUiSettings, TableUiConfigurator


class SortableTableWidgetItem(QTableWidgetItem):
    """Table item with explicit sort value."""

    def __init__(self, text: str, sort_value):
        super().__init__(text)
        self._sort_value = sort_value

    def __lt__(self, other) -> bool:
        if isinstance(other, SortableTableWidgetItem):
            return self._sort_value < other._sort_value
        return super().__lt__(other)


class TransactionTableView(QTableWidget):
    """
    Таблица для отображения транзакций.
    
    Сигналы:
        transaction_selected: Транзакция выбрана
        transaction_double_clicked: Двойной клик по транзакции
        context_menu_requested: Запрос контекстного меню
    """
    
    transaction_selected = pyqtSignal(str)  # transaction_id
    transaction_double_clicked = pyqtSignal(str)  # transaction_id
    context_menu_requested = pyqtSignal(str, dict)  # transaction_id, position
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transactions: List[TransactionResponseDTO] = []
        self.ui_settings = DesktopUiSettings(__file__, project_root_parent_index=6)
        self.table_ui = TableUiConfigurator(self.ui_settings)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Настроить UI таблицы."""
        # Настройки таблицы
        self.setColumnCount(7)  # Дата, Доход, Расход, Налог, Прибыль, Контрагент, Примечание
        self.setHorizontalHeaderLabels([
            "Дата",
            "Доход",
            "Расход", 
            "Налог",
            "Прибыль",
            "Контрагент",
            "Примечание"
        ])
        
        # Внешний вид
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSortingEnabled(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Заголовки
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Дата
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Доход
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Расход
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Налог
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Прибыль
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Контрагент
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)  # Примечание
        header.setStretchLastSection(True)

        counterparty_width = self.ui_settings.get_int(
            "transactions_column_counterparty_width",
            220
        )
        note_width = self.ui_settings.get_int(
            "transactions_column_note_width",
            300
        )
        self.setColumnWidth(5, counterparty_width)
        self.setColumnWidth(6, note_width)

        # Шрифт вертикального заголовка (номера строк)
        self.table_ui.apply_vertical_header(self, "transactionVerticalHeader")

        # Высота строк по умолчанию (чтобы номера строк не обрезались)
        self.table_ui.apply_row_heights(self)
        
        # Контекстное меню
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Сигналы
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.itemDoubleClicked.connect(self.on_double_click)
    
    def load_transactions(self, transactions: List[TransactionResponseDTO]) -> None:
        """
        Загрузить транзакции в таблицу.
        
        Args:
            transactions: Список транзакций
        """
        self.transactions = transactions
        
        # Временно отключаем сортировку для быстрой загрузки
        self.setSortingEnabled(False)
        self.clearSpans()
        
        # Очищаем таблицу
        self.clearContents()
        self.setRowCount(len(transactions))
        
        if not transactions:
            self.setRowCount(1)
            item = QTableWidgetItem("Нет данных для отображения")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(0, 0, item)
            self.setSpan(0, 0, 1, 7)
            self.setSortingEnabled(True)
            return

        income_color = self.ui_settings.get_str("color_income", "#2e7d32")
        expense_color = self.ui_settings.get_str("color_expense", "#c62828")
        tax_color = self.ui_settings.get_str("color_tax", "#1565c0")
        profit_positive_color = self.ui_settings.get_str("color_profit_positive", "#2e7d32")
        profit_negative_color = self.ui_settings.get_str("color_profit_negative", "#c62828")
        profit_positive_bg = self.ui_settings.get_str("totals_card_background", "#c8e6c9")
        
        # Заполняем таблицу
        for row, transaction in enumerate(transactions):
            # Дата
            date_item = SortableTableWidgetItem(
                transaction.date.strftime("%d.%m.%Y"),
                transaction.date,
            )
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            date_item.setData(Qt.ItemDataRole.UserRole, str(transaction.id))
            self.setItem(row, 0, date_item)
            
            # Доход
            income_item = SortableTableWidgetItem(
                f"{float(transaction.income):,.2f}",
                float(transaction.income),
            )
            income_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            income_item.setForeground(QColor(income_color))
            self.setItem(row, 1, income_item)
            
            # Расход
            expense_item = SortableTableWidgetItem(
                f"{float(transaction.expense):,.2f}",
                float(transaction.expense),
            )
            expense_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            expense_item.setForeground(QColor(expense_color))
            self.setItem(row, 2, expense_item)
            
            # Налог
            tax_item = SortableTableWidgetItem(
                f"{float(transaction.tax):,.2f}",
                float(transaction.tax),
            )
            tax_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tax_item.setForeground(QColor(tax_color))
            self.setItem(row, 3, tax_item)
            
            # Прибыль
            profit = float(transaction.profit)
            profit_item = SortableTableWidgetItem(f"{profit:,.2f}", profit)
            profit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Цвет в зависимости от прибыли
            if profit >= 0:
                profit_item.setForeground(QColor(profit_positive_color))
                profit_item.setBackground(QColor(profit_positive_bg))
            else:
                profit_item.setForeground(QColor(profit_negative_color))
                profit_item.setBackground(QColor("#ffcdd2"))
            
            # Жирный шрифт для прибыли
            font = QFont()
            font.setBold(True)
            profit_item.setFont(font)
            
            self.setItem(row, 4, profit_item)
            
            # Контрагент
            counterparty_item = QTableWidgetItem(transaction.counterparty_name or "-")
            self.setItem(row, 5, counterparty_item)
            
            # Примечание
            note_item = QTableWidgetItem(transaction.note or "-")
            self.setItem(row, 6, note_item)
        
        # Включаем сортировку обратно
        self.setSortingEnabled(True)
        
        # Сортируем по дате (новые сверху)
        self.sortItems(0, Qt.SortOrder.DescendingOrder)

        # Обновляем высоту строк после заполнения
        self.table_ui.apply_row_heights(self)
    
    def get_selected_transaction_id(self) -> Optional[str]:
        """
        Получить ID выбранной транзакции.
        
        Returns:
            ID транзакции или None
        """
        selected_items = self.selectedItems()
        if not selected_items:
            return None
        
        # Берем первый выбранный элемент и получаем ID из его строки
        row = selected_items[0].row()
        if row < self.rowCount():
            item = self.item(row, 0)  # Дата содержит ID в UserRole
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        
        return None
    
    def get_selected_transaction(self) -> Optional[TransactionResponseDTO]:
        """
        Получить выбранную транзакцию.
        
        Returns:
            Транзакция или None
        """
        transaction_id = self.get_selected_transaction_id()
        if not transaction_id:
            return None
        
        # Ищем транзакцию в списке
        for transaction in self.transactions:
            if str(transaction.id) == transaction_id:
                return transaction
        
        return None
    
    def on_selection_changed(self) -> None:
        """Обработчик изменения выбора."""
        transaction_id = self.get_selected_transaction_id()
        if transaction_id:
            self.transaction_selected.emit(transaction_id)
    
    def on_double_click(self, item) -> None:
        """Обработчик двойного клика."""
        transaction_id = self.get_selected_transaction_id()
        if transaction_id:
            self.transaction_double_clicked.emit(transaction_id)
    
    def show_context_menu(self, position) -> None:
        """Показать контекстное меню."""
        transaction_id = self.get_selected_transaction_id()
        if not transaction_id:
            return
        
        menu = QMenu()
        
        # Действия
        edit_action = QAction("✏️ Редактировать", self)
        edit_action.triggered.connect(lambda: self.transaction_double_clicked.emit(transaction_id))
        
        delete_action = QAction("🗑️ Удалить", self)
        delete_action.triggered.connect(lambda: self.context_menu_requested.emit("delete", {
            "transaction_id": transaction_id,
            "position": position
        }))
        
        copy_action = QAction("📋 Копировать", self)
        copy_action.triggered.connect(lambda: self.copy_selected_to_clipboard())
        
        # Добавляем действия
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(copy_action)
        
        # Показываем меню
        menu.exec(self.viewport().mapToGlobal(position))
    
    def copy_selected_to_clipboard(self) -> None:
        """Копировать выбранные данные в буфер обмена."""
        selected = self.selectedRanges()
        if not selected:
            return
        
        from PyQt6.QtWidgets import QApplication
        
        text = ""
        for range_ in selected:
            for row in range(range_.topRow(), range_.bottomRow() + 1):
                row_text = []
                for col in range(range_.leftColumn(), range_.rightColumn() + 1):
                    item = self.item(row, col)
                    if item:
                        row_text.append(item.text())
                    else:
                        row_text.append("")
                text += "\t".join(row_text) + "\n"
        
        clipboard = QApplication.clipboard()
        clipboard.setText(text.strip())
