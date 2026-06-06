"""
Dialog for desktop UI settings.
"""
from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...ui_settings import DesktopUiSettings


class _FocusAwareSpinBox(QSpinBox):
    """Ignores wheel changes unless spinbox currently has focus."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Prevent receiving focus from mouse wheel scrolling.
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        editor = self.lineEdit()
        if editor is not None:
            editor.installEventFilter(self)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 (Qt API)
        if self.hasFocus():
            super().wheelEvent(event)
            return
        event.ignore()

    def eventFilter(self, watched, event) -> bool:  # noqa: N802 (Qt API)
        if event.type() == QEvent.Type.Wheel and not self.hasFocus():
            event.ignore()
            return True
        return super().eventFilter(watched, event)


class SettingsDialog(QDialog):
    """Dialog for editing values from settings/settings.ini."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_settings = DesktopUiSettings(__file__, project_root_parent_index=6)
        self._setup_ui()
        self._load_values()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(600)

        root_layout = QVBoxLayout(self)

        self.auto_refresh_enabled = QCheckBox("Включить автообновление данных")
        self.auto_refresh_interval_seconds = self._create_spinbox(5, 3600)

        self.main_window_pos_x = self._create_spinbox(-4000, 4000)
        self.main_window_pos_y = self._create_spinbox(-4000, 4000)
        self.main_window_width = self._create_spinbox(800, 3840)
        self.main_window_height = self._create_spinbox(600, 2160)

        self.table_font_family = QLineEdit()
        self.table_font_family.setPlaceholderText("Segoe UI")
        self.table_font_size = self._create_spinbox(8, 24)
        self.table_header_font_family = QLineEdit()
        self.table_header_font_family.setPlaceholderText("Segoe UI")
        self.table_header_font_size = self._create_spinbox(8, 24)

        self.vertical_header_font_size = self._create_spinbox(8, 24)
        self.vertical_header_row_padding = self._create_spinbox(0, 80)
        self.vertical_header_width = self._create_spinbox(24, 100)
        self.transactions_column_counterparty_width = self._create_spinbox(120, 700)
        self.transactions_column_note_width = self._create_spinbox(120, 1000)
        self.counterparty_contacts_column_width = self._create_spinbox(120, 700)

        self.totals_card_padding_horizontal = self._create_spinbox(0, 40)
        self.totals_card_padding_vertical = self._create_spinbox(0, 40)
        self.totals_card_spacing = self._create_spinbox(0, 20)
        self.totals_label_padding_horizontal = self._create_spinbox(0, 30)
        self.totals_label_padding_vertical = self._create_spinbox(0, 30)

        self.totals_card_background = QLineEdit()
        self.totals_card_background.setPlaceholderText("#c8e6c9")
        self.totals_card_border_color = QLineEdit()
        self.totals_card_border_color.setPlaceholderText("#e0e0e0")
        self.totals_income_color = QLineEdit()
        self.totals_income_color.setPlaceholderText("#2e7d32")
        self.totals_expense_color = QLineEdit()
        self.totals_expense_color.setPlaceholderText("#c62828")
        self.totals_tax_color = QLineEdit()
        self.totals_tax_color.setPlaceholderText("#1565c0")
        self.totals_profit_positive_color = QLineEdit()
        self.totals_profit_positive_color.setPlaceholderText("#2e7d32")
        self.totals_profit_negative_color = QLineEdit()
        self.totals_profit_negative_color.setPlaceholderText("#c62828")
        self.totals_count_color = QLineEdit()
        self.totals_count_color.setPlaceholderText("#666666")
        self._color_previews: dict[QLineEdit, QLabel] = {}

        self.dialog_transaction_min_width = self._create_spinbox(360, 2400)
        self.dialog_counterparty_manager_min_width = self._create_spinbox(640, 2400)
        self.dialog_counterparty_manager_min_height = self._create_spinbox(360, 1600)
        self.dialog_statistics_min_width = self._create_spinbox(640, 2400)
        self.dialog_statistics_min_height = self._create_spinbox(480, 1600)

        self.color_income = QLineEdit()
        self.color_income.setPlaceholderText("#2e7d32")
        self.color_expense = QLineEdit()
        self.color_expense.setPlaceholderText("#c62828")
        self.color_tax = QLineEdit()
        self.color_tax.setPlaceholderText("#1565c0")
        self.color_profit_positive = QLineEdit()
        self.color_profit_positive.setPlaceholderText("#2e7d32")
        self.color_profit_negative = QLineEdit()
        self.color_profit_negative.setPlaceholderText("#c62828")
        self.color_neutral = QLineEdit()
        self.color_neutral.setPlaceholderText("#666666")

        self.chart_monthly_min_height = self._create_spinbox(120, 1200)
        self.chart_concentration_min_height = self._create_spinbox(120, 1200)
        self.chart_tax_min_height = self._create_spinbox(120, 1200)

        self.statistics_key_value_font_size = self._create_spinbox(10, 36)

        behavior_group = QGroupBox("Приложение: поведение и окно")
        behavior_layout = QFormLayout(behavior_group)
        behavior_layout.setSpacing(8)
        behavior_layout.addRow(
            self._create_group_hint_label(
                "Таймер автообновления и стартовая геометрия главного окна."
            )
        )
        behavior_layout.addRow("Автообновление:", self.auto_refresh_enabled)
        behavior_layout.addRow(
            "Интервал автообновления (сек):",
            self.auto_refresh_interval_seconds,
        )
        behavior_layout.addRow("Главное окно: позиция X:", self.main_window_pos_x)
        behavior_layout.addRow("Главное окно: позиция Y:", self.main_window_pos_y)
        behavior_layout.addRow("Главное окно: ширина:", self.main_window_width)
        behavior_layout.addRow("Главное окно: высота:", self.main_window_height)

        table_fonts_group = QGroupBox("Таблицы: шрифты")
        table_fonts_layout = QFormLayout(table_fonts_group)
        table_fonts_layout.setSpacing(8)
        table_fonts_layout.addRow(
            self._create_group_hint_label(
                "Шрифты данных, заголовков и номеров строк во всех таблицах."
            )
        )
        table_fonts_layout.addRow("Шрифт таблиц (данные):", self.table_font_family)
        table_fonts_layout.addRow("Кегль таблиц (данные):", self.table_font_size)
        table_fonts_layout.addRow("Шрифт заголовков таблиц:", self.table_header_font_family)
        table_fonts_layout.addRow("Кегль заголовков таблиц:", self.table_header_font_size)
        table_fonts_layout.addRow("Кегль вертикального заголовка:", self.vertical_header_font_size)

        table_sizes_group = QGroupBox("Таблицы: размеры и отступы")
        table_sizes_layout = QFormLayout(table_sizes_group)
        table_sizes_layout.setSpacing(8)
        table_sizes_layout.addRow(
            self._create_group_hint_label(
                "Размеры служебных колонок и отступы, влияющие на плотность таблиц."
            )
        )
        table_sizes_layout.addRow(
            "Отступ строки (вертикальный заголовок):",
            self.vertical_header_row_padding,
        )
        table_sizes_layout.addRow("Ширина вертикального заголовка:", self.vertical_header_width)
        table_sizes_layout.addRow(
            "Ширина колонки 'Контрагент' (транзакции):",
            self.transactions_column_counterparty_width,
        )
        table_sizes_layout.addRow(
            "Ширина колонки 'Примечание' (транзакции):",
            self.transactions_column_note_width,
        )
        table_sizes_layout.addRow(
            "Ширина колонки 'Контакты' (контрагенты):",
            self.counterparty_contacts_column_width,
        )

        totals_layout_group = QGroupBox("Карточки итогов: компоновка")
        totals_layout_form = QFormLayout(totals_layout_group)
        totals_layout_form.setSpacing(8)
        totals_layout_form.addRow(
            self._create_group_hint_label(
                "Внутренние отступы карточек и меток в нижнем блоке итогов."
            )
        )
        totals_layout_form.addRow(
            "Карточки итогов: горизонтальный padding:",
            self.totals_card_padding_horizontal,
        )
        totals_layout_form.addRow(
            "Карточки итогов: вертикальный padding:",
            self.totals_card_padding_vertical,
        )
        totals_layout_form.addRow(
            "Карточки итогов: расстояние между метками:",
            self.totals_card_spacing,
        )
        totals_layout_form.addRow(
            "Метки итогов: горизонтальный padding:",
            self.totals_label_padding_horizontal,
        )
        totals_layout_form.addRow(
            "Метки итогов: вертикальный padding:",
            self.totals_label_padding_vertical,
        )

        totals_colors_group = QGroupBox("Карточки итогов: цвета")
        totals_colors_form = QFormLayout(totals_colors_group)
        totals_colors_form.setSpacing(8)
        totals_colors_form.addRow(
            self._create_group_hint_label(
                "Цвета карточек итогов и текста. Формат HEX, например #2e7d32."
            )
        )
        self._add_color_row(
            totals_colors_form,
            "Фон карточек итогов (HEX):",
            self.totals_card_background,
            compact_input=True,
        )
        self._add_color_row(
            totals_colors_form,
            "Граница карточек итогов (HEX):",
            self.totals_card_border_color,
            compact_input=True,
        )
        self._add_color_row(
            totals_colors_form,
            "Текущий/общий доход (HEX):",
            self.totals_income_color,
            compact_input=True,
        )
        self._add_color_row(
            totals_colors_form,
            "Текущий/общий расход (HEX):",
            self.totals_expense_color,
            compact_input=True,
        )
        self._add_color_row(
            totals_colors_form,
            "Текущий/общий налог (HEX):",
            self.totals_tax_color,
            compact_input=True,
        )
        self._add_color_row(
            totals_colors_form,
            "Текущий/общий прибыль (плюс, HEX):",
            self.totals_profit_positive_color,
            compact_input=True,
        )
        self._add_color_row(
            totals_colors_form,
            "Текущий/общий прибыль (минус, HEX):",
            self.totals_profit_negative_color,
            compact_input=True,
        )
        self._add_color_row(
            totals_colors_form,
            "Счетчик записей (HEX):",
            self.totals_count_color,
            compact_input=True,
        )

        dialogs_group = QGroupBox("Диалоги: размеры")
        dialogs_layout = QFormLayout(dialogs_group)
        dialogs_layout.setSpacing(8)
        dialogs_layout.addRow(
            self._create_group_hint_label(
                "Минимальные размеры диалоговых окон."
            )
        )
        dialogs_layout.addRow(
            "Транзакция: минимальная ширина:",
            self.dialog_transaction_min_width,
        )
        dialogs_layout.addRow(
            "Контрагенты: минимальная ширина:",
            self.dialog_counterparty_manager_min_width,
        )
        dialogs_layout.addRow(
            "Контрагенты: минимальная высота:",
            self.dialog_counterparty_manager_min_height,
        )
        dialogs_layout.addRow(
            "Статистика: минимальная ширина:",
            self.dialog_statistics_min_width,
        )
        dialogs_layout.addRow(
            "Статистика: минимальная высота:",
            self.dialog_statistics_min_height,
        )

        palette_group = QGroupBox("Цветовая палитра: семантика")
        palette_layout = QFormLayout(palette_group)
        palette_layout.setSpacing(8)
        palette_layout.addRow(
            self._create_group_hint_label(
                "Общие цвета дохода/расхода/налога/прибыли для таблиц и статистики."
            )
        )
        self._add_color_row(palette_layout, "Доход (HEX):", self.color_income)
        self._add_color_row(palette_layout, "Расход (HEX):", self.color_expense)
        self._add_color_row(palette_layout, "Налог (HEX):", self.color_tax)
        self._add_color_row(palette_layout, "Прибыль плюс (HEX):", self.color_profit_positive)
        self._add_color_row(palette_layout, "Прибыль минус (HEX):", self.color_profit_negative)
        self._add_color_row(palette_layout, "Нейтральный (HEX):", self.color_neutral)

        charts_group = QGroupBox("Графики: размеры")
        charts_layout = QFormLayout(charts_group)
        charts_layout.setSpacing(8)
        charts_layout.addRow(
            self._create_group_hint_label(
                "Минимальная высота графиков в окне статистики."
            )
        )
        charts_layout.addRow("Тренды: минимальная высота:", self.chart_monthly_min_height)
        charts_layout.addRow(
            "Концентрация: минимальная высота:",
            self.chart_concentration_min_height,
        )
        charts_layout.addRow("Налоги: минимальная высота:", self.chart_tax_min_height)

        statistics_fonts_group = QGroupBox("Статистика: шрифты")
        statistics_fonts_layout = QFormLayout(statistics_fonts_group)
        statistics_fonts_layout.setSpacing(8)
        statistics_fonts_layout.addRow(
            self._create_group_hint_label(
                "Кегль значений в блоке 'Ключевые показатели' окна статистики."
            )
        )
        statistics_fonts_layout.addRow(
            "Кегль значений (Ключевые показатели):",
            self.statistics_key_value_font_size,
        )

        tab_widget = QTabWidget()

        general_tab = QWidget()
        general_tab_layout = QVBoxLayout(general_tab)
        general_content = QWidget()
        general_content_layout = QVBoxLayout(general_content)
        general_content_layout.addWidget(behavior_group)
        general_content_layout.addWidget(totals_layout_group)
        general_content_layout.addWidget(totals_colors_group)
        general_content_layout.addStretch()
        general_scroll = QScrollArea()
        general_scroll.setWidgetResizable(True)
        general_scroll.setWidget(general_content)
        general_tab_layout.addWidget(general_scroll)
        tab_widget.addTab(general_tab, "Главное окно")

        tables_tab = QWidget()
        tables_tab_layout = QVBoxLayout(tables_tab)
        tables_tab_layout.addWidget(table_fonts_group)
        tables_tab_layout.addWidget(table_sizes_group)
        tables_tab_layout.addStretch()
        tab_widget.addTab(tables_tab, "Транзакции и таблицы")

        statistics_tab = QWidget()
        statistics_tab_layout = QVBoxLayout(statistics_tab)
        statistics_tab_layout.addWidget(statistics_fonts_group)
        statistics_tab_layout.addWidget(palette_group)
        statistics_tab_layout.addWidget(charts_group)
        statistics_tab_layout.addStretch()
        tab_widget.addTab(statistics_tab, "Статистика")

        dialogs_tab = QWidget()
        dialogs_tab_layout = QVBoxLayout(dialogs_tab)
        dialogs_tab_layout.addWidget(dialogs_group)
        dialogs_tab_layout.addStretch()
        tab_widget.addTab(dialogs_tab, "Диалоги")

        root_layout.addWidget(tab_widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        root_layout.addWidget(buttons)

    @staticmethod
    def _create_spinbox(minimum: int, maximum: int) -> QSpinBox:
        spinbox = _FocusAwareSpinBox()
        spinbox.setRange(minimum, maximum)
        return spinbox

    @staticmethod
    def _create_group_hint_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("color: #666666;")
        return label

    def _add_color_row(
        self,
        form: QFormLayout,
        title: str,
        field: QLineEdit,
        compact_input: bool = False,
    ) -> None:
        if compact_input:
            field.setMaximumWidth(120)

        preview = QLabel()
        preview.setFixedSize(30, 30)
        preview.setStyleSheet("border: 1px solid #999999; border-radius: 2px;")
        self._color_previews[field] = preview

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        row_layout.addWidget(field)
        row_layout.addWidget(preview)
        row_layout.addStretch()

        field.textChanged.connect(
            lambda _text, current_field=field: self._update_color_preview(current_field)
        )
        self._update_color_preview(field)
        form.addRow(title, row_widget)

    def _update_color_preview(self, field: QLineEdit) -> None:
        preview = self._color_previews.get(field)
        if preview is None:
            return
        value = field.text().strip()
        color = value if self._is_valid_hex_color(value) else "#ffffff"
        preview.setStyleSheet(
            f"background-color: {color}; border: 1px solid #999999; border-radius: 2px;"
        )

    def _load_values(self) -> None:
        self.auto_refresh_enabled.setChecked(
            self.ui_settings.get_int("auto_refresh_enabled", 1) == 1
        )
        self.auto_refresh_interval_seconds.setValue(
            max(5, self.ui_settings.get_int("auto_refresh_interval_ms", 30000) // 1000)
        )
        self.main_window_pos_x.setValue(self.ui_settings.get_int("main_window_pos_x", 100))
        self.main_window_pos_y.setValue(self.ui_settings.get_int("main_window_pos_y", 100))
        self.main_window_width.setValue(self.ui_settings.get_int("main_window_width", 1400))
        self.main_window_height.setValue(self.ui_settings.get_int("main_window_height", 800))

        self.table_font_family.setText(
            self.ui_settings.get_str("table_font_family", "Segoe UI")
        )
        self.table_font_size.setValue(
            self.ui_settings.get_int("table_font_size", 11)
        )
        self.table_header_font_family.setText(
            self.ui_settings.get_str(
                "table_header_font_family",
                self.ui_settings.get_str("table_font_family", "Segoe UI"),
            )
        )
        self.table_header_font_size.setValue(
            self.ui_settings.get_int(
                "table_header_font_size",
                self.ui_settings.get_int("table_font_size", 11),
            )
        )
        self.vertical_header_font_size.setValue(
            self.ui_settings.get_int("vertical_header_font_size", 11)
        )
        self.vertical_header_row_padding.setValue(
            self.ui_settings.get_int("vertical_header_row_padding", 16)
        )
        self.vertical_header_width.setValue(
            self.ui_settings.get_int("vertical_header_width", 34)
        )
        self.transactions_column_counterparty_width.setValue(
            self.ui_settings.get_int("transactions_column_counterparty_width", 260)
        )
        self.transactions_column_note_width.setValue(
            self.ui_settings.get_int("transactions_column_note_width", 300)
        )
        self.counterparty_contacts_column_width.setValue(
            self.ui_settings.get_int("counterparty_contacts_column_width", 250)
        )
        self.totals_card_padding_horizontal.setValue(
            self.ui_settings.get_int("totals_card_padding_horizontal", 0)
        )
        self.totals_card_padding_vertical.setValue(
            self.ui_settings.get_int("totals_card_padding_vertical", 0)
        )
        self.totals_card_spacing.setValue(
            self.ui_settings.get_int("totals_card_spacing", 0)
        )
        self.totals_label_padding_horizontal.setValue(
            self.ui_settings.get_int("totals_label_padding_horizontal", 0)
        )
        self.totals_label_padding_vertical.setValue(
            self.ui_settings.get_int("totals_label_padding_vertical", 0)
        )
        self.totals_card_background.setText(
            self.ui_settings.get_str("totals_card_background", "#c8e6c9")
        )
        self.totals_card_border_color.setText(
            self.ui_settings.get_str("totals_card_border_color", "#e0e0e0")
        )
        self.totals_income_color.setText(
            self.ui_settings.get_str("totals_income_color", "#2e7d32")
        )
        self.totals_expense_color.setText(
            self.ui_settings.get_str("totals_expense_color", "#c62828")
        )
        self.totals_tax_color.setText(
            self.ui_settings.get_str("totals_tax_color", "#1565c0")
        )
        self.totals_profit_positive_color.setText(
            self.ui_settings.get_str("totals_profit_positive_color", "#2e7d32")
        )
        self.totals_profit_negative_color.setText(
            self.ui_settings.get_str("totals_profit_negative_color", "#c62828")
        )
        self.totals_count_color.setText(
            self.ui_settings.get_str("totals_count_color", "#666666")
        )

        self.dialog_transaction_min_width.setValue(
            self.ui_settings.get_int("dialog_transaction_min_width", 500)
        )
        self.dialog_counterparty_manager_min_width.setValue(
            self.ui_settings.get_int("dialog_counterparty_manager_min_width", 900)
        )
        self.dialog_counterparty_manager_min_height.setValue(
            self.ui_settings.get_int("dialog_counterparty_manager_min_height", 500)
        )
        self.dialog_statistics_min_width.setValue(
            self.ui_settings.get_int("dialog_statistics_min_width", 800)
        )
        self.dialog_statistics_min_height.setValue(
            self.ui_settings.get_int("dialog_statistics_min_height", 600)
        )

        self.color_income.setText(self.ui_settings.get_str("color_income", "#2e7d32"))
        self.color_expense.setText(self.ui_settings.get_str("color_expense", "#c62828"))
        self.color_tax.setText(self.ui_settings.get_str("color_tax", "#1565c0"))
        self.color_profit_positive.setText(
            self.ui_settings.get_str("color_profit_positive", "#2e7d32")
        )
        self.color_profit_negative.setText(
            self.ui_settings.get_str("color_profit_negative", "#c62828")
        )
        self.color_neutral.setText(self.ui_settings.get_str("color_neutral", "#666666"))

        self.chart_monthly_min_height.setValue(
            self.ui_settings.get_int("chart_monthly_min_height", 280)
        )
        self.chart_concentration_min_height.setValue(
            self.ui_settings.get_int("chart_concentration_min_height", 260)
        )
        self.chart_tax_min_height.setValue(
            self.ui_settings.get_int("chart_tax_min_height", 250)
        )
        self.statistics_key_value_font_size.setValue(
            self.ui_settings.get_int("statistics_key_value_font_size", 14)
        )

    def _on_save(self) -> None:
        table_font_family = self.table_font_family.text().strip() or "Segoe UI"
        table_header_font_family = (
            self.table_header_font_family.text().strip() or table_font_family
        )

        color_fields = [
            ("Фон карточек итогов", self.totals_card_background),
            ("Граница карточек итогов", self.totals_card_border_color),
            ("Цвет дохода в карточках итогов", self.totals_income_color),
            ("Цвет расхода в карточках итогов", self.totals_expense_color),
            ("Цвет налога в карточках итогов", self.totals_tax_color),
            ("Цвет прибыли (+) в карточках итогов", self.totals_profit_positive_color),
            ("Цвет прибыли (-) в карточках итогов", self.totals_profit_negative_color),
            ("Цвет счетчика записей в карточках итогов", self.totals_count_color),
            ("Семантический цвет дохода", self.color_income),
            ("Семантический цвет расхода", self.color_expense),
            ("Семантический цвет налога", self.color_tax),
            ("Семантический цвет прибыли (+)", self.color_profit_positive),
            ("Семантический цвет прибыли (-)", self.color_profit_negative),
            ("Семантический нейтральный цвет", self.color_neutral),
        ]
        for title, field in color_fields:
            value = field.text().strip()
            if not value:
                continue
            if not self._is_valid_hex_color(value):
                QMessageBox.warning(
                    self,
                    "Проверка данных",
                    f"{title} должен быть в формате HEX, например #c8e6c9",
                )
                return

        self.ui_settings.set_int(
            "auto_refresh_enabled",
            1 if self.auto_refresh_enabled.isChecked() else 0,
        )
        self.ui_settings.set_int(
            "auto_refresh_interval_ms",
            self.auto_refresh_interval_seconds.value() * 1000,
        )
        self.ui_settings.set_int("main_window_pos_x", self.main_window_pos_x.value())
        self.ui_settings.set_int("main_window_pos_y", self.main_window_pos_y.value())
        self.ui_settings.set_int("main_window_width", self.main_window_width.value())
        self.ui_settings.set_int("main_window_height", self.main_window_height.value())

        self.ui_settings.set_str("table_font_family", table_font_family)
        self.ui_settings.set_int("table_font_size", self.table_font_size.value())
        self.ui_settings.set_str("table_header_font_family", table_header_font_family)
        self.ui_settings.set_int("table_header_font_size", self.table_header_font_size.value())
        self.ui_settings.set_int("vertical_header_font_size", self.vertical_header_font_size.value())
        self.ui_settings.set_int("vertical_header_row_padding", self.vertical_header_row_padding.value())
        self.ui_settings.set_int("vertical_header_width", self.vertical_header_width.value())
        self.ui_settings.set_int(
            "transactions_column_counterparty_width",
            self.transactions_column_counterparty_width.value(),
        )
        self.ui_settings.set_int(
            "transactions_column_note_width",
            self.transactions_column_note_width.value(),
        )
        self.ui_settings.set_int(
            "counterparty_contacts_column_width",
            self.counterparty_contacts_column_width.value(),
        )
        self.ui_settings.set_int(
            "totals_card_padding_horizontal",
            self.totals_card_padding_horizontal.value(),
        )
        self.ui_settings.set_int(
            "totals_card_padding_vertical",
            self.totals_card_padding_vertical.value(),
        )
        self.ui_settings.set_int("totals_card_spacing", self.totals_card_spacing.value())
        self.ui_settings.set_int(
            "totals_label_padding_horizontal",
            self.totals_label_padding_horizontal.value(),
        )
        self.ui_settings.set_int(
            "totals_label_padding_vertical",
            self.totals_label_padding_vertical.value(),
        )

        self.ui_settings.set_str(
            "totals_card_background",
            self.totals_card_background.text().strip() or "#c8e6c9",
        )
        self.ui_settings.set_str(
            "totals_card_border_color",
            self.totals_card_border_color.text().strip() or "#e0e0e0",
        )
        self.ui_settings.set_str(
            "totals_income_color",
            self.totals_income_color.text().strip() or "#2e7d32",
        )
        self.ui_settings.set_str(
            "totals_expense_color",
            self.totals_expense_color.text().strip() or "#c62828",
        )
        self.ui_settings.set_str(
            "totals_tax_color",
            self.totals_tax_color.text().strip() or "#1565c0",
        )
        self.ui_settings.set_str(
            "totals_profit_positive_color",
            self.totals_profit_positive_color.text().strip() or "#2e7d32",
        )
        self.ui_settings.set_str(
            "totals_profit_negative_color",
            self.totals_profit_negative_color.text().strip() or "#c62828",
        )
        self.ui_settings.set_str(
            "totals_count_color",
            self.totals_count_color.text().strip() or "#666666",
        )

        self.ui_settings.set_int(
            "dialog_transaction_min_width",
            self.dialog_transaction_min_width.value(),
        )
        self.ui_settings.set_int(
            "dialog_counterparty_manager_min_width",
            self.dialog_counterparty_manager_min_width.value(),
        )
        self.ui_settings.set_int(
            "dialog_counterparty_manager_min_height",
            self.dialog_counterparty_manager_min_height.value(),
        )
        self.ui_settings.set_int(
            "dialog_statistics_min_width",
            self.dialog_statistics_min_width.value(),
        )
        self.ui_settings.set_int(
            "dialog_statistics_min_height",
            self.dialog_statistics_min_height.value(),
        )

        self.ui_settings.set_str("color_income", self.color_income.text().strip() or "#2e7d32")
        self.ui_settings.set_str("color_expense", self.color_expense.text().strip() or "#c62828")
        self.ui_settings.set_str("color_tax", self.color_tax.text().strip() or "#1565c0")
        self.ui_settings.set_str(
            "color_profit_positive",
            self.color_profit_positive.text().strip() or "#2e7d32",
        )
        self.ui_settings.set_str(
            "color_profit_negative",
            self.color_profit_negative.text().strip() or "#c62828",
        )
        self.ui_settings.set_str("color_neutral", self.color_neutral.text().strip() or "#666666")

        self.ui_settings.set_int(
            "chart_monthly_min_height",
            self.chart_monthly_min_height.value(),
        )
        self.ui_settings.set_int(
            "chart_concentration_min_height",
            self.chart_concentration_min_height.value(),
        )
        self.ui_settings.set_int(
            "chart_tax_min_height",
            self.chart_tax_min_height.value(),
        )
        self.ui_settings.set_int(
            "statistics_key_value_font_size",
            self.statistics_key_value_font_size.value(),
        )
        self.ui_settings.save()

        QMessageBox.information(
            self,
            "Настройки сохранены",
            "Настройки сохранены. Для полного применения перезапустите приложение.",
        )
        self.accept()

    @staticmethod
    def _is_valid_hex_color(value: str) -> bool:
        if len(value) != 7 or not value.startswith("#"):
            return False
        hex_part = value[1:]
        return all(ch in "0123456789abcdefABCDEF" for ch in hex_part)
