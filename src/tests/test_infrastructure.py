"""
Тесты инфраструктурного слоя.
"""
import pytest
from datetime import datetime
from uuid import uuid4, UUID
from decimal import Decimal

from solepro.infrastructure.database.models import TransactionModel, CounterpartyModel
from solepro.infrastructure.database.repositories import (
    SQLAlchemyTransactionRepository,
    SQLAlchemyCounterpartyRepository,
)
from solepro.core.domain.entities.counterparty import Counterparty
from solepro.core.domain.entities.transaction import Transaction
from solepro.core.domain.value_objects.money import Money
from solepro.core.domain.enums.transaction_type import TransactionType
from solepro.core.domain.exceptions.domain_exceptions import EntityNotFoundException


class TestSQLAlchemyModels:
    """Тесты для SQLAlchemy моделей."""
    
    def test_create_counterparty_model(self, session):
        """Тест создания модели контрагента."""
        counterparty = CounterpartyModel(
            name="Тестовый контрагент",
            description="Описание",
            contact_info="test@example.com",
        )
        
        session.add(counterparty)
        session.commit()
        
        assert counterparty.id is not None
        assert counterparty.name == "Тестовый контрагент"
    
    def test_create_transaction_model(self, session):
        """Тест создания модели транзакции."""
        # Сначала создаем контрагента
        counterparty = CounterpartyModel(name="Контрагент")
        session.add(counterparty)
        session.commit()
        
        # Создаем транзакцию
        transaction = TransactionModel(
            date=datetime.now(),
            income=Decimal("1000.00"),
            expense=Decimal("500.00"),
            tax=Decimal("100.00"),
            note="Тестовая транзакция",
            counterparty_id=counterparty.id,
        )
        
        session.add(transaction)
        session.commit()
        
        assert transaction.id is not None
        assert transaction.income == Decimal("1000.00")
        assert transaction.expense == Decimal("500.00")
        assert transaction.tax == Decimal("100.00")
        assert transaction.profit == Decimal("400.00")  # 1000 - 500 - 100
        assert transaction.note == "Тестовая транзакция"
        assert transaction.counterparty_id == counterparty.id
    
    def test_transaction_validation(self):
        """Тест валидации транзакции."""
        # Отрицательный доход
        with pytest.raises(ValueError):
            TransactionModel(income=Decimal("-100.00"))
        
        # Отрицательный расход
        with pytest.raises(ValueError):
            TransactionModel(expense=Decimal("-100.00"))
        
        # Отрицательный налог
        with pytest.raises(ValueError):
            TransactionModel(tax=Decimal("-100.00"))
        
        # Дата в будущем
        future_date = datetime(2100, 1, 1)
        with pytest.raises(ValueError):
            TransactionModel(date=future_date)
    
    def test_counterparty_validation(self):
        """Тест валидации контрагента."""
        # Пустое имя
        with pytest.raises(ValueError):
            CounterpartyModel(name="")
        
        # Слишком длинное имя
        long_name = "a" * 201
        with pytest.raises(ValueError):
            CounterpartyModel(name=long_name)


