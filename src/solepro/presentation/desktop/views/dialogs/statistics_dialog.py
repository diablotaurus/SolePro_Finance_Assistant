"""
Диалог со статистикой.
"""
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QWidget,
    QGridLayout,
    QGroupBox,
    QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath

from .....core.application.dto.statistics_dto import StatisticsDTO
from ...ui_settings import DesktopUiSettings, TableUiConfigurator


class MonthlyTrendChart(QWidget):
    """Простой виджет графика трендов без внешних зависимостей."""

    def __init__(
        self,
        parent=None,
        min_height: int = 280,
        colors: Optional[dict[str, QColor]] = None,
        neutral_color: QColor = QColor("#666666"),
    ):
        super().__init__(parent)
        self.setMinimumHeight(min_height)
        self._rows: list[dict] = []
        self._mode = "lines"
        self._neutral_color = neutral_color
        self._colors = colors or {
            "income": QColor("#2e7d32"),
            "expense": QColor("#c62828"),
            "tax": QColor("#1565c0"),
            "profit": QColor("#6a1b9a"),
        }

    def set_data(self, rows: list[dict]) -> None:
        self._rows = rows
        self.update()

    def set_mode(self, mode: str) -> None:
        self._mode = mode if mode in ("lines", "bars") else "lines"
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(40, 20, -20, -40)
        if rect.width() <= 0 or rect.height() <= 0:
            return

        painter.setPen(QPen(QColor("#d0d0d0"), 1))
        painter.drawRect(rect)

        if not self._rows:
            painter.setPen(QPen(self._neutral_color, 1))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Нет данных для трендов")
            return

        values = []
        for row in self._rows:
            values.extend([
                abs(float(row.get("income", 0.0))),
                abs(float(row.get("expense", 0.0))),
                abs(float(row.get("tax", 0.0))),
                abs(float(row.get("profit", 0.0))),
            ])
        max_value = max(values) if values else 0.0
        if max_value <= 0:
            max_value = 1.0

        months_count = len(self._rows)
        x_step = rect.width() / max(months_count - 1, 1)

        painter.setPen(QPen(QColor("#efefef"), 1))
        for i in range(1, 5):
            y = rect.bottom() - (rect.height() * i / 5)
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))

        if self._mode == "bars":
            self._paint_bars(painter, rect, max_value)
        else:
            self._paint_lines(painter, rect, x_step, max_value)

        painter.setPen(QPen(self._neutral_color, 1))
        labels = [row.get("label", "") for row in self._rows]
        for index, label in enumerate(labels):
            x = rect.left() + index * x_step
            painter.drawText(int(x - 18), rect.bottom() + 18, label)

    def _paint_lines(self, painter: QPainter, rect, x_step: float, max_value: float) -> None:
        series = ("income", "expense", "tax", "profit")
        for key in series:
            path = QPainterPath()
            for index, row in enumerate(self._rows):
                value = abs(float(row.get(key, 0.0)))
                x = rect.left() + index * x_step
                y = rect.bottom() - (value / max_value) * rect.height()
                if index == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            painter.setPen(QPen(self._colors[key], 2))
            painter.drawPath(path)

    def _paint_bars(self, painter: QPainter, rect, max_value: float) -> None:
        series = ("income", "expense", "tax", "profit")
        months_count = len(self._rows)
        group_width = rect.width() / max(months_count, 1)
        bar_width = max(group_width / 6, 4)
        for index, row in enumerate(self._rows):
            x0 = rect.left() + index * group_width + group_width * 0.1
            for series_index, key in enumerate(series):
                value = abs(float(row.get(key, 0.0)))
                height = (value / max_value) * rect.height()
                x = x0 + series_index * (bar_width + 2)
                y = rect.bottom() - height
                painter.fillRect(int(x), int(y), int(bar_width), int(height), self._colors[key])


class CounterpartyConcentrationChart(QWidget):
    """Горизонтальный бар-чарт прибыли по контрагентам."""

    def __init__(
        self,
        parent=None,
        min_height: int = 260,
        profit_positive_color: QColor = QColor("#2e7d32"),
        profit_negative_color: QColor = QColor("#c62828"),
        neutral_color: QColor = QColor("#666666"),
    ):
        super().__init__(parent)
        self.setMinimumHeight(min_height)
        self._rows: list[dict] = []
        self._profit_positive_color = profit_positive_color
        self._profit_negative_color = profit_negative_color
        self._neutral_color = neutral_color

    def set_data(self, rows: list[dict]) -> None:
        self._rows = rows[:8]
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(20, 20, -20, -20)
        if rect.width() <= 0 or rect.height() <= 0:
            return

        if not self._rows:
            painter.setPen(QPen(self._neutral_color, 1))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Нет данных по контрагентам")
            return

        max_abs_profit = max(abs(float(row.get("profit", 0.0))) for row in self._rows) or 1.0
        line_height = max(rect.height() // len(self._rows), 22)
        name_width = int(rect.width() * 0.42)
        bar_left = rect.left() + name_width + 12
        bar_max_width = rect.right() - bar_left - 70
        baseline_x = bar_left + int(bar_max_width * 0.5)

        for index, row in enumerate(self._rows):
            y = rect.top() + index * line_height
            name = str(row.get("name", ""))[:30]
            profit = float(row.get("profit", 0.0))
            bar_width = int(abs(profit) / max_abs_profit * (bar_max_width * 0.5))

            painter.setPen(QPen(QColor("#333333"), 1))
            painter.drawText(rect.left(), y + 15, name)

            painter.fillRect(bar_left, y + 3, bar_max_width, 12, QColor("#f0f0f0"))
            painter.setPen(QPen(QColor("#cfcfcf"), 1))
            painter.drawLine(baseline_x, y + 2, baseline_x, y + 16)

            if profit >= 0:
                painter.fillRect(
                    baseline_x,
                    y + 3,
                    bar_width,
                    12,
                    self._profit_positive_color,
                )
            else:
                painter.fillRect(
                    baseline_x - bar_width,
                    y + 3,
                    bar_width,
                    12,
                    self._profit_negative_color,
                )

            painter.setPen(QPen(QColor("#444444"), 1))
            painter.drawText(bar_left + bar_max_width + 8, y + 15, f"{profit:,.0f}")


class TaxBurdenChart(QWidget):
    """Линейный график эффективной ставки налога по месяцам."""

    def __init__(
        self,
        parent=None,
        min_height: int = 250,
        tax_color: QColor = QColor("#1565c0"),
        neutral_color: QColor = QColor("#666666"),
    ):
        super().__init__(parent)
        self.setMinimumHeight(min_height)
        self._rows: list[dict] = []
        self._tax_color = tax_color
        self._neutral_color = neutral_color

    def set_data(self, rows: list[dict]) -> None:
        self._rows = rows
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(40, 20, -20, -40)
        if rect.width() <= 0 or rect.height() <= 0:
            return

        painter.setPen(QPen(QColor("#d0d0d0"), 1))
        painter.drawRect(rect)

        if not self._rows:
            painter.setPen(QPen(self._neutral_color, 1))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Нет данных по налоговой нагрузке")
            return

        max_rate = max(float(row.get("effective_tax_rate", 0.0)) for row in self._rows)
        max_rate = max(max_rate, 1.0)
        count = len(self._rows)
        x_step = rect.width() / max(count - 1, 1)

        painter.setPen(QPen(QColor("#efefef"), 1))
        for i in range(1, 5):
            y = rect.bottom() - (rect.height() * i / 5)
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))

        path = QPainterPath()
        for idx, row in enumerate(self._rows):
            rate = float(row.get("effective_tax_rate", 0.0))
            x = rect.left() + idx * x_step
            y = rect.bottom() - (rate / max_rate) * rect.height()
            if idx == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        painter.setPen(QPen(self._tax_color, 2))
        painter.drawPath(path)

        painter.setPen(QPen(self._neutral_color, 1))
        for idx, row in enumerate(self._rows):
            label = row.get("label", "")
            x = rect.left() + idx * x_step
            painter.drawText(int(x - 18), rect.bottom() + 18, label)


