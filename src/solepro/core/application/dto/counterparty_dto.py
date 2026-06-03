"""
DTO для работы с контрагентами.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class CounterpartyBaseDTO(BaseModel):
    """Базовый DTO для контрагента."""
    name: str = Field(..., min_length=1, max_length=200, description="Наименование контрагента")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    contact_info: Optional[str] = Field(None, max_length=500, description="Контактная информация")

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        """Валидация имени контрагента."""
        v = v.strip()
        if not v:
            raise ValueError("Имя контрагента не может быть пустым")
        if len(v) > 200:
            raise ValueError("Имя контрагента не должно превышать 200 символов")
        return v

    model_config = ConfigDict(
        from_attributes=True,
    )


class CounterpartyCreateDTO(CounterpartyBaseDTO):
    """DTO для создания контрагента."""
    pass


class CounterpartyUpdateDTO(BaseModel):
    """DTO для обновления контрагента."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Наименование контрагента")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    contact_info: Optional[str] = Field(None, max_length=500, description="Контактная информация")

    model_config = ConfigDict(
        from_attributes=True,
    )


class CounterpartyResponseDTO(CounterpartyBaseDTO):
    """DTO для ответа с данными контрагента."""
    id: UUID = Field(..., description="ID контрагента")
    transaction_count: int = Field(0, description="Количество транзакций")
    total_income: Decimal = Field(Decimal("0"), description="Общий доход от контрагента")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime = Field(..., description="Время последнего обновления")


class CounterpartyListDTO(BaseModel):
    """DTO для списка контрагентов."""
    counterparties: List[CounterpartyResponseDTO] = Field(default_factory=list, description="Список контрагентов")
    total_count: int = Field(0, description="Общее количество контрагентов")
    page: int = Field(1, description="Текущая страница")
    page_size: int = Field(100, description="Размер страницы")
    total_pages: int = Field(0, description="Общее количество страниц")


class CounterpartyFilterDTO(BaseModel):
    """DTO для фильтрации контрагентов."""
    search_query: Optional[str] = Field(None, description="Текст для поиска")
    has_transactions: Optional[bool] = Field(None, description="Есть ли транзакции")
    page: int = Field(1, ge=1, description="Номер страницы")
    page_size: int = Field(100, ge=1, le=1000, description="Размер страницы")
    order_by: str = Field("name_asc", description="Поле сортировки")
    
    model_config = ConfigDict(
    )
