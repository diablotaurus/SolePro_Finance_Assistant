"""
Спецификации фильтрации для прикладного слоя.

Содержит единый предикат соответствия транзакции набору активных фильтров,
который используется во всех Use Cases (списки, поиск, статистика). Это
устраняет дублирование логики фильтрации и нормализации дат (DRY) и держит
правило фильтрации в одном месте (SRP).
"""
from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal
from typing import Optional
from uuid import UUID

from ..domain.entities.transaction import Transaction
from ..domain.enums.transaction_type import TransactionType
from .dto.transaction_dto import TransactionFilterDTO


class TransactionFilterSpecification:
    """Единый предикат соответствия транзакции активным фильтрам."""

    def __init__(
        self,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        counterparty_id: Optional[UUID] = None,
        transaction_type: Optional[TransactionType] = None,
        has_tax: Optional[bool] = None,
        no_tax: Optional[bool] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
    ) -> None:
        self._start_dt = self._normalize_start(start_date)
        self._end_dt = self._normalize_end(end_date)
        self._counterparty_id = counterparty_id
        self._transaction_type = transaction_type
        self._has_tax = has_tax
        self._no_tax = no_tax
        self._min_amount = min_amount
        self._max_amount = max_amount

    @classmethod
    def from_filter_dto(
        cls, filter_dto: TransactionFilterDTO
    ) -> "TransactionFilterSpecification":
        """Построить спецификацию из DTO фильтра."""
        return cls(
            start_date=filter_dto.start_date,
            end_date=filter_dto.end_date,
            counterparty_id=filter_dto.counterparty_id,
            transaction_type=filter_dto.transaction_type,
            has_tax=filter_dto.has_tax,
            no_tax=filter_dto.no_tax,
            min_amount=filter_dto.min_amount,
            max_amount=filter_dto.max_amount,
        )

    @property
    def start_datetime(self) -> Optional[datetime]:
        """Нормализованная начальная дата (или None)."""
        return self._start_dt

    @property
    def end_datetime(self) -> Optional[datetime]:
        """Нормализованная конечная дата (или None)."""
        return self._end_dt

    def for_period(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> "TransactionFilterSpecification":
        """Вернуть копию спецификации с другим периодом (для сравнения периодов)."""
        return TransactionFilterSpecification(
            start_date=start_date,
            end_date=end_date,
            counterparty_id=self._counterparty_id,
            transaction_type=self._transaction_type,
            has_tax=self._has_tax,
            no_tax=self._no_tax,
            min_amount=self._min_amount,
            max_amount=self._max_amount,
        )

    def is_satisfied_by(self, transaction: Transaction) -> bool:
        """Проверить, удовлетворяет ли транзакция фильтрам."""
        if self._start_dt and transaction.date < self._start_dt:
            return False
        if self._end_dt and transaction.date > self._end_dt:
            return False
        if self._counterparty_id and transaction.counterparty_id != self._counterparty_id:
            return False
        if self._transaction_type and transaction.get_transaction_type() != self._transaction_type:
            return False

        tax = transaction.tax.to_decimal()
        if self._has_tax and tax <= 0:
            return False
        if self._no_tax and tax > 0:
            return False

        amount_total = (
            transaction.income.to_decimal()
            + transaction.expense.to_decimal()
            + tax
        )
        if self._min_amount is not None and amount_total < self._min_amount:
            return False
        if self._max_amount is not None and amount_total > self._max_amount:
            return False

        return True

    @staticmethod
    def _normalize_start(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.combine(value, time.min)

    @staticmethod
    def _normalize_end(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            # Конечная граница с временем 00:00 означает «весь этот день»:
            # date-пикеры отдают дату без времени, а pydantic приводит её к
            # datetime полуночи — без расширения до конца дня терялись бы
            # транзакции с ненулевым временем (например, добавленные ботом).
            if value.time() == time.min:
                return datetime.combine(value.date(), time.max)
            return value
        return datetime.combine(value, time.max)


__all__ = ["TransactionFilterSpecification"]
