"""
Тесты доменного слоя.
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal

from solepro.core.domain.entities.transaction import Transaction
from solepro.core.domain.entities.counterparty import Counterparty
from solepro.core.domain.value_objects.money import Money
from solepro.core.domain.enums.transaction_type import TransactionType
from solepro.core.domain.exceptions.domain_exceptions import (
    InvalidTransactionException,
    InvalidCounterpartyException,
    InvalidMoneyException,
)


class TestMoney:
    """Тесты для Value Object Money."""
    
    def test_create_money(self):
        """Тест создания Money."""
        money = Money(Decimal("100.50"), "RUB")
        assert money.value == Decimal("100.50")
        assert money.currency == "RUB"
    
    def test_money_from_string(self):
        """Тест создания Money из строки."""
        money = Money.from_string("1,000.50")
        assert money.value == Decimal("1000.50")
        
        money = Money.from_string("1000,50", "RUB")
        assert money.value == Decimal("1000.50")
    
    def test_money_from_float(self):
        """Тест создания Money из float."""
        money = Money.from_float(1000.50)
        assert money.value == Decimal("1000.50")
    
    def test_money_operations(self):
        """Тест арифметических операций с Money."""
        m1 = Money(Decimal("100"), "RUB")
        m2 = Money(Decimal("50"), "RUB")
        
        # Сложение
        result = m1 + m2
        assert result.value == Decimal("150")
        
        # Вычитание
        result = m1 - m2
        assert result.value == Decimal("50")
        
        # Умножение
        result = m1 * Decimal("2")
        assert result.value == Decimal("200")
        
        # Деление
        result = m1 / Decimal("2")
        assert result.value == Decimal("50")
    
    def test_money_comparison(self):
        """Тест сравнения Money."""
        m1 = Money(Decimal("100"), "RUB")
        m2 = Money(Decimal("50"), "RUB")
        m3 = Money(Decimal("100"), "RUB")
        
        assert m1 > m2
        assert m2 < m1
        assert m1 == m3
        assert m1 != m2
    
    def test_invalid_money(self):
        """Тест невалидных Money."""
        with pytest.raises(InvalidMoneyException):
            Money(Decimal("100"), "XYZ")  # Неподдерживаемая валюта

    def test_str_does_not_depend_on_system_locale(self):
        """str(Money) работает на любой системе (регрессия v1.4.20)."""
        money = Money(Decimal("1234567.89"), "RUB")
        assert str(money) == "1 234 567,89 ₽"

    def test_format_falls_back_when_locale_unavailable(self, monkeypatch):
        """Недоступная локаль не роняет форматирование, а даёт фолбэк.

        setlocale подменяется, т.к. Windows принимает почти любые имена
        локалей, а на Linux без ru_RU реальный вызов бросает locale.Error.
        """
        import locale as locale_module

        def _raise(*args, **kwargs):
            raise locale_module.Error("unsupported locale")

        monkeypatch.setattr(
            "solepro.core.domain.value_objects.money.locale.setlocale", _raise
        )

        money = Money(Decimal("1000.50"), "RUB")
        result = money.format(show_currency=True, locale_name="ru_RU")
        assert result == "1 000,50 ₽"

    def test_format_without_currency(self):
        money = Money(Decimal("-25.5"), "RUB")
        assert money.format(show_currency=False) == "-25,50"


class TestTransaction:
    """Тесты для сущности Transaction."""
    
    def test_create_transaction(self):
        """Тест создания транзакции."""
        transaction = Transaction(
            date=datetime.now(),
            income=Money(Decimal("1000")),
            expense=Money(Decimal("500")),
            tax=Money(Decimal("100")),
            note="Тестовая транзакция",
        )
        
        assert transaction.income.value == Decimal("1000")
        assert transaction.expense.value == Decimal("500")
        assert transaction.tax.value == Decimal("100")
        assert transaction.note == "Тестовая транзакция"
        assert transaction.is_valid is True
    
    def test_calculate_profit(self):
        """Тест расчета прибыли."""
        transaction = Transaction(
            income=Money(Decimal("1000")),
            expense=Money(Decimal("500")),
            tax=Money(Decimal("100")),
        )
        
        profit = transaction.calculate_profit()
        assert profit.value == Decimal("400")
    
    def test_transaction_type(self):
        """Тест определения типа транзакции."""
        # Доходная транзакция
        income_transaction = Transaction(income=Money(Decimal("1000")))
        assert income_transaction.get_transaction_type() == TransactionType.INCOME
        
        # Расходная транзакция
        expense_transaction = Transaction(expense=Money(Decimal("500")))
        assert expense_transaction.get_transaction_type() == TransactionType.EXPENSE
        
        # Смешанная транзакция
        mixed_transaction = Transaction(
            income=Money(Decimal("1000")),
            expense=Money(Decimal("500")),
        )
        assert mixed_transaction.get_transaction_type() == TransactionType.MIXED
        
        # Нейтральная транзакция
        neutral_transaction = Transaction()
        assert neutral_transaction.get_transaction_type() == TransactionType.NEUTRAL
    
    def test_update_transaction(self):
        """Тест обновления транзакции."""
        transaction = Transaction(
            income=Money(Decimal("1000")),
            note="Старая заметка",
        )
        
        updated = transaction.update(
            income=Money(Decimal("2000")),
            note="Новая заметка",
        )
        
        assert updated.income.value == Decimal("2000")
        assert updated.note == "Новая заметка"
        assert updated.id == transaction.id  # ID должен остаться прежним

    def test_update_transaction_clear_counterparty(self):
        """Снятие контрагента: None означает «не менять», нужен явный флаг."""
        from uuid import uuid4

        counterparty_id = uuid4()
        transaction = Transaction(
            income=Money(Decimal("1000")),
            counterparty_id=counterparty_id,
        )

        # None не снимает контрагента.
        kept = transaction.update(note="Просто заметка")
        assert kept.counterparty_id == counterparty_id

        # Явный флаг снимает.
        cleared = transaction.update(clear_counterparty=True)
        assert cleared.counterparty_id is None

        # Новый контрагент имеет приоритет над флагом.
        replacement_id = uuid4()
        replaced = transaction.update(
            counterparty_id=replacement_id, clear_counterparty=True
        )
        assert replaced.counterparty_id == replacement_id

    def test_invalid_transaction(self):
        """Тест невалидных транзакций."""
        # Дата в будущем
        future_date = datetime(2100, 1, 1)
        with pytest.raises(InvalidTransactionException):
            Transaction(date=future_date)
        
        # Отрицательный доход
        with pytest.raises(InvalidTransactionException):
            Transaction(income=Money(Decimal("-100")))
        
        # Отрицательный расход
        with pytest.raises(InvalidTransactionException):
            Transaction(expense=Money(Decimal("-100")))
        
        # Отрицательный налог
        with pytest.raises(InvalidTransactionException):
            Transaction(tax=Money(Decimal("-100")))


class TestCounterparty:
    """Тесты для сущности Counterparty."""
    
    def test_create_counterparty(self):
        """Тест создания контрагента."""
        counterparty = Counterparty(
            name="Тестовый контрагент",
            description="Описание",
            contact_info="test@example.com",
        )
        
        assert counterparty.name == "Тестовый контрагент"
        assert counterparty.description == "Описание"
        assert counterparty.contact_info == "test@example.com"
        assert counterparty.is_valid is True
    
    def test_update_counterparty(self):
        """Тест обновления контрагента."""
        counterparty = Counterparty(name="Старое имя")
        
        updated = counterparty.update(
            name="Новое имя",
            description="Новое описание",
        )
        
        assert updated.name == "Новое имя"
        assert updated.description == "Новое описание"
        assert updated.id == counterparty.id  # ID должен остаться прежним
    
    def test_invalid_counterparty(self):
        """Тест невалидных контрагентов."""
        # Пустое имя
        with pytest.raises(InvalidCounterpartyException):
            Counterparty(name="")
        
        # Имя только из пробелов
        with pytest.raises(InvalidCounterpartyException):
            Counterparty(name="   ")
        
        # Слишком длинное имя
        long_name = "a" * 201
        with pytest.raises(InvalidCounterpartyException):
            Counterparty(name=long_name)
