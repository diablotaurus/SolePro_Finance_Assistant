"""
Панель фильтров для транзакций.
"""
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QDateEdit,
    QSpinBox,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from .....core.application.dto.transaction_dto import TransactionFilterDTO


class FilterPanel(QWidget):
    """
    Панель фильтров для транзакций.
    
    Сигналы:
        filter_changed: Фильтр изменен
        filter_cleared: Фильтр очищен
    """
    
    filter_changed = pyqtSignal(TransactionFilterDTO)
    filter_cleared = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filter = TransactionFilterDTO()
        self.show_all = False
        self.setup_ui()
        self._update_current_filter()
    
    def setup_ui(self) -> None:
        """Настроить UI панели."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Группа фильтров
        group = QGroupBox("Фильтры")
        group_layout = QVBoxLayout()
        
        # Тип транзакции
        self.type_combo = QComboBox()
        self.type_combo.addItem("Все типы", None)
        self.type_combo.addItem("Доход", "income")
        self.type_combo.addItem("Расход", "expense")
        self.type_combo.addItem("Налог = 0", "no_tax")
        self.type_combo.addItem("Налог", "tax")

        # Пагинация
        pagination_layout = QHBoxLayout()

        self.page_size_combo = QComboBox()
        self.page_size_combo.addItem("10 записей", 10)
        self.page_size_combo.addItem("25 записей", 25)
        self.page_size_combo.addItem("50 записей", 50)
        self.page_size_combo.addItem("100 записей", 100)
        self.page_size_combo.setCurrentIndex(3)  # 100 записей

        pagination_layout.addWidget(self.page_size_combo)

        # Поиск по тексту
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по контрагенту или примечанию...")
        self.search_input.setFixedWidth(320)
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Поиск:"))
        search_row.addWidget(self.search_input)
        search_row.addSpacing(16)
        search_row.addWidget(QLabel("Тип:"))
        search_row.addWidget(self.type_combo)
        search_row.addSpacing(16)
        search_row.addWidget(QLabel("Показывать:"))
        search_row.addLayout(pagination_layout)
        search_row.addStretch()
        group_layout.addLayout(search_row)
        
        # Период
        period_layout = QHBoxLayout()
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd.MM.yyyy")
        current_year_start = QDate(QDate.currentDate().year(), 1, 1)
        self.start_date_edit.setDate(current_year_start)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.end_date_edit.setDate(QDate.currentDate())
        
        period_layout.addWidget(QLabel("с:"))
        period_layout.addWidget(self.start_date_edit)
        period_layout.addWidget(QLabel("по:"))
        period_layout.addWidget(self.end_date_edit)
        
        # Сумма
        amount_layout = QHBoxLayout()
        
        self.min_amount_spin = QSpinBox()
        self.min_amount_spin.setMinimum(0)
        self.min_amount_spin.setMaximum(1000000000)
        self.min_amount_spin.setValue(0)
        self.min_amount_spin.setPrefix("от ")
        self.min_amount_spin.setSuffix(" руб.")
        
        self.max_amount_spin = QSpinBox()
        self.max_amount_spin.setMinimum(0)
        self.max_amount_spin.setMaximum(1000000000)
        self.max_amount_spin.setValue(1000000000)
        self.max_amount_spin.setPrefix("до ")
        self.max_amount_spin.setSuffix(" руб.")
        
        amount_layout.addWidget(self.min_amount_spin)
        amount_layout.addWidget(self.max_amount_spin)

        period_amount_row = QHBoxLayout()
        period_amount_row.addWidget(QLabel("Период:"))
        period_amount_row.addLayout(period_layout)
        period_amount_row.addSpacing(16)
        period_amount_row.addWidget(QLabel("Сумма:"))
        period_amount_row.addLayout(amount_layout)
        period_amount_row.addStretch()
        group_layout.addLayout(period_amount_row)
        
        # Тип + Показывать перенесены в первую строку
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Очистить фильтры")
        self.clear_button.clicked.connect(self.clear_filters)
        
        self.show_all_button = QPushButton("Показать все записи")
        self.show_all_button.clicked.connect(self.show_all_records)

        self.apply_button = QPushButton("Применить")
        self.apply_button.clicked.connect(self.apply_filters)

        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.apply_button)
        buttons_layout.addWidget(self.show_all_button)
        buttons_layout.addStretch()
        
        group_layout.addLayout(buttons_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def apply_filters(self) -> None:
        """Применить фильтры."""
        self.show_all = False
        self._update_current_filter()
        
        # Отправляем сигнал
        self.filter_changed.emit(self.current_filter)
    
    def clear_filters(self) -> None:
        """Очистить все фильтры."""
        # Сбрасываем значения
        self.search_input.clear()
        current_year_start = QDate(QDate.currentDate().year(), 1, 1)
        self.start_date_edit.setDate(current_year_start)
        self.end_date_edit.setDate(QDate.currentDate())
        self.type_combo.setCurrentIndex(0)
        self.min_amount_spin.setValue(0)
        self.max_amount_spin.setValue(1000000000)
        self.page_size_combo.setCurrentIndex(3)
        
        # Сбрасываем текущий фильтр
        self.show_all = False
        self._update_current_filter()
        
        # Отправляем сигнал
        self.filter_cleared.emit()
        self.filter_changed.emit(self.current_filter)

    def show_all_records(self) -> None:
        """Показать все записи без фильтров."""
        self.search_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.min_amount_spin.setValue(0)
        self.max_amount_spin.setValue(1000000000)
        self.page_size_combo.setCurrentIndex(3)
        self.show_all = True
        self._update_current_filter()
        self.filter_changed.emit(self.current_filter)
    
    def get_current_filter(self) -> TransactionFilterDTO:
        """
        Получить текущий фильтр.
        
        Returns:
            Текущий фильтр
        """
        return self.current_filter

    def _update_current_filter(self) -> None:
        """Собрать текущий фильтр без отправки сигнала."""
        filter_dto = TransactionFilterDTO()
        filter_dto.page_size = self.page_size_combo.currentData() or 100
        filter_dto.show_all = self.show_all

        if not self.show_all:
            search_text = self.search_input.text().strip()
            if search_text:
                filter_dto.search_query = search_text

            filter_dto.start_date = self.start_date_edit.date().toPyDate()
            filter_dto.end_date = self.end_date_edit.date().toPyDate()

            transaction_type = self.type_combo.currentData()
            if transaction_type:
                from .....core.domain.enums.transaction_type import TransactionType
                type_map = {
                    "income": TransactionType.INCOME,
                    "expense": TransactionType.EXPENSE,
                }
                if transaction_type == "tax":
                    filter_dto.has_tax = True
                elif transaction_type == "no_tax":
                    filter_dto.no_tax = True
                else:
                    filter_dto.transaction_type = type_map.get(transaction_type)

            min_amount = self.min_amount_spin.value()
            max_amount = self.max_amount_spin.value()
            if min_amount > 0:
                from decimal import Decimal
                filter_dto.min_amount = Decimal(str(min_amount))
            if max_amount < 1000000000:
                from decimal import Decimal
                filter_dto.max_amount = Decimal(str(max_amount))

        self.current_filter = filter_dto
