"""
Тесты StatisticsViewModel (расчёты статистики, без Qt).
"""
from decimal import Decimal

from solepro.core.application.dto.statistics_dto import (
    StatisticsDTO,
    MonthlyStatisticsDTO,
    CounterpartyStatisticsDTO,
)
from solepro.presentation.desktop.views.dialogs.statistics_view_model import (
    StatisticsViewModel,
)


def _monthly(year, month, income, expense, tax, profit, count):
    return MonthlyStatisticsDTO(
        year=year,
        month=month,
        income=Decimal(str(income)),
        expense=Decimal(str(expense)),
        tax=Decimal(str(tax)),
        profit=Decimal(str(profit)),
        transaction_count=count,
    )


def _cp(name, income, expense, tax, profit, count, cid="id"):
    return CounterpartyStatisticsDTO(
        counterparty_id=cid,
        counterparty_name=name,
        transaction_count=count,
        total_income=Decimal(str(income)),
        total_expense=Decimal(str(expense)),
        total_tax=Decimal(str(tax)),
        total_profit=Decimal(str(profit)),
        percentage_of_total=0.0,
    )


def test_yearly_rows_aggregates_and_sorts():
    stats = StatisticsDTO(monthly_statistics=[
        _monthly(2025, 1, 200, 20, 10, 170, 3),
        _monthly(2024, 2, 50, 0, 0, 50, 1),
        _monthly(2024, 1, 100, 10, 5, 85, 2),
    ])
    rows = StatisticsViewModel(stats).yearly_rows()

    assert [r.year for r in rows] == [2024, 2025]
    y2024 = rows[0]
    assert y2024.income == 150.0
    assert y2024.expense == 10.0
    assert y2024.tax == 5.0
    assert y2024.profit == 135.0
    assert y2024.count == 3
    assert rows[1].income == 200.0


def test_yearly_rows_empty():
    assert StatisticsViewModel(StatisticsDTO()).yearly_rows() == []


def test_counterparty_rows_and_margin():
    stats = StatisticsDTO(top_counterparties=[
        _cp("A", 100, 10, 5, 85, 2),
        _cp("B", 0, 50, 0, -50, 1),
    ])
    rows = StatisticsViewModel(stats).counterparty_rows()

    assert rows[0].name == "A"
    assert rows[0].margin == 85.0
    assert rows[1].margin is None  # income == 0 -> margin не считается


def test_portfolio_metrics_odd_median():
    stats = StatisticsDTO(top_counterparties=[
        _cp("A", 100, 0, 0, 85, 1),
        _cp("B", 0, 0, 0, -50, 1),
        _cp("C", 200, 0, 0, 100, 1),
    ])
    metrics = StatisticsViewModel(stats).portfolio_metrics()

    assert metrics.active_count == 3
    assert metrics.median_profit == 85.0
    assert metrics.best_name == "C"
    assert metrics.best_profit == 100.0
    assert round(metrics.avg_margin, 4) == 45.0  # 135 / 300 * 100


def test_portfolio_metrics_even_median():
    stats = StatisticsDTO(top_counterparties=[
        _cp("A", 100, 0, 0, 10, 1),
        _cp("B", 100, 0, 0, 30, 1),
    ])
    metrics = StatisticsViewModel(stats).portfolio_metrics()
    assert metrics.median_profit == 20.0


def test_portfolio_metrics_empty():
    metrics = StatisticsViewModel(StatisticsDTO()).portfolio_metrics()
    assert metrics.active_count == 0
    assert metrics.best_name is None
    assert metrics.best_profit is None
    assert metrics.median_profit is None
    assert metrics.avg_margin == 0.0


def test_monthly_rows_labels_and_order():
    stats = StatisticsDTO(monthly_statistics=[
        _monthly(2025, 3, 10, 0, 0, 10, 1),
        _monthly(2024, 12, 20, 0, 0, 20, 1),
    ])
    rows = StatisticsViewModel(stats).monthly_rows()
    assert [r.label for r in rows] == ["12.24", "03.25"]


