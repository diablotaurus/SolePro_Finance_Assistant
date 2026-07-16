"""
Диалог для добавления/редактирования транзакции.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Callable
from uuid import UUID

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDateEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from .....core.application.dto.transaction_dto import (
    TransactionCreateDTO,
    TransactionUpdateDTO,
    TransactionResponseDTO,
)
from .....core.application.dto.counterparty_dto import (
    CounterpartyCreateDTO,
    CounterpartyResponseDTO,
)
from .counterparty_dialog import CounterpartyDialog
from ...ui_settings import DesktopUiSettings


class TransactionDialog(QDialog):
    """
    Диалог для работы с транзакциями.
    
    Сигналы:
        transaction_saved: Транзакция сохранена
    """
    
    transaction_saved = pyqtSignal(object)  # TransactionResponseDTO
    
    def __init__(
        self,
        transaction: Optional[TransactionResponseDTO] = None,
        counterparties: Optional[list[CounterpartyResponseDTO]] = None,
        add_counterparty_callback: Optional[
            Callable[[CounterpartyCreateDTO], Optional[CounterpartyResponseDTO]]
        ] = None,
        parent=None
    ):
        super().__init__(parent)

        self.transaction = transaction
        self.counterparties = counterparties or []
        self.is_edit_mode = transaction is not None
        self.ui_settings = DesktopUiSettings(__file__, project_root_parent_index=6)
        self._add_counterparty_callback = add_counterparty_callback
        self._counterparty_change_in_progress = False
        self._previous_counterparty_index = 0
        
        self.setup_ui()
        self.load_data()
        self._previous_counterparty_index = self.counterparty_combo.currentIndex()
    
    def setup_ui(self) -> None:
        """Настроить UI диалога."""
        self.setWindowTitle(
            "Редактировать транзакцию" if self.is_edit_mode else "Добавить транзакцию"
        )
        self.setMinimumWidth(
            self.ui_settings.get_int("dialog_transaction_min_width", 500)
        )
        
        layout = QVBoxLayout(self)
        
        # Форма
        form_layout = QFormLayout()
        
        # Дата
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Дата:", self.date_edit)
        
        # Доход
        self.income_edit = QLineEdit()
        self.income_edit.setPlaceholderText("0.00")
        self.income_edit.textChanged.connect(self.validate_amounts)
        form_layout.addRow("Доход (руб.):", self.income_edit)
        
        # Расход
        self.expense_edit = QLineEdit()
        self.expense_edit.setPlaceholderText("0.00")
        self.expense_edit.textChanged.connect(self.validate_amounts)
        form_layout.addRow("Расход (руб.):", self.expense_edit)
        
        # Налог
        self.tax_edit = QLineEdit()
        self.tax_edit.setPlaceholderText("0.00")
        self.tax_edit.textChanged.connect(self.validate_amounts)
        form_layout.addRow("Налог (руб.):", self.tax_edit)
        
        # Контрагент
        self.counterparty_combo = QComboBox()
        self.counterparty_combo.addItem("-- Выберите контрагента --", None)
        
        for counterparty in self.counterparties:
            self.counterparty_combo.addItem(counterparty.name, counterparty.id)
        
        self.counterparty_combo.addItem("➕ Добавить нового...", "new")
        self.counterparty_combo.currentIndexChanged.connect(self.on_counterparty_changed)
        form_layout.addRow("Контрагент:", self.counterparty_combo)
        
        # Примечание
        self.note_edit = QTextEdit()
        self.note_edit.setMaximumHeight(100)
        form_layout.addRow("Примечание:", self.note_edit)
        
        # Расчетная прибыль
        self.profit_label = QLabel("0.00 руб.")
        self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        form_layout.addRow("Прибыль:", self.profit_label)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def load_data(self) -> None:
        """Загрузить данные транзакции."""
        if not self.transaction:
            return
        
        # Дата
        self.date_edit.setDate(QDate(
            self.transaction.date.year,
            self.transaction.date.month,
            self.transaction.date.day
        ))
        
        # Суммы
        self.income_edit.setText(str(self.transaction.income))
        self.expense_edit.setText(str(self.transaction.expense))
        self.tax_edit.setText(str(self.transaction.tax))
        
        # Контрагент
        if self.transaction.counterparty_id:
            for i in range(self.counterparty_combo.count()):
                if self.counterparty_combo.itemData(i) == self.transaction.counterparty_id:
                    self.counterparty_combo.setCurrentIndex(i)
                    break
        
        # Примечание
        self.note_edit.setText(self.transaction.note or "")
        
        # Прибыль
        self.update_profit()
    
    def validate_amounts(self) -> None:
        """Валидация денежных сумм."""
        try:
            # Обновляем расчетную прибыль
            self.update_profit()
            
            # Проверяем формат доходов
            income_text = self.income_edit.text().strip()
            if income_text:
                income = Decimal(income_text)
                if income < 0:
                    raise ValueError("Доход не может быть отрицательным")
            
            # Проверяем формат расходов
            expense_text = self.expense_edit.text().strip()
            if expense_text:
                expense = Decimal(expense_text)
                if expense < 0:
                    raise ValueError("Расход не может быть отрицательным")
            
            # Проверяем формат налога
            tax_text = self.tax_edit.text().strip()
            if tax_text:
                tax = Decimal(tax_text)
                if tax < 0:
                    raise ValueError("Налог не может быть отрицательным")
                
        except Exception:
            # Ошибки валидации будут отображены при сохранении
            pass

    def _set_counterparty_index(self, index: int) -> None:
        """Безопасно изменить выбранного контрагента без повторной обработки."""
        self._counterparty_change_in_progress = True
        self.counterparty_combo.setCurrentIndex(index)
        self._counterparty_change_in_progress = False

    def _add_counterparty_to_combo(self, counterparty: CounterpartyResponseDTO) -> None:
        """Добавить контрагента в список и выбрать его."""
        for i in range(self.counterparty_combo.count()):
            if self.counterparty_combo.itemData(i) == counterparty.id:
                self._set_counterparty_index(i)
                self._previous_counterparty_index = i
                return

        insert_index = max(self.counterparty_combo.count() - 1, 1)
        self.counterparty_combo.insertItem(insert_index, counterparty.name, counterparty.id)
        self.counterparties.append(counterparty)
        self._set_counterparty_index(insert_index)
        self._previous_counterparty_index = insert_index

    def on_counterparty_changed(self, index: int) -> None:
        """Обработчик выбора контрагента."""
        if self._counterparty_change_in_progress:
            return

        counterparty_id = self.counterparty_combo.itemData(index)
        if counterparty_id == "new":
            previous_index = self._previous_counterparty_index
            self._set_counterparty_index(previous_index)
            self._handle_add_counterparty()
            return

        self._previous_counterparty_index = index

    def _handle_add_counterparty(self) -> None:
        """Открыть диалог добавления контрагента и выбрать результат."""
        if not self._add_counterparty_callback:
            QMessageBox.information(
                self,
                "Добавление контрагента",
                "Добавление контрагента недоступно в этом режиме."
            )
            self._set_counterparty_index(self._previous_counterparty_index)
            return

        dialog = CounterpartyDialog(parent=self)
        if not dialog.exec():
            self._set_counterparty_index(self._previous_counterparty_index)
            return

        dto = dialog.get_counterparty_data()
        if not dto:
            self._set_counterparty_index(self._previous_counterparty_index)
            return

        created = self._add_counterparty_callback(dto)
        if not created:
            QMessageBox.warning(
                self,
                "Добавление контрагента",
                "Не удалось добавить контрагента. Проверьте данные и попробуйте снова."
            )
            self._set_counterparty_index(self._previous_counterparty_index)
            return

        self._add_counterparty_to_combo(created)
    
    def update_profit(self) -> None:
        """Обновить расчетную прибыль."""
        try:
            income = Decimal(self.income_edit.text() or "0")
            expense = Decimal(self.expense_edit.text() or "0")
            tax = Decimal(self.tax_edit.text() or "0")
            
            profit = income - expense - tax
            
            # Обновляем label
            self.profit_label.setText(f"{profit:,.2f} руб.")
            
            # Цвет в зависимости от прибыли
            if profit >= 0:
                self.profit_label.setStyleSheet(
                    (
                        "font-weight: bold; font-size: 12pt; color: "
                        f"{self.ui_settings.get_str('color_profit_positive', '#2e7d32')};"
                    )
                )
            else:
                self.profit_label.setStyleSheet(
                    (
                        "font-weight: bold; font-size: 12pt; color: "
                        f"{self.ui_settings.get_str('color_profit_negative', '#c62828')};"
                    )
                )
                
        except Exception:
            self.profit_label.setText("0.00 руб.")
            self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
    
    def get_transaction_data(self) -> Optional[TransactionCreateDTO]:
        """
        Получить данные транзакции из формы.
        
        Returns:
            Данные транзакции или None при ошибке
        """
        try:
            # Дата
            qdate = self.date_edit.date()
            date = datetime(qdate.year(), qdate.month(), qdate.day())
            
            # Суммы
            income = Decimal(self.income_edit.text() or "0")
            expense = Decimal(self.expense_edit.text() or "0")
            tax = Decimal(self.tax_edit.text() or "0")
            
            # Валидация сумм
            if income < 0 or expense < 0 or tax < 0:
                raise ValueError("Суммы не могут быть отрицательными")
            
            # Контрагент
            counterparty_id = self.counterparty_combo.currentData()
            counterparty_name = None
            
            if counterparty_id == "new":
                QMessageBox.warning(
                    self,
                    "Добавление контрагента",
                    "Сначала добавьте контрагента через диалог."
                )
                return None
            elif counterparty_id:
                # Ищем имя контрагента
                for counterparty in self.counterparties:
                    if counterparty.id == counterparty_id:
                        counterparty_name = counterparty.name
                        break
            
            # Примечание
            note = self.note_edit.toPlainText().strip()
            
            # Создаем DTO
            if self.is_edit_mode and self.transaction:
                # Для редактирования. Пустой выбор в комбобоксе означает
                # «убрать контрагента» — передаём это явным флагом,
                # так как None в counterparty_id значит «не менять».
                dto = TransactionUpdateDTO(
                    date=date,
                    income=income,
                    expense=expense,
                    tax=tax,
                    counterparty_id=counterparty_id if counterparty_id not in [None, "new"] else None,
                    clear_counterparty=counterparty_id is None,
                    note=note or None,
                )
            else:
                # Для создания
                dto = TransactionCreateDTO(
                    date=date,
                    income=income,
                    expense=expense,
                    tax=tax,
                    counterparty_id=counterparty_id if counterparty_id not in [None, "new"] else None,
                    counterparty_name=counterparty_name,
                    note=note or None,
                )
            
            return dto
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Неверные данные: {str(e)}")
            return None
    
    def accept(self) -> None:
        """Обработчик нажатия OK."""
        data = self.get_transaction_data()
        if data:
            super().accept()
            
            # Создаем объект транзакции для сигнала
            # В реальном приложении здесь будет сохраненная транзакция из контроллера
            from .....core.application.dto.transaction_dto import TransactionResponseDTO
            from decimal import Decimal
            from uuid import uuid4
            
            profit = data.income - data.expense - data.tax
            
            transaction = TransactionResponseDTO(
                id=self.transaction.id if self.transaction else uuid4(),
                date=data.date,
                income=data.income,
                expense=data.expense,
                tax=data.tax,
                profit=profit,
                counterparty_id=data.counterparty_id if hasattr(data, 'counterparty_id') else None,
                counterparty_name=self.counterparty_combo.currentText(),
                note=data.note or "",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            
            self.transaction_saved.emit({
                "transaction": transaction,
                "data": data,
                "is_edit": self.is_edit_mode
            })
