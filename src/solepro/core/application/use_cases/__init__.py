"""
Use Cases (бизнес-сценарии) приложения.

Каждый Use Case представляет собой отдельный бизнес-сценарий
и следует принципу Single Responsibility.
"""

from .transaction_use_cases import (
    AddTransactionUseCase,
    UpdateTransactionUseCase,
    DeleteTransactionUseCase,
    GetTransactionUseCase,
    ListTransactionsUseCase,
    SearchTransactionsUseCase,
    GetTransactionStatisticsUseCase,
)
from .counterparty_use_cases import (
    AddCounterpartyUseCase,
    UpdateCounterpartyUseCase,
    DeleteCounterpartyUseCase,
    GetCounterpartyUseCase,
    ListCounterpartiesUseCase,
    SearchCounterpartiesUseCase,
    GetCounterpartyStatisticsUseCase,
)

__all__ = [
    "AddTransactionUseCase",
    "UpdateTransactionUseCase",
    "DeleteTransactionUseCase",
    "GetTransactionUseCase",
    "ListTransactionsUseCase",
    "SearchTransactionsUseCase",
    "GetTransactionStatisticsUseCase",
    "AddCounterpartyUseCase",
    "UpdateCounterpartyUseCase",
    "DeleteCounterpartyUseCase",
    "GetCounterpartyUseCase",
    "ListCounterpartiesUseCase",
    "SearchCounterpartiesUseCase",
    "GetCounterpartyStatisticsUseCase",
]
