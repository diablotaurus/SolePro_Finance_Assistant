"""
View-model для диалога статистики.

Содержит вычисления, ранее жившие внутри StatisticsDialog (годовая агрегация,
метрики портфеля контрагентов, налоговые KPI и т.д.). Не зависит от Qt и
полностью тестируется как обычный Python-код. View (диалог) только отображает
готовые структуры.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .....core.application.dto.statistics_dto import StatisticsDTO


@dataclass(frozen=True)
class YearlyRow:
    """Агрегированная статистика за год."""
    year: int
    income: float
    expense: float
    tax: float
    profit: float
    count: int
    margin: Optional[float] = None
    income_growth: Optional[float] = None
    profit_growth: Optional[float] = None


@dataclass(frozen=True)
class YearlyTotals:
    """Итоги по всем годам."""
    income: float
    expense: float
    tax: float
    profit: float
    margin: Optional[float]
    count: int


@dataclass(frozen=True)
class CounterpartyRow:
    """Строка статистики по контрагенту."""
    name: str
    income: float
    expense: float
    tax: float
    profit: float
    margin: Optional[float]
    transaction_count: int
    percentage_of_total: float = 0.0


@dataclass(frozen=True)
class PortfolioMetrics:
    """Сводные метрики портфеля контрагентов."""
    active_count: int
    avg_margin: float
    best_name: Optional[str]
    best_profit: Optional[float]
    median_profit: Optional[float]


@dataclass(frozen=True)
class MonthlyRow:
    """Строка помесячного тренда."""
    label: str  # "MM.YY"
    income: float
    expense: float
    tax: float
    profit: float


@dataclass(frozen=True)
class TaxMonthlyRow:
    """Помесячная налоговая строка."""
    label: str        # "MM.YYYY"
    short_label: str  # "MM.YY"
    income: float
    tax: float
    profit: float
    effective_rate: float
    burden_rate: float


@dataclass(frozen=True)
class TaxKpis:
    """Сводные налоговые KPI."""
    effective_rate: float
    burden_rate: float
    run_rate: float
    forecast_next: float
    risk_level: str  # "low" / "medium" / "high"


class StatisticsViewModel:
    """Готовит данные статистики к отображению (без Qt)."""

    LOW_RISK_THRESHOLD = 10.0
    MEDIUM_RISK_THRESHOLD = 20.0
    RECENT_MONTHS_FOR_RUN_RATE = 3

    def __init__(self, statistics: StatisticsDTO):
        self._statistics = statistics

    def _sorted_monthly(self) -> list:
        return sorted(
            self._statistics.monthly_statistics,
            key=lambda item: (item.year, item.month),
        )

    @staticmethod
    def _growth(previous_value: float, current_value: float) -> Optional[float]:
        """Прирост в процентах относительно предыдущего значения."""
        if previous_value == 0:
            return None
        return (current_value - previous_value) / previous_value * 100.0

    def yearly_rows(self) -> List[YearlyRow]:
        """Свернуть помесячную статистику в годовую (с маржой и приростом)."""
        yearly: dict[int, dict[str, float]] = {}
        for monthly in self._statistics.monthly_statistics:
            stats = yearly.setdefault(
                monthly.year,
                {"income": 0.0, "expense": 0.0, "tax": 0.0, "profit": 0.0, "count": 0},
            )
            stats["income"] += float(monthly.income)
            stats["expense"] += float(monthly.expense)
            stats["tax"] += float(monthly.tax)
            stats["profit"] += float(monthly.profit)
            stats["count"] += int(monthly.transaction_count)

        rows: List[YearlyRow] = []
        previous: Optional[dict[str, float]] = None
        for year, stats in sorted(yearly.items()):
            income = stats["income"]
            profit = stats["profit"]
            margin = (profit / income * 100.0) if income > 0 else None
            income_growth = self._growth(previous["income"], income) if previous else None
            profit_growth = self._growth(previous["profit"], profit) if previous else None
            rows.append(
                YearlyRow(
                    year=year,
                    income=income,
                    expense=stats["expense"],
                    tax=stats["tax"],
                    profit=profit,
                    count=int(stats["count"]),
                    margin=margin,
                    income_growth=income_growth,
                    profit_growth=profit_growth,
                )
            )
            previous = stats
        return rows

    def yearly_totals(self) -> Optional[YearlyTotals]:
        """Итоги по всем годам (или None, если данных нет)."""
        rows = self.yearly_rows()
        if not rows:
            return None
        income = sum(row.income for row in rows)
        expense = sum(row.expense for row in rows)
        tax = sum(row.tax for row in rows)
        profit = sum(row.profit for row in rows)
        count = sum(row.count for row in rows)
        margin = (profit / income * 100.0) if income > 0 else None
        return YearlyTotals(
            income=income,
            expense=expense,
            tax=tax,
            profit=profit,
            margin=margin,
            count=count,
        )

    def overall_margin(self) -> Optional[float]:
        """Общая рентабельность (прибыль / доход, %)."""
        total_income = float(self._statistics.total_income or 0)
        total_profit = float(self._statistics.total_profit or 0)
        return (total_profit / total_income * 100.0) if total_income > 0 else None

    def counterparty_rows(self) -> List[CounterpartyRow]:
        """Строки по контрагентам в исходном порядке (как в top_counterparties)."""
        rows: List[CounterpartyRow] = []
        for cp in (self._statistics.top_counterparties or []):
            income = float(cp.total_income)
            expense = float(cp.total_expense)
            tax = float(cp.total_tax)
            profit = float(cp.total_profit)
            margin = (profit / income * 100.0) if income > 0 else None
            rows.append(
                CounterpartyRow(
                    name=cp.counterparty_name,
                    income=income,
                    expense=expense,
                    tax=tax,
                    profit=profit,
                    margin=margin,
                    transaction_count=int(cp.transaction_count),
                    percentage_of_total=float(cp.percentage_of_total),
                )
            )
        return rows

    def portfolio_metrics(
        self, rows: Optional[List[CounterpartyRow]] = None
    ) -> PortfolioMetrics:
        """Сводные метрики портфеля по строкам контрагентов."""
        if rows is None:
            rows = self.counterparty_rows()
        if not rows:
            return PortfolioMetrics(
                active_count=0,
                avg_margin=0.0,
                best_name=None,
                best_profit=None,
                median_profit=None,
            )

        total_income = sum(row.income for row in rows)
        total_profit = sum(row.profit for row in rows)

        profits = sorted(row.profit for row in rows)
        mid_index = len(profits) // 2
        if len(profits) % 2 == 0:
            median_profit = (profits[mid_index - 1] + profits[mid_index]) / 2
        else:
            median_profit = profits[mid_index]

        avg_margin = (total_profit / total_income * 100.0) if total_income > 0 else 0.0
        best_row = max(rows, key=lambda row: row.profit)

        return PortfolioMetrics(
            active_count=len(rows),
            avg_margin=avg_margin,
            best_name=best_row.name,
            best_profit=best_row.profit,
            median_profit=median_profit,
        )

    def monthly_rows(self) -> List[MonthlyRow]:
        """Помесячные строки тренда (отсортированы по дате)."""
        rows: List[MonthlyRow] = []
        for monthly in self._sorted_monthly():
            rows.append(
                MonthlyRow(
                    label=f"{monthly.month:02d}.{str(monthly.year)[-2:]}",
                    income=float(monthly.income),
                    expense=float(monthly.expense),
                    tax=float(monthly.tax),
                    profit=float(monthly.profit),
                )
            )
        return rows

    def tax_kpis(self) -> TaxKpis:
        """Сводные налоговые KPI с классификацией уровня нагрузки."""
        total_income = float(self._statistics.total_income or 0)
        total_tax = float(self._statistics.total_tax or 0)
        total_profit = float(self._statistics.total_profit or 0)

        effective_rate = (total_tax / total_income * 100.0) if total_income > 0 else 0.0
        burden_rate = (total_tax / total_profit * 100.0) if total_profit > 0 else 0.0

        recent_months = self._sorted_monthly()[-self.RECENT_MONTHS_FOR_RUN_RATE:]
        run_rate = (
            sum(float(item.tax) for item in recent_months) / len(recent_months)
            if recent_months
            else 0.0
        )
        forecast_next = run_rate

        if burden_rate < self.LOW_RISK_THRESHOLD:
            risk_level = "low"
        elif burden_rate < self.MEDIUM_RISK_THRESHOLD:
            risk_level = "medium"
        else:
            risk_level = "high"

        return TaxKpis(
            effective_rate=effective_rate,
            burden_rate=burden_rate,
            run_rate=run_rate,
            forecast_next=forecast_next,
            risk_level=risk_level,
        )

    def tax_monthly_rows(self) -> List[TaxMonthlyRow]:
        """Помесячные налоговые строки (отсортированы по дате)."""
        rows: List[TaxMonthlyRow] = []
        for monthly in self._sorted_monthly():
            income = float(monthly.income)
            tax = float(monthly.tax)
            profit = float(monthly.profit)
            effective_rate = (tax / income * 100.0) if income > 0 else 0.0
            burden_rate = (tax / profit * 100.0) if profit > 0 else 0.0
            rows.append(
                TaxMonthlyRow(
                    label=f"{monthly.month:02d}.{monthly.year}",
                    short_label=f"{monthly.month:02d}.{str(monthly.year)[-2:]}",
                    income=income,
                    tax=tax,
                    profit=profit,
                    effective_rate=effective_rate,
                    burden_rate=burden_rate,
                )
            )
        return rows