class SortableNumericItem(QTableWidgetItem):
    """QTableWidgetItem with numeric-aware sorting."""

    def __init__(self, text: str, value: float):
        super().__init__(text)
        self._sort_value = float(value)

    def __lt__(self, other) -> bool:  # noqa: N802 (Qt API)
        if isinstance(other, SortableNumericItem):
            return self._sort_value < other._sort_value
        return super().__lt__(other)


class StatisticsDialog(QDialog):
    """Диалог для отображения статистики."""
    
    def __init__(self, statistics: StatisticsDTO, parent=None, period_text: str = ""):
        super().__init__(parent)
        self.statistics = statistics
        self.period_text = period_text
        self.ui_settings = DesktopUiSettings(__file__, project_root_parent_index=6)
        self.table_ui = TableUiConfigurator(self.ui_settings)
        self.income_color = self.ui_settings.get_str("color_income", "#2e7d32")
        self.expense_color = self.ui_settings.get_str("color_expense", "#c62828")
        self.tax_color = self.ui_settings.get_str("color_tax", "#1565c0")
        self.profit_positive_color = self.ui_settings.get_str("color_profit_positive", "#2e7d32")
        self.profit_negative_color = self.ui_settings.get_str("color_profit_negative", "#c62828")
        self.neutral_color = self.ui_settings.get_str("color_neutral", "#666666")
        self.chart_monthly_min_height = self.ui_settings.get_int("chart_monthly_min_height", 280)
        self.chart_concentration_min_height = self.ui_settings.get_int(
            "chart_concentration_min_height",
            260,
        )
        self.chart_tax_min_height = self.ui_settings.get_int("chart_tax_min_height", 250)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self) -> None:
        """Настроить UI диалога."""
        self.setWindowTitle("Статистика")
        self.setMinimumSize(
            self.ui_settings.get_int("dialog_statistics_min_width", 800),
            self.ui_settings.get_int("dialog_statistics_min_height", 600),
        )
        
        layout = QVBoxLayout(self)
        
        # Вкладки
        self.tab_widget = QTabWidget()
        
        # Общая статистика
        self.general_tab = QWidget()
        self.setup_general_tab()
        self.tab_widget.addTab(self.general_tab, "Общая")
        
        # Статистика по годам
        self.yearly_tab = QWidget()
        self.setup_yearly_tab()
        self.tab_widget.addTab(self.yearly_tab, "По годам")

        self.trends_tab = QWidget()
        self.setup_trends_tab()
        self.tab_widget.addTab(self.trends_tab, "Тренды")
        
        # Топ контрагентов
        self.counterparties_tab = QWidget()
        self.setup_counterparties_tab()
        self.tab_widget.addTab(self.counterparties_tab, "Топ контрагентов")

        self.tax_tab = QWidget()
        self.setup_tax_tab()
        self.tab_widget.addTab(self.tax_tab, "Налоги")
        
        layout.addWidget(self.tab_widget)
    
    def setup_general_tab(self) -> None:
        """Настроить вкладку общей статистики."""
        layout = QGridLayout(self.general_tab)
        
        # Ключевые показатели
        key_indicators_group = QGroupBox("Ключевые показатели")
        key_layout = QGridLayout()
        
        # Общее количество транзакций
        self.total_transactions_label = QLabel("0")
        self.total_transactions_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        key_layout.addWidget(QLabel("Всего транзакций:"), 0, 0)
        key_layout.addWidget(self.total_transactions_label, 0, 1)
        
        # Общий доход
        self.total_income_label = QLabel("0.00 руб.")
        self.total_income_label.setStyleSheet(
            f"font-size: 18pt; font-weight: bold; color: {self.income_color};"
        )
        key_layout.addWidget(QLabel("Общий доход:"), 1, 0)
        key_layout.addWidget(self.total_income_label, 1, 1)
        
        # Общий расход
        self.total_expense_label = QLabel("0.00 руб.")
        self.total_expense_label.setStyleSheet(
            f"font-size: 18pt; font-weight: bold; color: {self.expense_color};"
        )
        key_layout.addWidget(QLabel("Общий расход:"), 2, 0)
        key_layout.addWidget(self.total_expense_label, 2, 1)
        
        # Общий налог
        self.total_tax_label = QLabel("0.00 руб.")
        self.total_tax_label.setStyleSheet(
            f"font-size: 18pt; font-weight: bold; color: {self.tax_color};"
        )
        key_layout.addWidget(QLabel("Общий налог:"), 3, 0)
        key_layout.addWidget(self.total_tax_label, 3, 1)
        
        # Общая прибыль
        self.total_profit_label = QLabel("0.00 руб.")
        self.total_profit_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        key_layout.addWidget(QLabel("Общая прибыль:"), 4, 0)
        key_layout.addWidget(self.total_profit_label, 4, 1)
        
        key_indicators_group.setLayout(key_layout)
        layout.addWidget(key_indicators_group, 2, 0, 1, 2)
        
        # Средние значения
        averages_group = QGroupBox("Средние значения")
        avg_layout = QGridLayout()
        
        # Средний доход
        self.avg_income_label = QLabel("0.00 руб.")
        avg_layout.addWidget(QLabel("Средний доход:"), 0, 0)
        avg_layout.addWidget(self.avg_income_label, 0, 1)
        
        # Средний расход
        self.avg_expense_label = QLabel("0.00 руб.")
        avg_layout.addWidget(QLabel("Средний расход:"), 1, 0)
        avg_layout.addWidget(self.avg_expense_label, 1, 1)
        
        # Средний налог
        self.avg_tax_label = QLabel("0.00 руб.")
        avg_layout.addWidget(QLabel("Средний налог:"), 2, 0)
        avg_layout.addWidget(self.avg_tax_label, 2, 1)
        
        # Средняя прибыль
        self.avg_profit_label = QLabel("0.00 руб.")
        avg_layout.addWidget(QLabel("Средняя прибыль:"), 3, 0)
        avg_layout.addWidget(self.avg_profit_label, 3, 1)
        
        averages_group.setLayout(avg_layout)
        layout.addWidget(averages_group, 1, 0)
        
        # Статистика по типам транзакций
        types_group = QGroupBox("Статистика по типам транзакций")
        types_layout = QGridLayout()
        
        # Количество доходных транзакций
        self.income_count_label = QLabel("0")
        types_layout.addWidget(QLabel("Доходных транзакций:"), 0, 0)
        types_layout.addWidget(self.income_count_label, 0, 1)
        
        # Количество расходных транзакций
        self.expense_count_label = QLabel("0")
        types_layout.addWidget(QLabel("Расходных транзакций:"), 1, 0)
        types_layout.addWidget(self.expense_count_label, 1, 1)
        
        # Количество смешанных транзакций
        self.mixed_count_label = QLabel("0")
        types_layout.addWidget(QLabel("Смешанных транзакций:"), 2, 0)
        types_layout.addWidget(self.mixed_count_label, 2, 1)
        
        types_group.setLayout(types_layout)
        layout.addWidget(types_group, 1, 1)
        
        # Период
        dates_group = QGroupBox("Период")
        dates_layout = QGridLayout()

        self.period_description_label = QLabel("-")
        self.period_description_label.setWordWrap(True)
        self.period_description_label.setStyleSheet(
            "padding-bottom: 8px; font-weight: bold;"
        )
        dates_layout.addWidget(self.period_description_label, 0, 0)
        
        dates_group.setLayout(dates_layout)
        layout.addWidget(dates_group, 0, 0, 1, 2)

        comparison_group = QGroupBox("Сравнение с предыдущим периодом")
        comparison_layout = QGridLayout()
        self.comparison_period_label = QLabel("-")
        self.comparison_period_label.setWordWrap(True)
        comparison_layout.addWidget(self.comparison_period_label, 0, 0, 1, 2)

        self.comparison_income_label = QLabel("-")
        comparison_layout.addWidget(QLabel("Доход:"), 1, 0)
        comparison_layout.addWidget(self.comparison_income_label, 1, 1)

        self.comparison_expense_label = QLabel("-")
        comparison_layout.addWidget(QLabel("Расход:"), 2, 0)
        comparison_layout.addWidget(self.comparison_expense_label, 2, 1)

        self.comparison_tax_label = QLabel("-")
        comparison_layout.addWidget(QLabel("Налог:"), 3, 0)
        comparison_layout.addWidget(self.comparison_tax_label, 3, 1)

        self.comparison_profit_label = QLabel("-")
        comparison_layout.addWidget(QLabel("Прибыль:"), 4, 0)
        comparison_layout.addWidget(self.comparison_profit_label, 4, 1)

        self.comparison_transactions_label = QLabel("-")
        comparison_layout.addWidget(QLabel("Транзакции:"), 5, 0)
        comparison_layout.addWidget(self.comparison_transactions_label, 5, 1)

        comparison_group.setLayout(comparison_layout)
        layout.addWidget(comparison_group, 3, 0, 1, 2)

        layout.setRowStretch(2, 1)
    
    def setup_yearly_tab(self) -> None:
        """Настроить вкладку статистики по годам."""
        layout = QVBoxLayout(self.yearly_tab)

        # Таблица
        self.yearly_table = QTableWidget()
        self.yearly_table.setColumnCount(6)
        self.yearly_table.setHorizontalHeaderLabels([
            "Год",
            "Доход",
            "Расход",
            "Налог",
            "Прибыль",
            "Транзакций"
        ])

        # Настройки таблицы
        header = self.yearly_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_ui.apply_vertical_header(self.yearly_table, "yearlyVerticalHeader")
        self.table_ui.apply_row_heights(self.yearly_table)

        layout.addWidget(self.yearly_table)
    
    def setup_counterparties_tab(self) -> None:
        """Настроить объединенную вкладку топа и портфеля контрагентов."""
        layout = QVBoxLayout(self.counterparties_tab)

        kpi_group = QGroupBox("Метрики портфеля")
        kpi_layout = QGridLayout()

        self.portfolio_active_counterparties_label = QLabel("-")
        self.portfolio_avg_margin_label = QLabel("-")
        self.portfolio_best_counterparty_label = QLabel("-")
        self.portfolio_median_profit_label = QLabel("-")

        kpi_layout.addWidget(QLabel("Активных контрагентов:"), 0, 0)
        kpi_layout.addWidget(self.portfolio_active_counterparties_label, 0, 1)
        kpi_layout.addWidget(QLabel("Средняя маржа по портфелю:"), 1, 0)
        kpi_layout.addWidget(self.portfolio_avg_margin_label, 1, 1)
        kpi_layout.addWidget(QLabel("Лучший по прибыли:"), 0, 2)
        kpi_layout.addWidget(self.portfolio_best_counterparty_label, 0, 3)
        kpi_layout.addWidget(QLabel("Медианная прибыль:"), 1, 2)
        kpi_layout.addWidget(self.portfolio_median_profit_label, 1, 3)

        kpi_group.setLayout(kpi_layout)
        layout.addWidget(kpi_group)

        self.concentration_chart = CounterpartyConcentrationChart(
            min_height=self.chart_concentration_min_height,
            profit_positive_color=QColor(self.profit_positive_color),
            profit_negative_color=QColor(self.profit_negative_color),
            neutral_color=QColor(self.neutral_color),
        )
        layout.addWidget(self.concentration_chart)

        self.counterparties_table = QTableWidget()
        self.counterparties_table.setColumnCount(7)
        self.counterparties_table.setHorizontalHeaderLabels([
            "Контрагент",
            "Доход",
            "Расход",
            "Налог",
            "Прибыль",
            "Маржа %",
            "Транзакций",
        ])
        
        # Настройки таблицы
        header = self.counterparties_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Контрагент
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Доход
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Расход
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Налог
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Прибыль
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Маржа %
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Транзакций
        self.table_ui.apply_vertical_header(
            self.counterparties_table,
            "counterpartiesVerticalHeader",
        )
        self.table_ui.apply_row_heights(self.counterparties_table)
        self.counterparties_table.setSortingEnabled(True)
        
        layout.addWidget(self.counterparties_table)

    def setup_concentration_tab(self) -> None:
        """Настроить вкладку портфеля контрагентов."""
        layout = QVBoxLayout(self.concentration_tab)

        kpi_group = QGroupBox("Метрики портфеля")
        kpi_layout = QGridLayout()

        self.portfolio_active_counterparties_label = QLabel("-")
        self.portfolio_avg_margin_label = QLabel("-")
        self.portfolio_best_counterparty_label = QLabel("-")
        self.portfolio_median_profit_label = QLabel("-")

        kpi_layout.addWidget(QLabel("Активных контрагентов:"), 0, 0)
        kpi_layout.addWidget(self.portfolio_active_counterparties_label, 0, 1)
        kpi_layout.addWidget(QLabel("Средняя маржа по портфелю:"), 1, 0)
        kpi_layout.addWidget(self.portfolio_avg_margin_label, 1, 1)
        kpi_layout.addWidget(QLabel("Лучший по прибыли:"), 0, 2)
        kpi_layout.addWidget(self.portfolio_best_counterparty_label, 0, 3)
        kpi_layout.addWidget(QLabel("Медианная прибыль:"), 1, 2)
        kpi_layout.addWidget(self.portfolio_median_profit_label, 1, 3)

        kpi_group.setLayout(kpi_layout)
        layout.addWidget(kpi_group)

        self.concentration_chart = CounterpartyConcentrationChart(
            min_height=self.chart_concentration_min_height,
            profit_positive_color=QColor(self.profit_positive_color),
            profit_negative_color=QColor(self.profit_negative_color),
            neutral_color=QColor(self.neutral_color),
        )
        layout.addWidget(self.concentration_chart)

        self.concentration_table = QTableWidget()
        self.concentration_table.setColumnCount(7)
        self.concentration_table.setHorizontalHeaderLabels(
            ["Контрагент", "Доход", "Расход", "Налог", "Прибыль", "Маржа %", "Транзакций"]
        )
        header = self.concentration_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table_ui.apply_vertical_header(
            self.concentration_table,
            "concentrationVerticalHeader",
        )
        self.table_ui.apply_row_heights(self.concentration_table)
        layout.addWidget(self.concentration_table)

    def setup_tax_tab(self) -> None:
        """Настроить вкладку налоговой аналитики."""
        layout = QVBoxLayout(self.tax_tab)

        kpi_group = QGroupBox("Налоговые KPI")
        kpi_layout = QGridLayout()
        self.tax_effective_rate_label = QLabel("-")
        self.tax_burden_label = QLabel("-")
        self.tax_run_rate_label = QLabel("-")
        self.tax_risk_label = QLabel("-")
        self.tax_forecast_label = QLabel("-")

        kpi_layout.addWidget(QLabel("Эффективная ставка (налог / доход):"), 0, 0)
        kpi_layout.addWidget(self.tax_effective_rate_label, 0, 1)
        kpi_layout.addWidget(QLabel("Налоговая нагрузка (налог / прибыль):"), 1, 0)
        kpi_layout.addWidget(self.tax_burden_label, 1, 1)
        kpi_layout.addWidget(QLabel("Средний налог в месяц (run-rate):"), 2, 0)
        kpi_layout.addWidget(self.tax_run_rate_label, 2, 1)
        kpi_layout.addWidget(QLabel("Прогноз налога на след. месяц:"), 0, 2)
        kpi_layout.addWidget(self.tax_forecast_label, 0, 3)
        kpi_layout.addWidget(QLabel("Уровень налоговой нагрузки:"), 1, 2)
        kpi_layout.addWidget(self.tax_risk_label, 1, 3)

        kpi_group.setLayout(kpi_layout)
        layout.addWidget(kpi_group)

        self.tax_chart = TaxBurdenChart(
            min_height=self.chart_tax_min_height,
            tax_color=QColor(self.tax_color),
            neutral_color=QColor(self.neutral_color),
        )
        layout.addWidget(self.tax_chart)

        self.tax_table = QTableWidget()
        self.tax_table.setColumnCount(6)
        self.tax_table.setHorizontalHeaderLabels(
            ["Месяц", "Доход", "Налог", "Прибыль", "Ставка налога", "Налог/Прибыль"]
        )
        self.tax_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_ui.apply_vertical_header(self.tax_table, "taxVerticalHeader")
        self.table_ui.apply_row_heights(self.tax_table)
        layout.addWidget(self.tax_table)

    def setup_trends_tab(self) -> None:
        """Настроить вкладку трендов по месяцам."""
        layout = QVBoxLayout(self.trends_tab)

        controls_row = QHBoxLayout()
        controls_row.addWidget(QLabel("Режим графика:"))
        self.trend_mode_combo = QComboBox()
        self.trend_mode_combo.addItem("Линии", "lines")
        self.trend_mode_combo.addItem("Столбцы", "bars")
        self.trend_mode_combo.currentIndexChanged.connect(self.on_trend_mode_changed)
        controls_row.addWidget(self.trend_mode_combo)
        controls_row.addStretch()
        layout.addLayout(controls_row)

        self.trend_chart = MonthlyTrendChart(
            min_height=self.chart_monthly_min_height,
            colors={
                "income": QColor(self.income_color),
                "expense": QColor(self.expense_color),
                "tax": QColor(self.tax_color),
                "profit": QColor(self.profit_positive_color),
            },
            neutral_color=QColor(self.neutral_color),
        )
        layout.addWidget(self.trend_chart)

        self.monthly_details_table = QTableWidget()
        self.monthly_details_table.setColumnCount(5)
        self.monthly_details_table.setHorizontalHeaderLabels(
            ["Месяц", "Доход", "Расход", "Налог", "Прибыль"]
        )
        self.monthly_details_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table_ui.apply_vertical_header(
            self.monthly_details_table,
            "monthlyDetailsVerticalHeader",
        )
        self.table_ui.apply_row_heights(self.monthly_details_table)
        layout.addWidget(self.monthly_details_table)
    
    def load_data(self) -> None:
        """Загрузить данные статистики."""
        # Общая статистика
        self.total_transactions_label.setText(str(self.statistics.total_transactions))
        self.total_income_label.setText(f"{float(self.statistics.total_income):,.2f} руб.")
        self.total_expense_label.setText(f"{float(self.statistics.total_expense):,.2f} руб.")
        self.total_tax_label.setText(f"{float(self.statistics.total_tax):,.2f} руб.")
        
        total_profit = float(self.statistics.total_profit)
        self.total_profit_label.setText(f"{total_profit:,.2f} руб.")
        
        # Цвет прибыли
        if total_profit >= 0:
            self.total_profit_label.setStyleSheet(
                (
                    "font-size: 18pt; font-weight: bold; color: "
                    f"{self.profit_positive_color};"
                )
            )
        else:
            self.total_profit_label.setStyleSheet(
                (
                    "font-size: 18pt; font-weight: bold; color: "
                    f"{self.profit_negative_color};"
                )
            )
        
        # Средние значения
        if self.statistics.avg_income is not None:
            self.avg_income_label.setText(f"{float(self.statistics.avg_income):,.2f} руб.")
        else:
            self.avg_income_label.setText("-")
        
        if self.statistics.avg_expense is not None:
            self.avg_expense_label.setText(f"{float(self.statistics.avg_expense):,.2f} руб.")
        else:
            self.avg_expense_label.setText("-")
        
        if self.statistics.avg_tax is not None:
            self.avg_tax_label.setText(f"{float(self.statistics.avg_tax):,.2f} руб.")
        else:
            self.avg_tax_label.setText("-")
        
        if self.statistics.avg_profit is not None:
            avg_profit = float(self.statistics.avg_profit)
            self.avg_profit_label.setText(f"{avg_profit:,.2f} руб.")
            
            # Цвет средней прибыли
            if avg_profit >= 0:
                self.avg_profit_label.setStyleSheet(
                    f"color: {self.profit_positive_color};"
                )
            else:
                self.avg_profit_label.setStyleSheet(
                    f"color: {self.profit_negative_color};"
                )
        else:
            self.avg_profit_label.setText("-")
        
        # Статистика по типам
        self.income_count_label.setText(str(self.statistics.income_transaction_count))
        self.expense_count_label.setText(str(self.statistics.expense_transaction_count))
        self.mixed_count_label.setText(str(self.statistics.mixed_transaction_count))
        
        # Период
        if self.period_text:
            self.period_description_label.setText(self.period_text)
        self.load_period_comparison()
        
        # Статистика по годам
        self.load_yearly_statistics()

        # Тренды по месяцам
        self.load_trends_statistics()
        
        # Топ контрагентов
        self.load_counterparties_statistics()

        # Налоговая аналитика
        self.load_tax_statistics()
    
    def load_yearly_statistics(self) -> None:
        """Загрузить статистику по годам."""
        if not self.statistics.monthly_statistics:
            self.yearly_table.setRowCount(1)
            item = QTableWidgetItem("Нет данных")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.yearly_table.setItem(0, 0, item)
            self.yearly_table.setSpan(0, 0, 1, 6)
            return

        yearly_stats = {}
        for monthly in self.statistics.monthly_statistics:
            stats = yearly_stats.setdefault(
                monthly.year,
                {"income": 0.0, "expense": 0.0, "tax": 0.0, "profit": 0.0, "count": 0},
            )
            stats["income"] += float(monthly.income)
            stats["expense"] += float(monthly.expense)
            stats["tax"] += float(monthly.tax)
            stats["profit"] += float(monthly.profit)
            stats["count"] += int(monthly.transaction_count)

        years = sorted(yearly_stats.keys())
        self.yearly_table.setRowCount(len(years))

        for row, year in enumerate(years):
            stats = yearly_stats[year]
            # Год
            year_item = QTableWidgetItem(str(year))
            year_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.yearly_table.setItem(row, 0, year_item)

            # Доход
            income_item = QTableWidgetItem(f"{stats['income']:,.2f}")
            income_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            income_item.setForeground(QColor(self.income_color))
            self.yearly_table.setItem(row, 1, income_item)

            # Расход
            expense_item = QTableWidgetItem(f"{stats['expense']:,.2f}")
            expense_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            expense_item.setForeground(QColor(self.expense_color))
            self.yearly_table.setItem(row, 2, expense_item)

            # Налог
            tax_item = QTableWidgetItem(f"{stats['tax']:,.2f}")
            tax_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tax_item.setForeground(QColor(self.tax_color))
            self.yearly_table.setItem(row, 3, tax_item)

            # Прибыль
            profit = float(stats["profit"])
            profit_item = QTableWidgetItem(f"{profit:,.2f}")
            profit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            if profit >= 0:
                profit_item.setForeground(QColor(self.profit_positive_color))
                profit_item.setBackground(QColor("#e8f5e9"))
            else:
                profit_item.setForeground(QColor(self.profit_negative_color))
                profit_item.setBackground(QColor("#ffebee"))
            
            self.yearly_table.setItem(row, 4, profit_item)

            # Количество транзакций
            count_item = QTableWidgetItem(str(stats["count"]))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.yearly_table.setItem(row, 5, count_item)

        self.table_ui.apply_row_heights(self.yearly_table)
    
    def load_counterparties_statistics(self) -> None:
        """Загрузить статистику топа и метрики портфеля контрагентов."""
        counterparties = list(self.statistics.top_counterparties or [])
        self.counterparties_table.setSortingEnabled(False)
        if not counterparties:
            self.portfolio_active_counterparties_label.setText("-")
            self.portfolio_avg_margin_label.setText("-")
            self.portfolio_best_counterparty_label.setText("-")
            self.portfolio_median_profit_label.setText("-")
            self.concentration_chart.set_data([])
            self.counterparties_table.setRowCount(1)
            item = QTableWidgetItem("Нет данных")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.counterparties_table.setItem(0, 0, item)
            self.counterparties_table.setSpan(0, 0, 1, 7)
            self.counterparties_table.setSortingEnabled(True)
            return

        rows = []
        total_income = 0.0
        total_profit = 0.0
        for cp in counterparties:
            income_value = float(cp.total_income)
            expense_value = float(cp.total_expense)
            tax_value = float(cp.total_tax)
            profit_value = float(cp.total_profit)
            margin = (profit_value / income_value * 100.0) if income_value > 0 else None
            rows.append(
                {
                    "cp": cp,
                    "income": income_value,
                    "expense": expense_value,
                    "tax": tax_value,
                    "profit": profit_value,
                    "margin": margin,
                }
            )
            total_income += income_value
            total_profit += profit_value

        # Ранжирование как в старой вкладке "Топ контрагентов": сохраняем исходный порядок.
        profits = sorted(row["profit"] for row in rows)
        mid_index = len(profits) // 2
        if len(profits) % 2 == 0:
            median_profit = (profits[mid_index - 1] + profits[mid_index]) / 2
        else:
            median_profit = profits[mid_index]
        avg_margin = (total_profit / total_income * 100.0) if total_income > 0 else 0.0

        best_row = max(rows, key=lambda row: row["profit"])
        best_name = best_row["cp"].counterparty_name
        best_profit = best_row["profit"]

        self.portfolio_active_counterparties_label.setText(str(len(rows)))
        self.portfolio_avg_margin_label.setText(f"{avg_margin:.2f}%")
        self.portfolio_best_counterparty_label.setText(f"{best_name} ({best_profit:,.2f})")
        self.portfolio_median_profit_label.setText(f"{median_profit:,.2f}")

        self.concentration_chart.set_data(
            [
                {
                    "name": row["cp"].counterparty_name,
                    "profit": row["profit"],
                }
                for row in rows
            ]
        )

        self.counterparties_table.clearSpans()
        self.counterparties_table.setRowCount(len(rows))

        for row, row_data in enumerate(rows):
            counterparty = row_data["cp"]
            income_value = row_data["income"]
            expense_value = row_data["expense"]
            tax_value = row_data["tax"]
            profit = row_data["profit"]
            margin = row_data["margin"]

            # Контрагент
            name_item = QTableWidgetItem(counterparty.counterparty_name)
            self.counterparties_table.setItem(row, 0, name_item)

            # Доход
            income_item = SortableNumericItem(f"{income_value:,.2f}", income_value)
            income_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            income_item.setForeground(QColor(self.income_color))
            self.counterparties_table.setItem(row, 1, income_item)

            # Расход
            expense_item = SortableNumericItem(f"{expense_value:,.2f}", expense_value)
            expense_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            expense_item.setForeground(QColor(self.expense_color))
            self.counterparties_table.setItem(row, 2, expense_item)

            # Налог
            tax_item = SortableNumericItem(f"{tax_value:,.2f}", tax_value)
            tax_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tax_item.setForeground(QColor(self.tax_color))
            self.counterparties_table.setItem(row, 3, tax_item)

            # Прибыль
            profit_item = SortableNumericItem(f"{profit:,.2f}", profit)
            profit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if profit >= 0:
                profit_item.setForeground(QColor(self.profit_positive_color))
            else:
                profit_item.setForeground(QColor(self.profit_negative_color))
            self.counterparties_table.setItem(row, 4, profit_item)

            # Маржа
            margin_text = f"{margin:.2f}%" if margin is not None else "-"
            margin_item = SortableNumericItem(margin_text, margin if margin is not None else 0.0)
            margin_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            margin_item.setForeground(
                QColor(self.profit_positive_color)
                if (margin is not None and margin >= 0)
                else QColor(self.profit_negative_color)
            )
            self.counterparties_table.setItem(row, 5, margin_item)

            # Количество транзакций
            count_item = SortableNumericItem(
                str(counterparty.transaction_count),
                float(counterparty.transaction_count),
            )
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.counterparties_table.setItem(row, 6, count_item)

        self.table_ui.apply_row_heights(self.counterparties_table)
        self.counterparties_table.setSortingEnabled(True)

    def load_concentration_statistics(self) -> None:
        """Загрузить дашборд портфеля контрагентов."""
        counterparties = list(self.statistics.top_counterparties or [])
        if not counterparties:
            self.portfolio_active_counterparties_label.setText("-")
            self.portfolio_avg_margin_label.setText("-")
            self.portfolio_best_counterparty_label.setText("-")
            self.portfolio_median_profit_label.setText("-")
            self.concentration_chart.set_data([])
            self.concentration_table.setRowCount(1)
            item = QTableWidgetItem("Нет данных")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.concentration_table.setItem(0, 0, item)
            self.concentration_table.setSpan(0, 0, 1, 7)
            self.table_ui.apply_row_heights(self.concentration_table)
            return

        rows = []
        total_income = 0.0
        total_profit = 0.0
        for cp in counterparties:
            income_value = float(cp.total_income)
            expense_value = float(cp.total_expense)
            tax_value = float(cp.total_tax)
            profit_value = float(cp.total_profit)
            margin = (profit_value / income_value * 100.0) if income_value > 0 else None
            rows.append(
                {
                    "cp": cp,
                    "income": income_value,
                    "expense": expense_value,
                    "tax": tax_value,
                    "profit": profit_value,
                    "margin": margin,
                }
            )
            total_income += income_value
            total_profit += profit_value

        rows.sort(key=lambda row: row["profit"], reverse=True)
        profits = sorted(row["profit"] for row in rows)
        mid_index = len(profits) // 2
        if len(profits) % 2 == 0:
            median_profit = (profits[mid_index - 1] + profits[mid_index]) / 2
        else:
            median_profit = profits[mid_index]
        avg_margin = (total_profit / total_income * 100.0) if total_income > 0 else 0.0

        best_row = rows[0]
        best_name = best_row["cp"].counterparty_name
        best_profit = best_row["profit"]

        self.portfolio_active_counterparties_label.setText(str(len(rows)))
        self.portfolio_avg_margin_label.setText(f"{avg_margin:.2f}%")
        self.portfolio_best_counterparty_label.setText(f"{best_name} ({best_profit:,.2f})")
        self.portfolio_median_profit_label.setText(f"{median_profit:,.2f}")

        self.concentration_chart.set_data(
            [
                {
                    "name": row["cp"].counterparty_name,
                    "profit": row["profit"],
                }
                for row in rows
            ]
        )

        self.concentration_table.clearSpans()
        self.concentration_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            cp = row["cp"]
            income_value = row["income"]
            expense_value = row["expense"]
            tax_value = row["tax"]
            profit_value = row["profit"]
            margin = row["margin"]

            self.concentration_table.setItem(row_index, 0, QTableWidgetItem(cp.counterparty_name))

            income_item = QTableWidgetItem(f"{income_value:,.2f}")
            income_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            income_item.setForeground(QColor(self.income_color))
            self.concentration_table.setItem(row_index, 1, income_item)

            expense_item = QTableWidgetItem(f"{expense_value:,.2f}")
            expense_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            expense_item.setForeground(QColor(self.expense_color))
            self.concentration_table.setItem(row_index, 2, expense_item)

            tax_item = QTableWidgetItem(f"{tax_value:,.2f}")
            tax_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tax_item.setForeground(QColor(self.tax_color))
            self.concentration_table.setItem(row_index, 3, tax_item)

            profit_item = QTableWidgetItem(f"{profit_value:,.2f}")
            profit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            profit_item.setForeground(
                QColor(self.profit_positive_color)
                if profit_value >= 0
                else QColor(self.profit_negative_color)
            )
            self.concentration_table.setItem(row_index, 4, profit_item)

            margin_text = f"{margin:.2f}%" if margin is not None else "-"
            margin_item = QTableWidgetItem(margin_text)
            margin_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            margin_item.setForeground(
                QColor(self.profit_positive_color)
                if (margin is not None and margin >= 0)
                else QColor(self.profit_negative_color)
            )
            self.concentration_table.setItem(row_index, 5, margin_item)

            count_item = QTableWidgetItem(str(cp.transaction_count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.concentration_table.setItem(row_index, 6, count_item)
        self.table_ui.apply_row_heights(self.concentration_table)

    def load_tax_statistics(self) -> None:
        """Загрузить налоговую аналитику по месяцам."""
        monthly_stats = sorted(
            self.statistics.monthly_statistics,
            key=lambda item: (item.year, item.month)
        )

        total_income = float(self.statistics.total_income or 0)
        total_tax = float(self.statistics.total_tax or 0)
        total_profit = float(self.statistics.total_profit or 0)

        effective_rate = (total_tax / total_income * 100.0) if total_income > 0 else 0.0
        burden_rate = (total_tax / total_profit * 100.0) if total_profit > 0 else 0.0

        recent_months = monthly_stats[-3:] if monthly_stats else []
        run_rate = (
            sum(float(item.tax) for item in recent_months) / len(recent_months)
            if recent_months
            else 0.0
        )
        forecast_next = run_rate

        if burden_rate < 10:
            risk_text = "Низкий"
            risk_color = self.profit_positive_color
        elif burden_rate < 20:
            risk_text = "Средний"
            risk_color = "#ef6c00"
        else:
            risk_text = "Высокий"
            risk_color = self.profit_negative_color

        self.tax_effective_rate_label.setText(f"{effective_rate:.2f}%")
        self.tax_burden_label.setText(f"{burden_rate:.2f}%")
        self.tax_run_rate_label.setText(f"{run_rate:,.2f} руб.")
        self.tax_forecast_label.setText(f"{forecast_next:,.2f} руб.")
        self.tax_risk_label.setText(risk_text)
        self.tax_risk_label.setStyleSheet(f"color: {risk_color}; font-weight: bold;")

        chart_rows = []
        for item in monthly_stats:
            income = float(item.income)
            tax = float(item.tax)
            row_rate = (tax / income * 100.0) if income > 0 else 0.0
            chart_rows.append(
                {
                    "label": f"{item.month:02d}.{str(item.year)[-2:]}",
                    "effective_tax_rate": row_rate,
                }
            )
        self.tax_chart.set_data(chart_rows)

        if not monthly_stats:
            self.tax_table.setRowCount(1)
            item = QTableWidgetItem("Нет данных")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tax_table.setItem(0, 0, item)
            self.tax_table.setSpan(0, 0, 1, 6)
            self.table_ui.apply_row_heights(self.tax_table)
            return

        self.tax_table.clearSpans()
        self.tax_table.setRowCount(len(monthly_stats))
        for row_idx, month_item in enumerate(monthly_stats):
            month_label = f"{month_item.month:02d}.{month_item.year}"
            income = float(month_item.income)
            tax = float(month_item.tax)
            profit = float(month_item.profit)
            month_effective_rate = (tax / income * 100.0) if income > 0 else 0.0
            month_burden_rate = (tax / profit * 100.0) if profit > 0 else 0.0

            month_cell = QTableWidgetItem(month_label)
            month_cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tax_table.setItem(row_idx, 0, month_cell)

            income_cell = QTableWidgetItem(f"{income:,.2f}")
            income_cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            income_cell.setForeground(QColor(self.income_color))
            self.tax_table.setItem(row_idx, 1, income_cell)

            tax_cell = QTableWidgetItem(f"{tax:,.2f}")
            tax_cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tax_cell.setForeground(QColor(self.tax_color))
            self.tax_table.setItem(row_idx, 2, tax_cell)

            profit_cell = QTableWidgetItem(f"{profit:,.2f}")
            profit_cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            profit_cell.setForeground(
                QColor(self.profit_positive_color)
                if profit >= 0
                else QColor(self.profit_negative_color)
            )
            self.tax_table.setItem(row_idx, 3, profit_cell)

            effective_cell = QTableWidgetItem(f"{month_effective_rate:.2f}%")
            effective_cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tax_table.setItem(row_idx, 4, effective_cell)

            burden_cell = QTableWidgetItem(f"{month_burden_rate:.2f}%")
            burden_cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tax_table.setItem(row_idx, 5, burden_cell)
        self.table_ui.apply_row_heights(self.tax_table)

    def on_trend_mode_changed(self, *_args) -> None:
        """Переключить режим отображения трендов."""
        mode = self.trend_mode_combo.currentData()
        self.trend_chart.set_mode(mode)

    def load_trends_statistics(self) -> None:
        """Загрузить дашборд трендов по месяцам."""
        monthly_stats = sorted(
            self.statistics.monthly_statistics,
            key=lambda item: (item.year, item.month)
        )
        rows = []
        for monthly in monthly_stats:
            label = f"{monthly.month:02d}.{str(monthly.year)[-2:]}"
            rows.append(
                {
                    "label": label,
                    "income": float(monthly.income),
                    "expense": float(monthly.expense),
                    "tax": float(monthly.tax),
                    "profit": float(monthly.profit),
                }
            )

        self.trend_chart.set_data(rows)
        self.trend_chart.set_mode(self.trend_mode_combo.currentData())

        if not rows:
            self.monthly_details_table.setRowCount(1)
            item = QTableWidgetItem("Нет данных")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.monthly_details_table.setItem(0, 0, item)
            self.monthly_details_table.setSpan(0, 0, 1, 5)
            self.table_ui.apply_row_heights(self.monthly_details_table)
            return

        self.monthly_details_table.clearSpans()
        self.monthly_details_table.setRowCount(len(rows))
        for row_index, row_data in enumerate(rows):
            month_item = QTableWidgetItem(row_data["label"])
            month_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.monthly_details_table.setItem(row_index, 0, month_item)

            income_item = QTableWidgetItem(f"{row_data['income']:,.2f}")
            income_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            income_item.setForeground(QColor(self.income_color))
            self.monthly_details_table.setItem(row_index, 1, income_item)

            expense_item = QTableWidgetItem(f"{row_data['expense']:,.2f}")
            expense_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            expense_item.setForeground(QColor(self.expense_color))
            self.monthly_details_table.setItem(row_index, 2, expense_item)

            tax_item = QTableWidgetItem(f"{row_data['tax']:,.2f}")
            tax_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tax_item.setForeground(QColor(self.tax_color))
            self.monthly_details_table.setItem(row_index, 3, tax_item)

            profit_item = QTableWidgetItem(f"{row_data['profit']:,.2f}")
            profit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if row_data["profit"] >= 0:
                profit_item.setForeground(QColor(self.profit_positive_color))
            else:
                profit_item.setForeground(QColor(self.profit_negative_color))
            self.monthly_details_table.setItem(row_index, 4, profit_item)
        self.table_ui.apply_row_heights(self.monthly_details_table)

    def load_period_comparison(self) -> None:
        """Загрузить сравнение текущего периода с предыдущим."""
        comparison = self.statistics.period_comparison
        if not comparison:
            self.comparison_period_label.setText("Сравнение доступно после выбора диапазона дат в фильтрах.")
            self.comparison_income_label.setText("-")
            self.comparison_expense_label.setText("-")
            self.comparison_tax_label.setText("-")
            self.comparison_profit_label.setText("-")
            self.comparison_transactions_label.setText("-")
            return

        current_start = comparison.current_start.strftime("%d.%m.%Y")
        current_end = comparison.current_end.strftime("%d.%m.%Y")
        previous_start = comparison.previous_start.strftime("%d.%m.%Y")
        previous_end = comparison.previous_end.strftime("%d.%m.%Y")
        self.comparison_period_label.setText(
            f"Текущий: {current_start} - {current_end}; предыдущий: {previous_start} - {previous_end}"
        )

        self._apply_delta_label(
            self.comparison_income_label,
            float(comparison.income_delta),
            self._format_delta_money(comparison.income_delta, comparison.income_delta_percent),
        )
        self._apply_delta_label(
            self.comparison_expense_label,
            float(comparison.expense_delta),
            self._format_delta_money(comparison.expense_delta, comparison.expense_delta_percent),
        )
        self._apply_delta_label(
            self.comparison_tax_label,
            float(comparison.tax_delta),
            self._format_delta_money(comparison.tax_delta, comparison.tax_delta_percent),
        )
        self._apply_delta_label(
            self.comparison_profit_label,
            float(comparison.profit_delta),
            self._format_delta_money(comparison.profit_delta, comparison.profit_delta_percent),
        )
        self._apply_delta_label(
            self.comparison_transactions_label,
            float(comparison.transactions_delta),
            self._format_delta_count(comparison.transactions_delta, comparison.transactions_delta_percent),
        )

    def _format_delta_money(self, delta, delta_percent: Optional[float]) -> str:
        sign = "+" if float(delta) > 0 else ""
        text = f"{sign}{float(delta):,.2f} руб."
        if delta_percent is not None:
            text += f" ({delta_percent:+.1f}%)"
        return text

    def _format_delta_count(self, delta: int, delta_percent: Optional[float]) -> str:
        sign = "+" if delta > 0 else ""
        text = f"{sign}{delta}"
        if delta_percent is not None:
            text += f" ({delta_percent:+.1f}%)"
        return text

    def _apply_delta_label(self, label: QLabel, value: float, text: str) -> None:
        label.setText(text)
        if value > 0:
            label.setStyleSheet(f"color: {self.profit_positive_color};")
        elif value < 0:
            label.setStyleSheet(f"color: {self.profit_negative_color};")
        else:
            label.setStyleSheet(f"color: {self.neutral_color};")