def test_tax_kpis_rates_risk_and_run_rate():
    stats = StatisticsDTO(
        total_income=Decimal("300"),
        total_tax=Decimal("15"),
        total_profit=Decimal("100"),
        monthly_statistics=[
            _monthly(2024, 1, 0, 0, 5, 0, 1),
            _monthly(2024, 2, 0, 0, 0, 0, 1),
            _monthly(2025, 1, 0, 0, 10, 0, 1),
        ],
    )
    kpis = StatisticsViewModel(stats).tax_kpis()

    assert round(kpis.effective_rate, 4) == 5.0   # 15 / 300 * 100
    assert round(kpis.burden_rate, 4) == 15.0     # 15 / 100 * 100
    assert kpis.risk_level == "medium"
    assert round(kpis.run_rate, 4) == 5.0         # (5 + 0 + 10) / 3
    assert kpis.forecast_next == kpis.run_rate


def test_tax_risk_levels():
    def risk(tax, profit):
        stats = StatisticsDTO(
            total_tax=Decimal(str(tax)),
            total_profit=Decimal(str(profit)),
        )
        return StatisticsViewModel(stats).tax_kpis().risk_level

    assert risk(5, 100) == "low"      # 5%
    assert risk(15, 100) == "medium"  # 15%
    assert risk(30, 100) == "high"    # 30%
    assert risk(10, 0) == "not_applicable"
    assert risk(10, -100) == "not_applicable"


def test_tax_monthly_rows():
    stats = StatisticsDTO(monthly_statistics=[
        _monthly(2025, 1, 100, 0, 10, 90, 1),
    ])
    rows = StatisticsViewModel(stats).tax_monthly_rows()

    assert len(rows) == 1
    row = rows[0]
    assert row.label == "01.2025"
    assert row.short_label == "01.25"
    assert round(row.effective_rate, 4) == 10.0  # 10 / 100 * 100
    assert round(row.burden_rate, 4) == round(10 / 90 * 100, 4)


def test_yearly_rows_margin_and_growth():
    stats = StatisticsDTO(monthly_statistics=[
        _monthly(2024, 1, 100, 0, 0, 80, 1),
        _monthly(2025, 1, 150, 0, 0, 120, 1),
    ])
    rows = StatisticsViewModel(stats).yearly_rows()

    # Первый год — без прироста
    assert rows[0].income_growth is None
    assert rows[0].profit_growth is None
    assert round(rows[0].margin, 4) == 80.0

    # Второй год — прирост к первому
    assert round(rows[1].income_growth, 4) == 50.0  # (150-100)/100
    assert round(rows[1].profit_growth, 4) == 50.0  # (120-80)/80
    assert round(rows[1].margin, 4) == 80.0


def test_yearly_profit_growth_is_undefined_after_loss():
    stats = StatisticsDTO(monthly_statistics=[
        _monthly(2024, 1, 100, 150, 0, -50, 1),
        _monthly(2025, 1, 150, 0, 0, 100, 1),
    ])

    rows = StatisticsViewModel(stats).yearly_rows()

    assert rows[1].profit_growth is None


def test_yearly_totals():
    stats = StatisticsDTO(monthly_statistics=[
        _monthly(2024, 1, 100, 10, 5, 85, 2),
        _monthly(2025, 1, 200, 20, 10, 170, 3),
    ])
    totals = StatisticsViewModel(stats).yearly_totals()

    assert totals.income == 300.0
    assert totals.expense == 30.0
    assert totals.tax == 15.0
    assert totals.profit == 255.0
    assert totals.count == 5
    assert round(totals.margin, 4) == 85.0  # 255 / 300 * 100


def test_yearly_totals_empty():
    assert StatisticsViewModel(StatisticsDTO()).yearly_totals() is None


def test_overall_margin():
    stats = StatisticsDTO(total_income=Decimal("200"), total_profit=Decimal("50"))
    assert round(StatisticsViewModel(stats).overall_margin(), 4) == 25.0
    # без дохода -> None
    assert StatisticsViewModel(StatisticsDTO()).overall_margin() is None


def test_counterparty_rows_percentage_of_total():
    stats = StatisticsDTO(top_counterparties=[
        CounterpartyStatisticsDTO(
            counterparty_id="a",
            counterparty_name="A",
            transaction_count=1,
            total_income=Decimal("100"),
            total_expense=Decimal("0"),
            total_tax=Decimal("0"),
            total_profit=Decimal("100"),
            percentage_of_total=42.5,
        ),
    ])
    rows = StatisticsViewModel(stats).counterparty_rows()
    assert rows[0].percentage_of_total == 42.5
