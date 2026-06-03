"""
Доменная сущность Транзакция.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from ..value_objects.money import Money
from ..enums.transaction_type import TransactionType
from ..exceptions.domain_exceptions import InvalidTransactionException


@dataclass(frozen=True)
class Transaction:
    """
    Сущность транзакции.
    
    Атрибуты:
        id: Уникальный идентификатор транзакции
        date: Дата транзакции
        income: Сумма дохода
        expense: Сумма расхода
        tax: Сумма налога
        counterparty_id: ID контрагента
        note: Примечание
        created_at: Время создания
        updated_at: Время последнего обновления
    """
    id: UUID = field(default_factory=uuid4)
    date: datetime = field(default_factory=datetime.now)
    income: Money = field(default_factory=lambda: Money(0))
    expense: Money = field(default_factory=lambda: Money(0))
    tax: Money = field(default_factory=lambda: Money(0))
    counterparty_id: Optional[UUID] = None
    note: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Валидация инвариантов домена после инициализации."""
        self._validate()
    
    def _validate(self) -> None:
        """Валидация бизнес-правил транзакции."""
        errors = []
        
        # Дата не может быть в будущем (с допущением для сегодняшнего дня)
        if self.date > datetime.now():
            errors.append("Дата транзакции не может быть в будущем")
        
        # Суммы не могут быть отрицательными
        if self.income.value < 0:
            errors.append("Сумма дохода не может быть отрицательной")
        
        if self.expense.value < 0:
            errors.append("Сумма расхода не может быть отрицательной")
        
        if self.tax.value < 0:
            errors.append("Сумма налога не может быть отрицательной")
        
        # Прибыль должна быть разумной (не проверяем строго, только предупреждаем)
        profit = self.calculate_profit()
        if profit.value < -1000000:  # Убыток более 1 млн
            errors.append("Убыток транзакции подозрительно велик")
        
        if errors:
            raise InvalidTransactionException(
                f"Ошибка валидации транзакции: {'; '.join(errors)}"
            )
    
    def calculate_profit(self) -> Money:
        """Рассчитать прибыль от транзакции."""
        return self.income - self.expense - self.tax
    
    def get_transaction_type(self) -> TransactionType:
        """Определить тип транзакции на основе сумм."""
        if self.income.value > 0 and self.expense.value == 0:
            return TransactionType.INCOME
        elif self.expense.value > 0 and self.income.value == 0:
            return TransactionType.EXPENSE
        elif self.income.value > 0 and self.expense.value > 0:
            return TransactionType.MIXED
        else:
            return TransactionType.NEUTRAL
    
    def update(
        self,
        income: Optional[Money] = None,
        expense: Optional[Money] = None,
        tax: Optional[Money] = None,
        note: Optional[str] = None,
        date: Optional[datetime] = None,
        counterparty_id: Optional[UUID] = None,
    ) -> "Transaction":
        """
        Создать новую версию транзакции с обновленными значениями.
        
        Возвращает новый объект Transaction, так как сущность immutable.
        """
        from dataclasses import replace
        
        return replace(
            self,
            income=income if income is not None else self.income,
            expense=expense if expense is not None else self.expense,
            tax=tax if tax is not None else self.tax,
            note=note if note is not None else self.note,
            date=date if date is not None else self.date,
            counterparty_id=counterparty_id if counterparty_id is not None else self.counterparty_id,
            updated_at=datetime.now(),
        )
    
    @property
    def is_valid(self) -> bool:
        """Проверка валидности транзакции."""
        try:
            self._validate()
            return True
        except InvalidTransactionException:
            return False
    
    def __str__(self) -> str:
        profit = self.calculate_profit()
        return (
            f"Транзакция от {self.date.strftime('%d.%m.%Y')} | "
            f"Доход: {self.income} | Расход: {self.expense} | "
            f"Налог: {self.tax} | Прибыль: {profit}"
        )
