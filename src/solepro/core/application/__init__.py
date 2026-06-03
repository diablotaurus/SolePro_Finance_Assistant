"""
Application слой приложения.

Содержит Use Cases (бизнес-сценарии), DTO и сервисы приложения.
Этот слой зависит только от Domain слоя и реализует бизнес-правила.
"""

from .use_cases import *
from .dto import *
from .unit_of_work import *
from .mappers import *
from .specifications import *

__all__ = [
    # Use Cases
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
    
    # DTO
    "TransactionCreateDTO",
    "TransactionUpdateDTO",
    "TransactionResponseDTO",
    "CounterpartyCreateDTO",
    "CounterpartyUpdateDTO",
    "CounterpartyResponseDTO",
    "StatisticsDTO",
    "UnitOfWork",
    "RepositoryUnitOfWork",
    "to_transaction_response_dto",
    "to_counterparty_response_dto",
    "to_counterparty_statistics_dto",

    # Specifications
    "TransactionFilterSpecification",
]
