"""
Диалог для создания и редактирования контрагента.
"""
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QDialogButtonBox,
)
from PyQt6.QtCore import pyqtSignal

from .....core.application.dto.counterparty_dto import (
    CounterpartyCreateDTO,
    CounterpartyUpdateDTO,
    CounterpartyResponseDTO,
)


class CounterpartyDialog(QDialog):
    """
    Диалог для создания и редактирования контрагента.

    Сигналы:
        counterparty_saved: испускается при сохранении
    """

    counterparty_saved = pyqtSignal(object)  # CounterpartyResponseDTO

    def __init__(
        self,
        counterparty: Optional[CounterpartyResponseDTO] = None,
        parent=None
    ):
        super().__init__(parent)

        self.counterparty = counterparty
        self.is_edit_mode = counterparty is not None

        self.setup_ui()
        self.load_data()

    def setup_ui(self) -> None:
        """Настраивает UI диалога."""
        self.setWindowTitle(
            "Редактирование контрагента" if self.is_edit_mode else "Создание контрагента"
        )
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Форма
        form_layout = QFormLayout()

        # Название
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите название контрагента")
        form_layout.addRow("Название*:", self.name_edit)

        # Описание
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Описание контрагента (необязательно)")
        form_layout.addRow("Описание:", self.description_edit)

        # Контактная информация
        self.contact_edit = QTextEdit()
        self.contact_edit.setMaximumHeight(80)
        self.contact_edit.setPlaceholderText("Контактная информация (необязательно)")
        form_layout.addRow("Контакты:", self.contact_edit)

        layout.addLayout(form_layout)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def load_data(self) -> None:
        """Загружает данные контрагента."""
        if not self.counterparty:
            return

        # Название
        self.name_edit.setText(self.counterparty.name)

        # Описание
        if self.counterparty.description:
            self.description_edit.setText(self.counterparty.description)

        # Контактная информация
        if self.counterparty.contact_info:
            self.contact_edit.setText(self.counterparty.contact_info)

    def get_counterparty_data(self) -> Optional[CounterpartyCreateDTO]:
        """
        Извлекает данные контрагента из формы.

        Returns:
            Данные контрагента или None при ошибке
        """
        try:
            # Валидация (обязательное поле)
            name = self.name_edit.text().strip()
            if not name:
                raise ValueError("Название контрагента обязательно")

            # Описание
            description = self.description_edit.toPlainText().strip()
            if not description:
                description = None

            # Контактная информация
            contact_info = self.contact_edit.toPlainText().strip()
            if not contact_info:
                contact_info = None

            # Создаем DTO
            if self.is_edit_mode and self.counterparty:
                # Для редактирования
                dto = CounterpartyUpdateDTO(
                    name=name,
                    description=description,
                    contact_info=contact_info,
                )
            else:
                # Для создания
                dto = CounterpartyCreateDTO(
                    name=name,
                    description=description,
                    contact_info=contact_info,
                )

            return dto

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка ввода: {str(e)}")
            return None

    def accept(self) -> None:
        """Обработка нажатия OK."""
        data = self.get_counterparty_data()
        if data:
            super().accept()

            # Сохранением занимается контроллер: наружу отдаём только
            # введённые данные и ID редактируемого контрагента.
            self.counterparty_saved.emit({
                "counterparty_id": self.counterparty.id if self.counterparty else None,
                "data": data,
                "is_edit": self.is_edit_mode
            })
