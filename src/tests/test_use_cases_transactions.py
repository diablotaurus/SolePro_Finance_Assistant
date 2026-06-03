"""
Тесты use cases для транзакций.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import uuid4, UUID

import pytest

from solepro.core.application.dto.transaction_dto import (
    TransactionCreateDTO,
    TransactionUpdateDTO,
    TransactionFilterDTO,
)
from solepro.core.application.use_cases.transaction_use_cases import (
    AddTransactionUseCase,
    UpdateTransactionUseCase,
    DeleteTransactionUseCase,
    GetTransactionUseCase,
    ListTransactionsUseCase,
    SearchTransactionsUseCase,
    GetTransactionStatisticsUseCase,
)
from solepro.core.domain.entities.counterparty import Counterparty
from solepro.core.domain.entities.transaction import Transaction
from solepro.core.domain.enums.transaction_type import TransactionType
from solepro.core.domain.exceptions.domain_exceptions import EntityNotFoundException
from solepro.core.domain.value_objects.money import Money
from solepro.infrastructure.database.repositories import (
    SQLAlchemyTransactionRepository,
    SQLAlchemyCounterpartyRepository,
)


def _create_counterparty(repository, name: str) -> Counterparty:
    counterparty = Counterparty(name=name)
    return repository.save(counterparty)


def _create_transaction(
    repository,
    *,
    date: datetime,
    income: Decimal,
    expense: Decimal,
    tax: Decimal,
    counterparty_id: Optional[UUID] = None,
    note: str = ""
) -> Transaction:
    transaction = Transaction(
        date=date,
        income=Money(income),
        expense=Money(expense),
        tax=Money(tax),
        counterparty_id=counterparty_id,
        note=note,
    )
    return repository.save(transaction)


class TestTransactionUseCases:
    def test_add_transaction_creates_counterparty_by_name(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        cp_repo = SQLAlchemyCounterpartyRepository(session)
        use_case = AddTransactionUseCase(tx_repo, cp_repo)

        dto = TransactionCreateDTO(
            date=datetime.now(),
            income=Decimal("100"),
            expense=Decimal("0"),
            tax=Decimal("0"),
            counterparty_name="Новый контрагент",
            note="Тест",
        )

        result = use_case.execute(dto)

        assert result.counterparty_id is not None
        assert result.counterparty_name == "Новый контрагент"
        assert cp_repo.get_by_id(result.counterparty_id) is not None

    def test_add_transaction_uses_existing_counterparty(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        cp_repo = SQLAlchemyCounterpartyRepository(session)
        use_case = AddTransactionUseCase(tx_repo, cp_repo)

        saved_counterparty = _create_counterparty(cp_repo, "Партнер")

        dto = TransactionCreateDTO(
            date=datetime.now(),
            income=Decimal("250"),
            expense=Decimal("50"),
            tax=Decimal("20"),
            counterparty_id=saved_counterparty.id,
            note="Контрагент по ID",
        )

        result = use_case.execute(dto)

        assert result.counterparty_id == saved_counterparty.id
        assert result.counterparty_name == "Партнер"

    def test_update_transaction_updates_amounts_and_note(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        cp_repo = SQLAlchemyCounterpartyRepository(session)
        use_case = UpdateTransactionUseCase(tx_repo, cp_repo)

        saved = _create_transaction(
            tx_repo,
            date=datetime.now(),
            income=Decimal("100"),
            expense=Decimal("30"),
            tax=Decimal("10"),
            note="Старое",
        )

        dto = TransactionUpdateDTO(
            income=Decimal("200"),
            expense=Decimal("20"),
            tax=Decimal("5"),
            note="Новое",
        )

        updated = use_case.execute(saved.id, dto)

        assert updated.income == Decimal("200")
        assert updated.expense == Decimal("20")
        assert updated.tax == Decimal("5")
        assert updated.note == "Новое"

    def test_update_transaction_rejects_unknown_counterparty(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        cp_repo = SQLAlchemyCounterpartyRepository(session)
        use_case = UpdateTransactionUseCase(tx_repo, cp_repo)

        saved = _create_transaction(
            tx_repo,
            date=datetime.now(),
            income=Decimal("50"),
            expense=Decimal("0"),
            tax=Decimal("0"),
        )

        dto = TransactionUpdateDTO(counterparty_id=uuid4())

        with pytest.raises(EntityNotFoundException):
            use_case.execute(saved.id, dto)

    def test_delete_transaction_existing_and_missing(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        use_case = DeleteTransactionUseCase(tx_repo)

        saved = _create_transaction(
            tx_repo,
            date=datetime.now(),
            income=Decimal("10"),
            expense=Decimal("0"),
            tax=Decimal("0"),
        )

        assert use_case.execute(saved.id) is True
        assert use_case.execute(saved.id) is False

    def test_get_transaction_found_and_not_found(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        cp_repo = SQLAlchemyCounterpartyRepository(session)
        use_case = GetTransactionUseCase(tx_repo, cp_repo)
        saved_counterparty = _create_counterparty(cp_repo, "Lookup Partner")

        saved = _create_transaction(
            tx_repo,
            date=datetime.now(),
            income=Decimal("30"),
            expense=Decimal("5"),
            tax=Decimal("1"),
            counterparty_id=saved_counterparty.id,
            note="lookup",
        )

        found = use_case.execute(saved.id)
        assert found is not None
        assert found.id == saved.id
        assert found.note == "lookup"
        assert found.counterparty_name == "Lookup Partner"

        missing = use_case.execute(uuid4())
        assert missing is None

    def test_list_transactions_pagination_and_filters(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        cp_repo = SQLAlchemyCounterpartyRepository(session)
        use_case = ListTransactionsUseCase(tx_repo, cp_repo)

        cp = _create_counterparty(cp_repo, "List Partner")
        _create_transaction(
            tx_repo,
            date=datetime(2024, 1, 1, 10, 0, 0),
            income=Decimal("100"),
            expense=Decimal("0"),
            tax=Decimal("0"),
            counterparty_id=cp.id,
            note="t1",
        )
        _create_transaction(
            tx_repo,
            date=datetime(2024, 1, 2, 10, 0, 0),
            income=Decimal("0"),
            expense=Decimal("50"),
            tax=Decimal("0"),
            note="t2",
        )
        _create_transaction(
            tx_repo,
            date=datetime(2024, 1, 3, 10, 0, 0),
            income=Decimal("25"),
            expense=Decimal("5"),
            tax=Decimal("2"),
            note="t3",
        )

        paged = use_case.execute(skip=0, limit=2, order_by="date_asc")
        assert len(paged.transactions) == 2
        assert paged.total_count == 3
        assert paged.total_pages == 2
        assert paged.transactions[0].date <= paged.transactions[1].date

        filtered = use_case.execute(
            skip=0,
            limit=10,
            order_by="date_asc",
            transaction_type=TransactionType.EXPENSE,
            no_tax=True,
        )
        assert filtered.total_count == 1
        assert len(filtered.transactions) == 1
        assert filtered.transactions[0].note == "t2"

        with_amount_bounds = use_case.execute(
            skip=0,
            limit=10,
            min_amount=Decimal("30"),
            max_amount=Decimal("40"),
        )
        assert with_amount_bounds.total_count == 1
        assert with_amount_bounds.transactions[0].note == "t3"

    def test_search_transactions_with_filters(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        cp_repo = SQLAlchemyCounterpartyRepository(session)
        use_case = SearchTransactionsUseCase(tx_repo, cp_repo)

        cp = _create_counterparty(cp_repo, "Search Partner")
        _create_transaction(
            tx_repo,
            date=datetime(2025, 1, 1, 10, 0, 0),
            income=Decimal("50"),
            expense=Decimal("0"),
            tax=Decimal("0"),
            counterparty_id=cp.id,
            note="alpha keep",
        )
        _create_transaction(
            tx_repo,
            date=datetime(2025, 1, 2, 10, 0, 0),
            income=Decimal("10"),
            expense=Decimal("0"),
            tax=Decimal("1"),
            note="alpha filtered-out",
        )

        result = use_case.execute(
            query="alpha",
            fields=["note"],
            skip=0,
            limit=10,
            no_tax=True,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 1, 23, 59, 59),
        )

        assert result.total_count == 1
        assert len(result.transactions) == 1
        assert result.transactions[0].note == "alpha keep"
        assert result.transactions[0].counterparty_name == "Search Partner"

    def test_statistics_avg_tax_and_filters(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        use_case = GetTransactionStatisticsUseCase(tx_repo)

        now = datetime.now()
        _create_transaction(
            tx_repo,
            date=now - timedelta(days=1),
            income=Decimal("100"),
            expense=Decimal("0"),
            tax=Decimal("10"),
            note="alpha",
        )
        _create_transaction(
            tx_repo,
            date=now,
            income=Decimal("50"),
            expense=Decimal("0"),
            tax=Decimal("0"),
            note="beta",
        )

        stats = use_case.execute()
        assert stats.avg_tax == Decimal("5")

        filter_dto = TransactionFilterDTO(has_tax=True)
        stats_with_tax = use_case.execute(filter_dto=filter_dto)
        assert stats_with_tax.total_transactions == 1
        assert stats_with_tax.avg_tax == Decimal("10")

        search_filter = TransactionFilterDTO(search_query="alpha")
        stats_search = use_case.execute(filter_dto=search_filter)
        assert stats_search.total_transactions == 1
        assert stats_search.avg_tax == Decimal("10")

    def test_statistics_filters_by_date_and_type(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        use_case = GetTransactionStatisticsUseCase(tx_repo)

        older_date = datetime(2024, 1, 1, 10, 0, 0)
        newer_date = datetime(2025, 1, 1, 10, 0, 0)
        _create_transaction(
            tx_repo,
            date=older_date,
            income=Decimal("100"),
            expense=Decimal("0"),
            tax=Decimal("0"),
            note="older-income",
        )
        _create_transaction(
            tx_repo,
            date=newer_date,
            income=Decimal("0"),
            expense=Decimal("50"),
            tax=Decimal("0"),
            note="newer-expense",
        )

        date_filter = TransactionFilterDTO(
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 1, 23, 59, 59),
        )
        stats_date = use_case.execute(filter_dto=date_filter)
        assert stats_date.total_transactions == 1
        assert stats_date.total_expense == Decimal("50")

        type_filter = TransactionFilterDTO(transaction_type=TransactionType.INCOME)
        stats_type = use_case.execute(filter_dto=type_filter)
        assert stats_type.total_transactions == 1
        assert stats_type.total_income == Decimal("100")

    def test_statistics_filters_has_tax_and_no_tax(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        use_case = GetTransactionStatisticsUseCase(tx_repo)

        _create_transaction(
            tx_repo,
            date=datetime.now(),
            income=Decimal("100"),
            expense=Decimal("0"),
            tax=Decimal("10"),
        )
        _create_transaction(
            tx_repo,
            date=datetime.now(),
            income=Decimal("50"),
            expense=Decimal("0"),
            tax=Decimal("0"),
        )

        stats_has_tax = use_case.execute(filter_dto=TransactionFilterDTO(has_tax=True))
        assert stats_has_tax.total_transactions == 1
        assert stats_has_tax.total_tax == Decimal("10")

        stats_no_tax = use_case.execute(filter_dto=TransactionFilterDTO(no_tax=True))
        assert stats_no_tax.total_transactions == 1
        assert stats_no_tax.total_tax == Decimal("0")

    def test_statistics_period_comparison_for_selected_range(self, session):
        tx_repo = SQLAlchemyTransactionRepository(session)
        use_case = GetTransactionStatisticsUseCase(tx_repo)

        _create_transaction(
            tx_repo,
            date=datetime(2025, 1, 24, 10, 0, 0),
            income=Decimal("80"),
            expense=Decimal("20"),
            tax=Decimal("5"),
        )
        _create_transaction(
            tx_repo,
            date=datetime(2025, 1, 30, 10, 0, 0),
            income=Decimal("0"),
            expense=Decimal("40"),
            tax=Decimal("0"),
        )

        _create_transaction(
            tx_repo,
            date=datetime(2025, 2, 2, 10, 0, 0),
            income=Decimal("100"),
            expense=Decimal("30"),
            tax=Decimal("10"),
        )
        _create_transaction(
            tx_repo,
            date=datetime(2025, 2, 8, 10, 0, 0),
            income=Decimal("50"),
            expense=Decimal("0"),
            tax=Decimal("0"),
        )

        stats = use_case.execute(
            filter_dto=TransactionFilterDTO(
                start_date=datetime(2025, 2, 1, 0, 0, 0),
                end_date=datetime(2025, 2, 10, 23, 59, 59),
            )
        )

        assert stats.period_comparison is not None
        assert stats.period_comparison.current_transactions == 2
        assert stats.period_comparison.previous_transactions == 2
        assert stats.period_comparison.current_income == Decimal("150")
        assert stats.period_comparison.previous_income == Decimal("80")
        assert stats.period_comparison.current_expense == Decimal("30")
        assert stats.period_comparison.previous_expense == Decimal("60")
        assert stats.period_comparison.current_tax == Decimal("10")
        assert stats.period_comparison.previous_tax == Decimal("5")
        assert stats.period_comparison.current_profit == Decimal("110")
        assert stats.period_comparison.previous_profit == Decimal("15")
        assert stats.period_comparison.income_delta == Decimal("70")
        assert stats.period_comparison.expense_delta == Decimal("-30")
        assert stats.period_comparison.tax_delta == Decimal("5")
        assert stats.period_comparison.profit_delta == Decimal("95")
