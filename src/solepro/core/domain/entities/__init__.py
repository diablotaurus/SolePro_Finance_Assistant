"""
Доменные сущности приложения.

Сущности содержат бизнес-логику и инварианты домена.
Они не зависят от инфраструктуры, фреймворков или UI.
"""

from .transaction import Transaction
from .counterparty import Counterparty

__all__ = ["Transaction", "Counterparty"]
