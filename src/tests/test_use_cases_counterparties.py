"""
Тесты use cases для контрагентов.
"""
import pytest
from uuid import uuid4

from solepro.core.application.dto.counterparty_dto import (
    CounterpartyCreateDTO,
    CounterpartyUpdateDTO,
)
from solepro.core.application.dto.transaction_dto import TransactionFilterDTO
from solepro.core.application.use_cases.counterparty_use_cases import (
    AddCounterpartyUseCase,
    UpdateCounterpartyUseCase,
    DeleteCounterpartyUseCase,
    GetCounterpartyUseCase,
    ListCounterpartiesUseCase,
    SearchCounterpartiesUseCase,
    GetCounterpartyStatisticsUseCase,
)
from solepro.core.domain.entities.counterparty import Counterparty
from solepro.core.domain.exceptions.domain_exceptions import DuplicateEntityException
from solepro.infrastructure.database.repositories import SQLAlchemyCounterpartyRepository
from solepro.infrastructure.database.repositories import SQLAlchemyTransactionRepository
from solepro.core.domain.entities.transaction import Transaction
from solepro.core.domain.value_objects.money import Money
from decimal import Decimal
from datetime import datetime


class TestCounterpartyUseCases:
    def test_add_counterparty_duplicate_name(self, session):
        repository = SQLAlchemyCounterpartyRepository(session)
        use_case = AddCounterpartyUseCase(repository)

        dto = CounterpartyCreateDTO(name="Дубликат")
        use_case.execute(dto)

        with pytest.raises(DuplicateEntityException):
            use_case.execute(dto)

    def test_update_counterparty_duplicate_name(self, session):
        repository = SQLAlchemyCounterpartyRepository(session)
        use_case = UpdateCounterpartyUseCase(repository)

        first = repository.save(Counterparty(name="Первый"))
        second = repository.save(Counterparty(name="Второй"))

        dto = CounterpartyUpdateDTO(name="Первый")

        with pytest.raises(DuplicateEntityException):
            use_case.execute(second.id, dto)

    def test_search_counterparties(self, session):
        repository = SQLAlchemyCounterpartyRepository(session)
        use_case = SearchCounterpartiesUseCase(repository)

        repository.save(Counterparty(name="Alpha Company", description="Услуги"))
        repository.save(Counterparty(name="Beta", description="Торговля"))

        result = use_case.execute(query="Alpha")
        assert len(result.counterparties) == 1
        assert result.counterparties[0].name == "Alpha Company"

        result = use_case.execute(query="Торговля", fields=["description"])
        assert len(result.counterparties) == 1
        assert result.counterparties[0].name == "Beta"

    def test_delete_counterparty_existing_and_missing(self, session):
        repository = SQLAlchemyCounterpartyRepository(session)
        use_case = DeleteCounterpartyUseCase(repository)

        saved = repository.save(Counterparty(name="Delete Me"))
        assert use_case.execute(saved.id) is True
        assert use_case.execute(saved.id) is False

    def test_get_counterparty_found_and_not_found(self, session):
        repository = SQLAlchemyCounterpartyRepository(session)
        use_case = GetCounterpartyUseCase(repository)

        saved = repository.save(Counterparty(name="Lookup CP"))
        found = use_case.execute(saved.id)
        assert found is not None
        assert found.id == saved.id
        assert found.name == "Lookup CP"
        assert found.transaction_count == 0
        assert found.total_income == 0.0

        assert use_case.execute(uuid4()) is None

    def test_list_counterparties_pagination_and_aggregates(self, session):
        repository = SQLAlchemyCounterpartyRepository(session)
        tx_repository = SQLAlchemyTransactionRepository(session)
        use_case = ListCounterpartiesUseCase(repository)

        alpha = repository.save(Counterparty(name="Alpha List"))
        beta = repository.save(Counterparty(name="Beta List"))

        tx_repository.save(Transaction(
            date=datetime.now(),
            income=Money(Decimal("100")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            counterparty_id=alpha.id,
        ))

        page1 = use_case.execute(skip=0, limit=1, order_by="name_asc")
        page2 = use_case.execute(skip=1, limit=1, order_by="name_asc")
        assert page1.total_count == 2
        assert page1.total_pages == 2
        assert len(page1.counterparties) == 1
        assert len(page2.counterparties) == 1

        all_items = use_case.execute(skip=0, limit=10, order_by="name_asc").counterparties
        alpha_item = next(item for item in all_items if item.id == alpha.id)
        beta_item = next(item for item in all_items if item.id == beta.id)
        assert alpha_item.transaction_count == 1
        assert alpha_item.total_income == 100.0
        assert beta_item.transaction_count == 0
        assert beta_item.total_income == 0.0

    def test_search_counterparties_pagination(self, session):
        repository = SQLAlchemyCounterpartyRepository(session)
        use_case = SearchCounterpartiesUseCase(repository)

        repository.save(Counterparty(name="Gamma One"))
        repository.save(Counterparty(name="Gamma Two"))

        page = use_case.execute(query="Gamma", fields=["name"], skip=0, limit=1)
        assert len(page.counterparties) == 1
        assert page.total_count == 2
        assert page.total_pages == 2

    def test_get_counterparty_statistics(self, session):
        repository = SQLAlchemyCounterpartyRepository(session)
        tx_repository = SQLAlchemyTransactionRepository(session)
        use_case = GetCounterpartyStatisticsUseCase(repository)

        first = repository.save(Counterparty(name="Alpha"))
        second = repository.save(Counterparty(name="Beta"))

        tx_repository.save(Transaction(
            date=datetime.now(),
            income=Money(Decimal("100")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("10")),
            counterparty_id=first.id,
        ))
        tx_repository.save(Transaction(
            date=datetime.now(),
            income=Money(Decimal("50")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            counterparty_id=second.id,
        ))

        stats = use_case.execute()
        names = {item.counterparty_name for item in stats}
        assert {"Alpha", "Beta"}.issubset(names)

    def test_get_counterparty_statistics_respects_transaction_filter(self, session):
        repository = SQLAlchemyCounterpartyRepository(session)
        tx_repository = SQLAlchemyTransactionRepository(session)
        use_case = GetCounterpartyStatisticsUseCase(
            repository,
            transaction_repository=tx_repository
        )

        first = repository.save(Counterparty(name="Filtered Alpha"))
        second = repository.save(Counterparty(name="Filtered Beta"))

        tx_repository.save(Transaction(
            date=datetime(2025, 1, 5, 10, 0, 0),
            income=Money(Decimal("100")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("10")),
            counterparty_id=first.id,
        ))
        tx_repository.save(Transaction(
            date=datetime(2025, 2, 5, 10, 0, 0),
            income=Money(Decimal("200")),
            expense=Money(Decimal("0")),
            tax=Money(Decimal("0")),
            counterparty_id=second.id,
        ))

        january_filter = TransactionFilterDTO(
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31, 23, 59, 59),
        )
        stats = use_case.execute(filter_dto=january_filter)
        assert len(stats) == 1
        assert stats[0].counterparty_name == "Filtered Alpha"
        assert stats[0].transaction_count == 1

        tax_filter = TransactionFilterDTO(has_tax=True)
        tax_stats = use_case.execute(filter_dto=tax_filter)
        assert len(tax_stats) == 1
        assert tax_stats[0].counterparty_name == "Filtered Alpha"
