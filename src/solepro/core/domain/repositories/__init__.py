"""
Интерфейсы репозиториев доменного слоя.

Реализация принципа Dependency Inversion:
- Domain layer зависит от абстракций (интерфейсов)
- Infrastructure layer реализует эти интерфейсы
"""
from .transaction_repository import TransactionRepository, TransactionView
from .counterparty_repository import CounterpartyRepository

__all__ = ["TransactionRepository", "TransactionView", "CounterpartyRepository"]
