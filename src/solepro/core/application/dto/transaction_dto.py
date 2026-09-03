"""
DTO для работы с транзакциями.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from ....core.domain.constants import (
    MAX_COUNTERPARTY_NAME_LENGTH,
    MAX_MONEY_AMOUNT,
    MAX_NOTE_LENGTH,
    MONEY_QUANTUM,
)
from ....core.domain.enums.transaction_type import TransactionType
from ....core.domain.value_objects.money import Money


def _normalize_amount(value: Decimal) -> Decimal:
    """Validate and normalize a monetary amount for storage."""
    if not value.is_finite():
        raise ValueError("Сумма должна быть конечным числом")
    if value < 0:
        raise ValueError("Сумма не может быть отрицательной")
    if value > MAX_MONEY_AMOUNT:
        raise ValueError("Сумма слишком большая")
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


class TransactionBaseDTO(BaseModel):
    """Базовый DTO для транзакции."""
    date: datetime = Field(..., description="Дата транзакции")
    income: Decimal = Field(default=Decimal("0"), ge=0, description="Сумма дохода")
    expense: Decimal = Field(default=Decimal("0"), ge=0, description="Сумма расхода")
    tax: Decimal = Field(default=Decimal("0"), ge=0, description="Сумма налога")
    counterparty_id: Optional[UUID] = Field(None, description="ID контрагента")
    note: Optional[str] = Field(None, max_length=MAX_NOTE_LENGTH, description="Примечание")

    @field_validator("income", "expense", "tax")
    def validate_amounts(cls, v: Decimal) -> Decimal:
        """Валидация денежных сумм."""
        return _normalize_amount(v)

    model_config = ConfigDict(
        from_attributes=True,
    )


class TransactionCreateDTO(TransactionBaseDTO):
    """DTO для создания транзакции."""
    counterparty_name: Optional[str] = Field(
        None,
        max_length=MAX_COUNTERPARTY_NAME_LENGTH,
        description="Имя контрагента (если ID не указан)",
    )

    @field_validator("date")
    def validate_date(cls, v: datetime) -> datetime:
        """Валидация даты нового ввода.

        Проверка только при создании: response-DTO не должен валидировать
        бизнес-правила ввода, иначе перевод системных часов назад ломал бы
        отображение уже сохранённых данных.
        """
        if v > datetime.now():
            raise ValueError("Дата не может быть в будущем")
        return v


class TransactionUpdateDTO(BaseModel):
    """DTO для обновления транзакции."""
    date: Optional[datetime] = Field(None, description="Дата транзакции")
    income: Optional[Decimal] = Field(None, ge=0, description="Сумма дохода")
    expense: Optional[Decimal] = Field(None, ge=0, description="Сумма расхода")
    tax: Optional[Decimal] = Field(None, ge=0, description="Сумма налога")
    counterparty_id: Optional[UUID] = Field(None, description="ID контрагента")
    # None в counterparty_id означает «не менять», поэтому для снятия
    # контрагента нужен отдельный явный флаг.
    clear_counterparty: bool = Field(False, description="Убрать контрагента у транзакции")
    note: Optional[str] = Field(None, max_length=MAX_NOTE_LENGTH, description="Примечание")

    @field_validator("income", "expense", "tax")
    @classmethod
    def validate_amounts(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        """Применить к обновлению те же денежные правила, что и к созданию."""
        return None if value is None else _normalize_amount(value)

    model_config = ConfigDict(
        from_attributes=True,
    )


class TransactionResponseDTO(TransactionBaseDTO):
    """DTO для ответа с данными транзакции."""
    id: UUID = Field(..., description="ID транзакции")
    profit: Decimal = Field(..., description="Прибыль (доход - расход - налог)")
    counterparty_name: Optional[str] = Field(None, description="Имя контрагента")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime = Field(..., description="Время последнего обновления")
    
    @property
    def transaction_type(self) -> TransactionType:
        """Определить тип транзакции."""
        if self.income > 0 and self.expense == 0:
            return TransactionType.INCOME
        elif self.expense > 0 and self.income == 0:
            return TransactionType.EXPENSE
        elif self.income > 0 and self.expense > 0:
            return TransactionType.MIXED
        else:
            return TransactionType.NEUTRAL


class TransactionListDTO(BaseModel):
    """DTO для списка транзакций."""
    transactions: List[TransactionResponseDTO] = Field(default_factory=list, description="Список транзакций")
    total_count: int = Field(0, description="Общее количество транзакций")
    page: int = Field(1, description="Текущая страница")
    page_size: int = Field(100, description="Размер страницы")
    total_pages: int = Field(0, description="Общее количество страниц")


class TransactionFilterDTO(BaseModel):
    """DTO для фильтрации транзакций."""
    start_date: Optional[datetime] = Field(None, description="Начальная дата")
    end_date: Optional[datetime] = Field(None, description="Конечная дата")
    counterparty_id: Optional[UUID] = Field(None, description="ID контрагента")
    transaction_type: Optional[TransactionType] = Field(None, description="Тип транзакции")
    has_tax: Optional[bool] = Field(None, description="Только транзакции с налогом")
    no_tax: Optional[bool] = Field(None, description="Только транзакции без налога")
    show_all: bool = Field(False, description="Показать все записи без фильтров")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Минимальная сумма")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Максимальная сумма")
    search_query: Optional[str] = Field(None, description="Текст для поиска")
    page: int = Field(1, ge=1, description="Номер страницы")
    page_size: int = Field(100, ge=1, le=1000, description="Размер страницы")
    order_by: str = Field("date_desc", description="Поле сортировки")
    
    model_config = ConfigDict(
    )
