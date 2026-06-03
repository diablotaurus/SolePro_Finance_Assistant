"""
DTO для статистических данных.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class MonthlyStatisticsDTO(BaseModel):
    """DTO для статистики за месяц."""
    year: int = Field(..., description="Год")
    month: int = Field(..., ge=1, le=12, description="Месяц")
    income: Decimal = Field(Decimal("0"), description="Доход за месяц")
    expense: Decimal = Field(Decimal("0"), description="Расход за месяц")
    tax: Decimal = Field(Decimal("0"), description="Налог за месяц")
    profit: Decimal = Field(Decimal("0"), description="Прибыль за месяц")
    transaction_count: int = Field(0, description="Количество транзакций за месяц")


class CounterpartyStatisticsDTO(BaseModel):
    """DTO для статистики по контрагенту."""
    counterparty_id: str = Field(..., description="ID контрагента")
    counterparty_name: str = Field(..., description="Имя контрагента")
    transaction_count: int = Field(0, description="Количество транзакций")
    total_income: Decimal = Field(Decimal("0"), description="Общий доход")
    total_expense: Decimal = Field(Decimal("0"), description="Общий расход")
    total_tax: Decimal = Field(Decimal("0"), description="Общий налог")
    total_profit: Decimal = Field(Decimal("0"), description="Общая прибыль")
    percentage_of_total: float = Field(0.0, description="Процент от общего объема")


class PeriodComparisonDTO(BaseModel):
    """DTO для сравнения текущего периода с предыдущим периодом той же длительности."""
    current_start: datetime = Field(..., description="Начало текущего периода")
    current_end: datetime = Field(..., description="Конец текущего периода")
    previous_start: datetime = Field(..., description="Начало предыдущего периода")
    previous_end: datetime = Field(..., description="Конец предыдущего периода")

    current_transactions: int = Field(0, description="Количество транзакций в текущем периоде")
    previous_transactions: int = Field(0, description="Количество транзакций в предыдущем периоде")

    current_income: Decimal = Field(Decimal("0"), description="Доход текущего периода")
    previous_income: Decimal = Field(Decimal("0"), description="Доход предыдущего периода")
    income_delta: Decimal = Field(Decimal("0"), description="Изменение дохода")
    income_delta_percent: Optional[float] = Field(None, description="Изменение дохода в процентах")

    current_expense: Decimal = Field(Decimal("0"), description="Расход текущего периода")
    previous_expense: Decimal = Field(Decimal("0"), description="Расход предыдущего периода")
    expense_delta: Decimal = Field(Decimal("0"), description="Изменение расхода")
    expense_delta_percent: Optional[float] = Field(None, description="Изменение расхода в процентах")

    current_tax: Decimal = Field(Decimal("0"), description="Налог текущего периода")
    previous_tax: Decimal = Field(Decimal("0"), description="Налог предыдущего периода")
    tax_delta: Decimal = Field(Decimal("0"), description="Изменение налога")
    tax_delta_percent: Optional[float] = Field(None, description="Изменение налога в процентах")

    current_profit: Decimal = Field(Decimal("0"), description="Прибыль текущего периода")
    previous_profit: Decimal = Field(Decimal("0"), description="Прибыль предыдущего периода")
    profit_delta: Decimal = Field(Decimal("0"), description="Изменение прибыли")
    profit_delta_percent: Optional[float] = Field(None, description="Изменение прибыли в процентах")

    transactions_delta: int = Field(0, description="Изменение количества транзакций")
    transactions_delta_percent: Optional[float] = Field(None, description="Изменение количества транзакций в процентах")


class StatisticsDTO(BaseModel):
    """Основной DTO для статистики."""
    # Общая статистика
    total_transactions: int = Field(0, description="Общее количество транзакций")
    total_income: Decimal = Field(Decimal("0"), description="Общий доход")
    total_expense: Decimal = Field(Decimal("0"), description="Общий расход")
    total_tax: Decimal = Field(Decimal("0"), description="Общий налог")
    total_profit: Decimal = Field(Decimal("0"), description="Общая прибыль")

    # Средние значения
    avg_income: Optional[Decimal] = Field(None, description="Средний доход")
    avg_expense: Optional[Decimal] = Field(None, description="Средний расход")
    avg_tax: Optional[Decimal] = Field(None, description="Средний налог")
    avg_profit: Optional[Decimal] = Field(None, description="Средняя прибыль")

    # Даты
    first_transaction_date: Optional[datetime] = Field(None, description="Дата первой транзакции")
    last_transaction_date: Optional[datetime] = Field(None, description="Дата последней транзакции")

    # Статистика по месяцам
    monthly_statistics: List[MonthlyStatisticsDTO] = Field(default_factory=list, description="Статистика по месяцам")

    # Сравнение текущего периода с предыдущим
    period_comparison: Optional[PeriodComparisonDTO] = Field(None, description="Сравнение текущего периода с предыдущим")

    # Топ контрагентов
    top_counterparties: List[CounterpartyStatisticsDTO] = Field(default_factory=list, description="Топ контрагентов")

    # Дополнительная информация
    income_transaction_count: int = Field(0, description="Количество транзакций дохода")
    expense_transaction_count: int = Field(0, description="Количество транзакций расхода")
    mixed_transaction_count: int = Field(0, description="Количество смешанных транзакций")
