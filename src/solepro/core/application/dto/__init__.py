"""
Data Transfer Objects (DTO) для передачи данных между слоями.

DTO используются для:
- Ввода данных в Use Cases
- Вывода данных из Use Cases
- Сериализации для API/UI
"""

from .transaction_dto import (
    TransactionCreateDTO,
    TransactionUpdateDTO,
    TransactionResponseDTO,
    TransactionListDTO,
    TransactionFilterDTO,
)
from .counterparty_dto import (
    CounterpartyCreateDTO,
    CounterpartyUpdateDTO,
    CounterpartyResponseDTO,
    CounterpartyListDTO,
)
from .statistics_dto import (
    StatisticsDTO,
    MonthlyStatisticsDTO,
    CounterpartyStatisticsDTO,
)

__all__ = [
    "TransactionCreateDTO",
    "TransactionUpdateDTO",
    "TransactionResponseDTO",
    "TransactionListDTO",
    "TransactionFilterDTO",
    "CounterpartyCreateDTO",
    "CounterpartyUpdateDTO",
    "CounterpartyResponseDTO",
    "CounterpartyListDTO",
    "StatisticsDTO",
    "MonthlyStatisticsDTO",
    "CounterpartyStatisticsDTO",
]