class TestTransactionRepository:
    """Тесты для репозитория транзакций."""
    
    @pytest.fixture
    def repository(self, session):
        """Создать репозиторий для тестов."""
        return SQLAlchemyTransactionRepository(session)
    
    @pytest.fixture
    def counterparty(self, session):
        """Создать тестового контрагента."""
        counterparty = CounterpartyModel(name="Тестовый контрагент")
        session.add(counterparty)
        session.commit()
        return counterparty
    
    def test_save_and_get_transaction(self, repository, counterparty):
        """Тест сохранения и получения транзакции."""
        from solepro.core.domain.entities.transaction import Transaction
        from solepro.core.domain.value_objects.money import Money
        
        # Создаем доменную сущность с несуществующим контрагентом
        transaction = Transaction(
            date=datetime.now(),
            income=Money(Decimal("1000")),
            expense=Money(Decimal("500")),
            tax=Money(Decimal("100")),
            counterparty_id=uuid4(),  # Несуществующий контрагент
            note="Тестовая транзакция",
        )
        
        # Пытаемся сохранить - должно вызвать исключение
        with pytest.raises(EntityNotFoundException):
            repository.save(transaction)
        
        # Создаем с валидным контрагентом
        counterparty_id = UUID(str(counterparty.id))
        valid_transaction = Transaction(
            date=datetime.now(),
            income=Money(Decimal("1000")),
            expense=Money(Decimal("500")),
            tax=Money(Decimal("100")),
            counterparty_id=counterparty_id,
            note="Тестовая транзакция",
        )
        saved = repository.save(valid_transaction)
        loaded = repository.get_by_id(saved.id)

        assert loaded is not None
        assert loaded.counterparty_id == counterparty_id
        assert loaded.income.value == Decimal("1000")

    def test_search_transactions_by_note(self, repository):
        """Тест поиска транзакций по примечанию."""
        from solepro.core.domain.entities.transaction import Transaction
        from solepro.core.domain.value_objects.money import Money

        tx_alpha = Transaction(
            date=datetime.now(),
            income=Money(Decimal("10")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            note="alpha note",
        )
        repository.save(tx_alpha)

        results = repository.search(query="alpha", fields=["note"])
        assert len(results) == 1
        assert results[0].note == "alpha note"

    def test_find_all_ordering_by_date(self, repository):
        """Тест сортировки транзакций по дате."""
        from solepro.core.domain.entities.transaction import Transaction
        from solepro.core.domain.value_objects.money import Money

        older = Transaction(
            date=datetime(2024, 1, 1),
            income=Money(Decimal("1")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
        )
        newer = Transaction(
            date=datetime(2025, 1, 1),
            income=Money(Decimal("2")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
        )
        repository.save(older)
        repository.save(newer)

        results = repository.find_all(order_by="date_asc")
        assert results[0].date <= results[-1].date

    def test_find_by_date_range(self, repository):
        from solepro.core.domain.entities.transaction import Transaction
        from solepro.core.domain.value_objects.money import Money

        inside = Transaction(
            date=datetime(2025, 1, 15, 12, 0, 0),
            income=Money(Decimal("10")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            note="inside-range",
        )
        outside = Transaction(
            date=datetime(2024, 12, 31, 23, 59, 59),
            income=Money(Decimal("10")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            note="outside-range",
        )
        repository.save(inside)
        repository.save(outside)

        results = repository.find_by_date_range(
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31, 23, 59, 59),
        )
        notes = {tx.note for tx in results}
        assert "inside-range" in notes
        assert "outside-range" not in notes

    def test_exists_transaction(self, repository):
        from solepro.core.domain.entities.transaction import Transaction
        from solepro.core.domain.value_objects.money import Money

        tx = repository.save(Transaction(
            date=datetime.now(),
            income=Money(Decimal("1")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
        ))
        assert repository.exists(tx.id) is True
        assert repository.exists(uuid4()) is False


class TestCounterpartyRepository:
    """Тесты для репозитория контрагентов."""
    
    @pytest.fixture
    def repository(self, session):
        """Создать репозиторий для тестов."""
        return SQLAlchemyCounterpartyRepository(session)
    
    def test_save_and_get_counterparty(self, repository):
        """Тест сохранения и получения контрагента."""
        from solepro.core.domain.entities.counterparty import Counterparty
        
        # Создаем доменную сущность
        counterparty = Counterparty(
            name="Тестовый контрагент",
            description="Описание",
            contact_info="test@example.com",
        )
        
        # Сохраняем
        saved = repository.save(counterparty)
        
        # Получаем по ID
        retrieved = repository.get_by_id(saved.id)
        
        assert retrieved is not None
        assert retrieved.name == "Тестовый контрагент"
        assert retrieved.description == "Описание"
        assert retrieved.contact_info == "test@example.com"
    
    def test_find_all_counterparties(self, repository):
        """Тест получения всех контрагентов."""
        # Создаем несколько контрагентов
        counterparties = [
            Counterparty(name=f"Контрагент {i}")
            for i in range(5)
        ]
        
        for cp in counterparties:
            repository.save(cp)
        
        # Получаем все
        all_counterparties = repository.find_all()
        
        assert len(all_counterparties) >= 5
    
    def test_search_counterparties(self, repository):
        """Тест поиска контрагентов."""
        # Создаем контрагента с уникальным именем
        unique_name = "УникальныйКонтрагент123"
        counterparty = Counterparty(
            name=unique_name,
            description="Поисковое описание",
        )
        
        repository.save(counterparty)
        
        # Ищем по имени
        results = repository.search(query="Уникальный")
        assert len(results) == 1
        assert results[0].name == unique_name
        
        # Ищем по описанию
        results = repository.search(query="описание", fields=["description"])
        assert len(results) == 1
        assert results[0].description == "Поисковое описание"
    
    def test_duplicate_counterparty(self, repository):
        """Тест дублирования контрагента."""
        from solepro.core.domain.exceptions.domain_exceptions import DuplicateEntityException
        
        counterparty1 = Counterparty(name="Дубликат")
        repository.save(counterparty1)
        
        # Пытаемся создать контрагента с таким же именем
        counterparty2 = Counterparty(name="Дубликат")
        
        with pytest.raises(DuplicateEntityException):
            repository.save(counterparty2)

    def test_get_transaction_aggregates(self, repository, session):
        """Тест агрегатов по транзакциям."""
        from solepro.core.domain.entities.transaction import Transaction
        from solepro.core.domain.value_objects.money import Money
        from solepro.infrastructure.database.repositories import SQLAlchemyTransactionRepository

        counterparty = Counterparty(name="Счетчик")
        saved_counterparty = repository.save(counterparty)

        tx_repo = SQLAlchemyTransactionRepository(session)
        tx_repo.save(Transaction(
            date=datetime.now(),
            income=Money(Decimal("100")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            counterparty_id=saved_counterparty.id,
        ))
        tx_repo.save(Transaction(
            date=datetime.now(),
            income=Money(Decimal("50")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            counterparty_id=saved_counterparty.id,
        ))

        aggregates = repository.get_transaction_aggregates([saved_counterparty.id])
        data = aggregates.get(saved_counterparty.id)

        assert data is not None
        assert data["transaction_count"] == 2
        assert data["total_income"] == 150.0

    def test_find_all_order_by_transaction_count(self, repository, session):
        tx_repo = SQLAlchemyTransactionRepository(session)

        first = repository.save(Counterparty(name="Top Counterparty"))
        second = repository.save(Counterparty(name="Low Counterparty"))

        tx_repo.save(Transaction(
            date=datetime.now(),
            income=Money(Decimal("10")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            counterparty_id=first.id,
        ))
        tx_repo.save(Transaction(
            date=datetime.now(),
            income=Money(Decimal("20")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            counterparty_id=first.id,
        ))
        tx_repo.save(Transaction(
            date=datetime.now(),
            income=Money(Decimal("5")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            counterparty_id=second.id,
        ))

        rows = repository.find_all(order_by="transaction_count_desc")
        assert len(rows) >= 2
        assert rows[0].id == first.id

    def test_counterparty_statistics_and_exists(self, repository, session):
        tx_repo = SQLAlchemyTransactionRepository(session)

        alpha = repository.save(Counterparty(name="Stats Alpha"))
        beta = repository.save(Counterparty(name="Stats Beta"))

        tx_repo.save(Transaction(
            date=datetime.now(),
            income=Money(Decimal("100")),
            expense=Money(Decimal("30")),
            tax=Money(Decimal("10")),
            counterparty_id=alpha.id,
        ))
        tx_repo.save(Transaction(
            date=datetime.now(),
            income=Money(Decimal("50")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            counterparty_id=beta.id,
        ))

        stats = repository.get_statistics()
        assert stats["total_count"] >= 2
        assert stats["with_transactions"] >= 2
        assert len(stats["top_counterparties"]) >= 2
        names = {item["counterparty_name"] for item in stats["top_counterparties"]}
        assert "Stats Alpha" in names
        assert "Stats Beta" in names

        assert repository.exists(alpha.id) is True
        assert repository.exists(uuid4()) is False
        assert repository.exists_by_name("Stats Alpha") is True
        assert repository.exists_by_name("stats alpha") is True
        assert repository.exists_by_name("Missing Name") is False
