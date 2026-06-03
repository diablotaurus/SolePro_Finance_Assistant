"""
Shared DTO mappers for application use cases.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from .dto.counterparty_dto import CounterpartyResponseDTO
from .dto.statistics_dto import CounterpartyStatisticsDTO
from .dto.transaction_dto import TransactionResponseDTO
from ..domain.entities.counterparty import Counterparty
from ..domain.entities.transaction import Transaction


def to_transaction_response_dto(
    transaction: Transaction,
    *,
    counterparty_name: Optional[str] = None,
) -> TransactionResponseDTO:
    """Convert a transaction entity to response DTO."""
    return TransactionResponseDTO(
        id=transaction.id,
        date=transaction.date,
        income=transaction.income.to_decimal(),
        expense=transaction.expense.to_decimal(),
        tax=transaction.tax.to_decimal(),
        profit=transaction.calculate_profit().to_decimal(),
        counterparty_id=transaction.counterparty_id,
        counterparty_name=counterparty_name,
        note=transaction.note,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at,
    )


def to_counterparty_response_dto(
    counterparty: Counterparty,
    *,
    aggregate: Optional[dict[str, Any]] = None,
) -> CounterpartyResponseDTO:
    """Convert a counterparty entity and aggregate payload to response DTO."""
    payload = aggregate or {}
    return CounterpartyResponseDTO(
        id=counterparty.id,
        name=counterparty.name,
        description=counterparty.description,
        contact_info=counterparty.contact_info,
        transaction_count=int(payload.get("transaction_count", 0)),
        total_income=Decimal(str(payload.get("total_income", 0))),
        created_at=counterparty.created_at,
        updated_at=counterparty.updated_at,
    )


def to_counterparty_statistics_dto(item: dict[str, Any]) -> CounterpartyStatisticsDTO:
    """Convert raw statistics item to counterparty statistics DTO."""
    return CounterpartyStatisticsDTO(
        counterparty_id=str(item.get("counterparty_id", "")),
        counterparty_name=item.get("counterparty_name", ""),
        transaction_count=int(item.get("transaction_count", 0)),
        total_income=Decimal(str(item.get("total_income", 0))),
        total_expense=Decimal(str(item.get("total_expense", 0))),
        total_tax=Decimal(str(item.get("total_tax", 0))),
        total_profit=Decimal(str(item.get("total_profit", 0))),
        percentage_of_total=float(item.get("percentage_of_total", 0.0)),
    )
