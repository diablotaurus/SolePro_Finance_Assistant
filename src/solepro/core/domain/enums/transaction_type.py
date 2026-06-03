"""
Перечисления для типов транзакций.
"""
from enum import Enum, auto


class TransactionType(Enum):
    """
    Типы транзакций.
    
    INCOME: Только доход (приход денег)
    EXPENSE: Только расход (расход денег)
    MIXED: Смешанная операция (и доход и расход)
    NEUTRAL: Нейтральная (без движения денег)
    """
    INCOME = auto()
    EXPENSE = auto()
    MIXED = auto()
    NEUTRAL = auto()
    
    def __str__(self) -> str:
        """Строковое представление для UI."""
        return {
            TransactionType.INCOME: "Доход",
            TransactionType.EXPENSE: "Расход",
            TransactionType.MIXED: "Смешанная",
            TransactionType.NEUTRAL: "Нейтральная"
        }[self]
