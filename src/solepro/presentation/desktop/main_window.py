"""
Главное окно приложения.
"""
import sys
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStatusBar,
    QMenuBar,
    QMenu,
    QToolBar,
    QMessageBox,
    QFileDialog,
    QSplitter,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont

from .controllers.main_controller import MainController
from .views.widgets.transaction_table import TransactionTableView
from .views.widgets.filter_panel import FilterPanel
from .views.dialogs.transaction_dialog import TransactionDialog
from .views.dialogs.statistics_dialog import StatisticsDialog
from .views.dialogs.counterparty_manager_dialog import CounterpartyManagerDialog
from .views.dialogs.settings_dialog import SettingsDialog
from .ui_settings import DesktopUiSettings
from ...core.application.dto.transaction_dto import TransactionFilterDTO


class MainWindow(QMainWindow):
    """
    Главное окно приложения.
    
    Сигналы:
        refresh_requested: Запрос на обновление данных
    """
    
    refresh_requested = pyqtSignal()
    
    def __init__(self, controller: MainController):
        super().__init__()
        
        self.controller = controller
        self.ui_settings = DesktopUiSettings(__file__, project_root_parent_index=4)
        self.setup_ui()
        self.connect_signals()
        self.load_initial_data()
        
        # Таймер для автообновления
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        if self.ui_settings.get_int("auto_refresh_enabled", 1) == 1:
            interval = max(1000, self.ui_settings.get_int("auto_refresh_interval_ms", 30000))
            self.refresh_timer.start(interval)
    
    def setup_ui(self) -> None:
        """Настроить UI главного окна."""
        # Основные настройки окна
        version = self._get_app_version()
        title = f"SolePro Finance Assistant - v{version}" if version else "SolePro Finance Assistant"
        self.setWindowTitle(title)
        self.setGeometry(
            self.ui_settings.get_int("main_window_pos_x", 100),
            self.ui_settings.get_int("main_window_pos_y", 100),
            self.ui_settings.get_int("main_window_width", 1400),
            self.ui_settings.get_int("main_window_height", 800),
        )
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Создаем меню
        self.create_menu_bar()
        
        # Создаем панель инструментов
        self.create_toolbar()
        
        # Создаем разделитель для основной области
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter = splitter
        
        # Верхняя часть: фильтры
        filter_widget = QWidget()
        self.filter_container = filter_widget
        filter_layout = QVBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        
        self.filter_panel = FilterPanel()
        filter_layout.addWidget(self.filter_panel)
        
        splitter.addWidget(filter_widget)
        
        # Центральная часть: таблица транзакций
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.transaction_table = TransactionTableView()
        table_layout.addWidget(self.transaction_table)
        
        splitter.addWidget(table_widget)
        
        # Нижняя часть: итоги
        totals_widget = QWidget()
        totals_layout = QVBoxLayout(totals_widget)
        totals_layout.setContentsMargins(10, 10, 10, 10)
        totals_layout.setSpacing(8)

        totals_row = QHBoxLayout()
        totals_row.setSpacing(10)

        income_color = self.ui_settings.get_str("totals_income_color", "#2e7d32")
        expense_color = self.ui_settings.get_str("totals_expense_color", "#c62828")
        tax_color = self.ui_settings.get_str("totals_tax_color", "#1565c0")
        profit_positive_color = self.ui_settings.get_str("totals_profit_positive_color", "#2e7d32")
        self._totals_profit_negative_color = self.ui_settings.get_str(
            "totals_profit_negative_color",
            "#c62828",
        )
        count_color = self.ui_settings.get_str("totals_count_color", "#666666")
        self._totals_profit_positive_color = profit_positive_color

        income_card, self.period_income_label, self.total_income_label = self.create_total_card(
            "Текущий доход: 0.00 руб.",
            "Общий доход: 0.00 руб.",
            income_color
        )
        expense_card, self.period_expense_label, self.total_expense_label = self.create_total_card(
            "Текущий расход: 0.00 руб.",
            "Общий расход: 0.00 руб.",
            expense_color
        )
        tax_card, self.period_tax_label, self.total_tax_label = self.create_total_card(
            "Текущий налог: 0.00 руб.",
            "Общий налог: 0.00 руб.",
            tax_color
        )
        profit_card, self.period_profit_label, self.total_profit_label = self.create_total_card(
            "Текущая прибыль: 0.00 руб.",
            "Общая прибыль: 0.00 руб.",
            profit_positive_color
        )
        count_card, self.period_count_label, self.transaction_count_label = self.create_total_card(
            "Записей за период: 0",
            "Всего записей: 0",
            count_color
        )

        totals_row.addWidget(income_card, 12)
        totals_row.addWidget(expense_card, 12)
        totals_row.addWidget(tax_card, 12)
        totals_row.addWidget(profit_card, 12)
        totals_row.addWidget(count_card, 7)

        totals_layout.addLayout(totals_row)
        totals_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        
        splitter.addWidget(totals_widget)
        
        # Настраиваем разделитель
        splitter.setSizes([0, 500, 120])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        
        main_layout.addWidget(splitter)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")
    
    def create_total_label(self, text: str, color: str) -> QLabel:
        """
        Создать метку для итогов.
        
        Args:
            text: Текст метки
            color: Цвет текста
            
        Returns:
            Созданная метка
        """
        label = QLabel(text)
        label.setStyleSheet(
            f"color: {color}; font-weight: bold; border: none; background: transparent;"
        )
        label_padding_horizontal = self.ui_settings.get_int("totals_label_padding_horizontal", 6)
        label_padding_vertical = self.ui_settings.get_int("totals_label_padding_vertical", 2)
        label.setContentsMargins(
            label_padding_horizontal,
            label_padding_vertical,
            label_padding_horizontal,
            label_padding_vertical,
        )
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def create_total_card(
        self,
        top_text: str,
        bottom_text: str,
        color: str
    ) -> tuple[QWidget, QLabel, QLabel]:
        card = QFrame()
        padding_horizontal = self.ui_settings.get_int("totals_card_padding_horizontal", 8)
        padding_vertical = self.ui_settings.get_int("totals_card_padding_vertical", 6)
        background = self.ui_settings.get_str("totals_card_background", "#f5f5f5")
        border_color = self.ui_settings.get_str("totals_card_border_color", "#e0e0e0")
        card.setStyleSheet("""
            background-color: %s;
            border: 1px solid %s;
            border-radius: 4px;
        """ % (background, border_color) + (
            f"padding: {padding_vertical}px {padding_horizontal}px;"
        ))
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(self.ui_settings.get_int("totals_card_spacing", 4))

        top_label = self.create_total_label(top_text, color)
        bottom_label = self.create_total_label(bottom_text, color)

        card_layout.addWidget(top_label)
        card_layout.addWidget(bottom_label)

        return card, top_label, bottom_label

    def _get_app_version(self) -> str:
        try:
            from solepro import __version__

            return __version__
        except Exception:
            return ""
    
    def create_menu_bar(self) -> None:
        """Создать меню."""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        
        # Обновить
        refresh_action = QAction("🔄 Обновить", self)
        refresh_action.triggered.connect(self.refresh_data)
        refresh_action.setShortcut("Ctrl+R")
        file_menu.addAction(refresh_action)
        
        # Экспорт
        export_action = QAction("📊 Экспорт в Excel", self)
        export_action.triggered.connect(self.export_to_excel)
        export_action.setShortcut("Ctrl+X")
        file_menu.addAction(export_action)

        settings_action = QAction("⚙ Настройки...", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        settings_action.setShortcut("Ctrl+,")
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Выход
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)
        
        # Меню "Данные"
        data_menu = menubar.addMenu("Данные")
        
        # Добавить транзакцию
        add_action = QAction("➕ Добавить транзакцию", self)
        add_action.triggered.connect(self.add_transaction)
        add_action.setShortcut("Ctrl+N")
        data_menu.addAction(add_action)
        
        # Редактировать транзакцию
        edit_action = QAction("✏️ Редактировать транзакцию", self)
        edit_action.triggered.connect(self.edit_transaction)
        edit_action.setShortcut("Ctrl+E")
        data_menu.addAction(edit_action)
        
        # Удалить транзакцию
        delete_action = QAction("🗑️ Удалить транзакцию", self)
        delete_action.triggered.connect(self.delete_transaction)
        delete_action.setShortcut("Ctrl+D")
        data_menu.addAction(delete_action)
        
        data_menu.addSeparator()
        
        # Контрагенты
        counterparties_action = QAction("🏢 Контрагенты", self)
        counterparties_action.triggered.connect(self.manage_counterparties)
        counterparties_action.setShortcut("Ctrl+C")
        data_menu.addAction(counterparties_action)
        
        # Статистика
        stats_action = QAction("📈 Статистика", self)
        stats_action.triggered.connect(self.show_statistics)
        stats_action.setShortcut("Ctrl+S")
        data_menu.addAction(stats_action)

        data_menu.addSeparator()

        self.toggle_filters_action = QAction("🔍 Показать фильтры", self)
        self.toggle_filters_action.triggered.connect(self.toggle_filters)
        self.toggle_filters_action.setShortcut("Ctrl+F")
        data_menu.addAction(self.toggle_filters_action)
        
        # Меню "Справка"
        help_menu = menubar.addMenu("Справка")
        
        # О программе
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self) -> None:
        """Создать панель инструментов."""
        toolbar = QToolBar("Основные инструменты")
        self.addToolBar(toolbar)
        
        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addSeparator()
        
        # Кнопка добавления
        add_btn = QPushButton("➕ Добавить")
        add_btn.clicked.connect(self.add_transaction)
        toolbar.addWidget(add_btn)
        
        # Кнопка редактирования
        edit_btn = QPushButton("✏️ Редактировать")
        edit_btn.clicked.connect(self.edit_transaction)
        toolbar.addWidget(edit_btn)
        
        # Кнопка удаления
        delete_btn = QPushButton("🗑️ Удалить")
        delete_btn.clicked.connect(self.delete_transaction)
        toolbar.addWidget(delete_btn)
        
        toolbar.addSeparator()
        
        # Кнопка контрагентов
        counterparties_btn = QPushButton("🏢 Контрагенты")
        counterparties_btn.clicked.connect(self.manage_counterparties)
        toolbar.addWidget(counterparties_btn)
        
        # Кнопка статистики
        stats_btn = QPushButton("📈 Статистика")
        stats_btn.clicked.connect(self.show_statistics)
        toolbar.addWidget(stats_btn)
        
        toolbar.addSeparator()
        
        # Кнопка экспорта
        export_btn = QPushButton("📊 Экспорт")
        export_btn.clicked.connect(self.export_to_excel)
        toolbar.addWidget(export_btn)
    
    def connect_signals(self) -> None:
        """Подключить сигналы."""
        # Контроллер -> View
        self.controller.data_loaded.connect(self.on_data_loaded)
        self.controller.transaction_added.connect(self.on_transaction_added)
        self.controller.transaction_updated.connect(self.on_transaction_updated)
        self.controller.transaction_deleted.connect(self.on_transaction_deleted)
        self.controller.error_occurred.connect(self.on_error)
        
        # View -> Контроллер
        self.filter_panel.filter_changed.connect(self.on_filter_changed)
        self.filter_panel.filter_cleared.connect(self.on_filter_cleared)
        
        # Таблица транзакций
        self.transaction_table.context_menu_requested.connect(self.on_context_menu_requested)
        self.transaction_table.transaction_double_clicked.connect(
            lambda _: self.edit_transaction()
        )
        
        # Обновление данных
        self.refresh_requested.connect(self.refresh_data)
    
    def load_initial_data(self) -> None:
        """Загрузить начальные данные."""
        self.status_bar.showMessage("Загрузка данных...")
        self.controller.load_transactions(self.filter_panel.get_current_filter())
    
    def refresh_data(self) -> None:
        """Обновить данные."""
        self.controller.load_transactions(self.filter_panel.get_current_filter())
    
    def on_data_loaded(self, transactions: list, statistics: dict) -> None:
        """
        Обработчик загрузки данных.
        
        Args:
            transactions: Список транзакций
            statistics: Статистика
        """
        # Обновляем таблицу
        self.transaction_table.load_transactions(transactions)
        
        # Обновляем итоги за период (с учетом фильтров)
        self.update_period_totals(transactions)

        # Обновляем общие итоги
        if statistics:
            self.update_totals(statistics)
        
        # Обновляем статус
        count = len(transactions)
        self.status_bar.showMessage(f"Загружено {count} записей")
    
    def update_totals(self, statistics: dict) -> None:
        """
        Обновить панель итогов.
        
        Args:
            statistics: Статистика
        """
        # Доход
        total_income = statistics.get("total_income", 0)
        self.total_income_label.setText(f"Общий доход: {float(total_income):,.2f} руб.")
        
        # Расход
        total_expense = statistics.get("total_expense", 0)
        self.total_expense_label.setText(f"Общий расход: {float(total_expense):,.2f} руб.")
        
        # Налог
        total_tax = statistics.get("total_tax", 0)
        self.total_tax_label.setText(f"Общий налог: {float(total_tax):,.2f} руб.")
        
        # Прибыль
        total_profit = statistics.get("total_profit", 0)
        profit_text = f"Общая прибыль: {float(total_profit):,.2f} руб."
        self.total_profit_label.setText(profit_text)
        
        # Цвет прибыли
        if total_profit >= 0:
            self.total_profit_label.setStyleSheet(
                (
                    f"color: {self._totals_profit_positive_color}; "
                    "font-weight: bold; border: none; background: transparent;"
                )
            )
        else:
            self.total_profit_label.setStyleSheet(
                (
                    f"color: {self._totals_profit_negative_color}; "
                    "font-weight: bold; border: none; background: transparent;"
                )
            )
        
        # Количество записей
        count = statistics.get("total_transactions", 0)
        self.transaction_count_label.setText(f"Всего записей: {count}")

    def update_period_totals(self, transactions: list) -> None:
        """Обновить панель итогов за период (по текущему списку транзакций)."""
        total_income = sum(float(t.income) for t in transactions)
        total_expense = sum(float(t.expense) for t in transactions)
        total_tax = sum(float(t.tax) for t in transactions)
        total_profit = sum(float(t.profit) for t in transactions)
        count = len(transactions)

        self.period_income_label.setText(
            f"Текущий доход: {float(total_income):,.2f} руб."
        )
        self.period_expense_label.setText(
            f"Текущий расход: {float(total_expense):,.2f} руб."
        )
        self.period_tax_label.setText(
            f"Текущий налог: {float(total_tax):,.2f} руб."
        )
        self.period_profit_label.setText(
            f"Текущая прибыль: {float(total_profit):,.2f} руб."
        )
        self.period_count_label.setText(f"Записей за период: {count}")
    
    def on_filter_changed(self, filter_dto: TransactionFilterDTO) -> None:
        """
        Обработчик изменения фильтра.
        
        Args:
            filter_dto: Новый фильтр
        """
        self.controller.load_transactions(filter_dto)
    
    def on_filter_cleared(self) -> None:
        """Обработчик очистки фильтров."""
        self.controller.load_transactions()
    
    def on_transaction_added(self, transaction) -> None:
        """
        Обработчик добавления транзакции.
        
        Args:
            transaction: Добавленная транзакция
        """
        self.status_bar.showMessage(f"Транзакция добавлена: {transaction.id}")
    
    def on_transaction_updated(self, transaction) -> None:
        """
        Обработчик обновления транзакции.
        
        Args:
            transaction: Обновленная транзакция
        """
        self.status_bar.showMessage(f"Транзакция обновлена: {transaction.id}")
    
    def on_transaction_deleted(self, transaction_id) -> None:
        """
        Обработчик удаления транзакции.
        
        Args:
            transaction_id: ID удаленной транзакции
        """
        self.status_bar.showMessage(f"Транзакция удалена: {transaction_id}")
    
    def on_error(self, message: str) -> None:
        """
        Обработчик ошибки.
        
        Args:
            message: Сообщение об ошибке
        """
        QMessageBox.critical(self, "Ошибка", message)
        self.status_bar.showMessage(f"Ошибка: {message}")
    
    def on_context_menu_requested(self, action: str, data: dict) -> None:
        """
        Обработчик запроса контекстного меню.
        
        Args:
            action: Действие
            data: Данные
        """
        if action == "delete":
            transaction_id = data.get("transaction_id")
            if transaction_id:
                self.delete_transaction_by_id(transaction_id)
    
    def add_transaction(self) -> None:
        """Добавить транзакцию."""
        # Загружаем контрагентов
        counterparties_result = self.controller.load_counterparties()
        
        # Создаем диалог
        dialog = TransactionDialog(
            transaction=None,
            counterparties=counterparties_result.counterparties,
            add_counterparty_callback=self.controller.add_counterparty,
            parent=self
        )
        
        # Подключаем сигнал сохранения
        dialog.transaction_saved.connect(self.on_transaction_saved)
        
        # Показываем диалог
        if dialog.exec():
            # Данные уже обработаны через сигнал
            pass
    
    def edit_transaction(self) -> None:
        """Редактировать транзакцию."""
        # Получаем выбранную транзакцию
        transaction = self.transaction_table.get_selected_transaction()
        if not transaction:
            QMessageBox.warning(self, "Внимание", "Выберите транзакцию для редактирования")
            return

        from uuid import UUID
        try:
            transaction_id = transaction.id if isinstance(transaction.id, UUID) else UUID(str(transaction.id))
        except (ValueError, TypeError):
            transaction_id = None

        if transaction_id:
            fresh_transaction = self.controller.get_transaction(transaction_id)
            if fresh_transaction:
                transaction = fresh_transaction
        
        # Загружаем контрагентов
        counterparties_result = self.controller.load_counterparties()
        
        # Создаем диалог
        dialog = TransactionDialog(
            transaction=transaction,
            counterparties=counterparties_result.counterparties,
            add_counterparty_callback=self.controller.add_counterparty,
            parent=self
        )
        
        # Подключаем сигнал сохранения
        dialog.transaction_saved.connect(self.on_transaction_saved)
        
        # Показываем диалог
        if dialog.exec():
            # Данные уже обработаны через сигнал
            pass
    
    def on_transaction_saved(self, data: dict) -> None:
        """
        Обработчик сохранения транзакции.
        
        Args:
            data: Данные транзакции
        """
        from uuid import UUID
        
        transaction_data = data["data"]
        is_edit = data["is_edit"]
        
        if is_edit:
            # Редактирование
            transaction_id = data["transaction"].id
            if not isinstance(transaction_id, UUID):
                transaction_id = UUID(str(transaction_id))
            self.controller.update_transaction(transaction_id, transaction_data)
        else:
            # Добавление
            self.controller.add_transaction(transaction_data)
    
    def delete_transaction(self) -> None:
        """Удалить транзакцию."""
        # Получаем выбранную транзакцию
        transaction = self.transaction_table.get_selected_transaction()
        if not transaction:
            QMessageBox.warning(self, "Внимание", "Выберите транзакцию для удаления")
            return
        
        self.delete_transaction_by_id(str(transaction.id))
    
    def delete_transaction_by_id(self, transaction_id: str) -> None:
        """
        Удалить транзакцию по ID.
        
        Args:
            transaction_id: ID транзакции
        """
        from uuid import UUID
        
        # Подтверждение
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить эту транзакцию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_transaction(UUID(transaction_id))
    
    def manage_counterparties(self) -> None:
        """Управление контрагентами."""
        dialog = CounterpartyManagerDialog(self.controller, self)
        dialog.exec()
    
    def show_statistics(self) -> None:
        """Показать статистику."""
        statistics = self.controller.get_transaction_statistics()
        if not statistics:
            QMessageBox.warning(self, "Внимание", "Не удалось загрузить статистику")
            return

        filtered_statistics = self.controller.get_transaction_statistics(
            self.filter_panel.get_current_filter()
        )
        if filtered_statistics:
            statistics = statistics.model_copy(update={
                "total_transactions": filtered_statistics.total_transactions,
                "total_income": filtered_statistics.total_income,
                "total_expense": filtered_statistics.total_expense,
                "total_tax": filtered_statistics.total_tax,
                "total_profit": filtered_statistics.total_profit,
                "avg_income": filtered_statistics.avg_income,
                "avg_expense": filtered_statistics.avg_expense,
                "avg_tax": filtered_statistics.avg_tax,
                "avg_profit": filtered_statistics.avg_profit,
                "first_transaction_date": filtered_statistics.first_transaction_date,
                "last_transaction_date": filtered_statistics.last_transaction_date,
                "monthly_statistics": filtered_statistics.monthly_statistics,
                "period_comparison": filtered_statistics.period_comparison,
                "income_transaction_count": filtered_statistics.income_transaction_count,
                "expense_transaction_count": filtered_statistics.expense_transaction_count,
                "mixed_transaction_count": filtered_statistics.mixed_transaction_count,
            })

        counterparty_stats = self.controller.get_counterparty_statistics(
            self.filter_panel.get_current_filter()
        )
        if counterparty_stats:
            statistics = statistics.model_copy(update={"top_counterparties": counterparty_stats})

        period_text = self._build_statistics_period_text(statistics)
        dialog = StatisticsDialog(statistics, self, period_text=period_text)
        dialog.exec()

    def _build_statistics_period_text(self, statistics) -> str:
        filter_dto = self.filter_panel.get_current_filter()
        period_start = None
        period_end = None

        if filter_dto and filter_dto.show_all:
            period_start = statistics.first_transaction_date
            period_end = datetime.now() if statistics.first_transaction_date else None
        else:
            if filter_dto:
                period_start = filter_dto.start_date
                period_end = filter_dto.end_date

        if period_start is None or period_end is None:
            if statistics.total_transactions == 0:
                return "Нет данных за период"
            today = datetime.now().date()
            period_start = period_start or datetime(today.year, 1, 1).date()
            period_end = period_end or today

        if isinstance(period_start, datetime):
            period_start = period_start.date()
        if isinstance(period_end, datetime):
            period_end = period_end.date()

        start_text = period_start.strftime("%d.%m.%Y")
        end_text = period_end.strftime("%d.%m.%Y")
        return (
            "Статистика показана за период с "
            f"{start_text} по {end_text}.\n"
            "Для изменения периода используйте Фильтры (меню Данные - Показать фильтры)"
        )

    def toggle_filters(self) -> None:
        """Показать или скрыть панель фильтров."""
        if not hasattr(self, "main_splitter"):
            return
        sizes = self.main_splitter.sizes()
        if not sizes or len(sizes) < 3:
            self.main_splitter.setSizes([180, 500, 50])
            self._update_filters_toggle_text(True)
            return
        if sizes[0] == 0:
            self.main_splitter.setSizes([180, sizes[1], sizes[2]])
            self._update_filters_toggle_text(True)
        else:
            self.main_splitter.setSizes([0, sizes[1], sizes[2]])
            self._update_filters_toggle_text(False)

    def _update_filters_toggle_text(self, is_visible: bool) -> None:
        if hasattr(self, "toggle_filters_action"):
            text = "🔍 Скрыть фильтры" if is_visible else "🔍 Показать фильтры"
            self.toggle_filters_action.setText(text)
    
    def export_to_excel(self) -> None:
        """Экспортировать данные в Excel."""
        # Диалог выбора файла
        from pathlib import Path
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт в Excel",
            str(Path.home() / "Desktop" / "Финансы_ИП.xlsx"),
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not filepath:
            return
        
        # Добавляем расширение если нужно
        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'
        
        # Экспортируем
        success = self.controller.export_to_excel(filepath)
        
        if success:
            QMessageBox.information(
                self,
                "Экспорт завершен",
                f"Данные успешно экспортированы в файл:\n{filepath}"
            )
            self.status_bar.showMessage(f"Данные экспортированы: {Path(filepath).name}")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось экспортировать данные")

    def open_settings_dialog(self) -> None:
        """Открыть окно настроек."""
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def show_about(self) -> None:
        """Показать информацию о программе."""
        version = self._get_app_version() or "unknown"
        QMessageBox.about(
            self,
            "О программе",
            "SolePro Finance Assistant\n\n"
            "Десктопное приложение для учета финансов ИП.\n"
            "Построено на принципах Clean Architecture.\n\n"
            f"Версия: {version}\n"
            "© 2026 SolePro Finance Assistant"
        )
    
    def closeEvent(self, event) -> None:
        """Обработчик закрытия окна."""
        # Останавливаем таймер
        self.refresh_timer.stop()
        
        # Подтверждение выхода
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите выйти?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
