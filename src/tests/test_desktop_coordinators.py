"""Tests for desktop coordinators."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from solepro.core.application.dto.counterparty_dto import CounterpartyListDTO
from solepro.core.application.dto.statistics_dto import StatisticsDTO
from solepro.core.application.dto.transaction_dto import (
    TransactionFilterDTO,
    TransactionListDTO,
    TransactionResponseDTO,
)
from solepro.presentation.desktop.controllers.coordinators import (
    CounterpartyCoordinator,
    TransactionCoordinator,
)


class _UseCase:
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def execute(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result


def _tx() -> TransactionResponseDTO:
    now = datetime.now()
    return TransactionResponseDTO(
        id=uuid4(),
        date=now,
        income=Decimal("100"),
        expense=Decimal("20"),
        tax=Decimal("5"),
        profit=Decimal("75"),
        counterparty_id=None,
        counterparty_name=None,
        note="n",
        created_at=now,
        updated_at=now,
    )


def test_transaction_coordinator_load_transactions_show_all_uses_list():
    list_uc = _UseCase(result=TransactionListDTO(transactions=[_tx()], total_count=1))
    search_uc = _UseCase(result=TransactionListDTO(transactions=[]))
    coordinator = TransactionCoordinator(
        add_transaction_use_case=_UseCase(),
        update_transaction_use_case=_UseCase(),
        delete_transaction_use_case=_UseCase(),
        get_transaction_use_case=_UseCase(),
        list_transactions_use_case=list_uc,
        search_transactions_use_case=search_uc,
        get_transaction_statistics_use_case=_UseCase(result=StatisticsDTO()),
    )

    result = coordinator.load_transactions(
        TransactionFilterDTO(show_all=True, page=2, page_size=10, order_by="date_desc")
    )

    assert len(search_uc.calls) == 0
    assert len(list_uc.calls) == 1
    _, kwargs = list_uc.calls[0]
    assert kwargs["skip"] == 10
    assert kwargs["limit"] == 10
    assert result.total_count == 1


def test_transaction_coordinator_load_transactions_search_uses_search():
    list_uc = _UseCase(result=TransactionListDTO(transactions=[]))
    search_uc = _UseCase(result=TransactionListDTO(transactions=[_tx()], total_count=1))
    coordinator = TransactionCoordinator(
        add_transaction_use_case=_UseCase(),
        update_transaction_use_case=_UseCase(),
        delete_transaction_use_case=_UseCase(),
        get_transaction_use_case=_UseCase(),
        list_transactions_use_case=list_uc,
        search_transactions_use_case=search_uc,
        get_transaction_statistics_use_case=_UseCase(result=StatisticsDTO()),
    )

    result = coordinator.load_transactions(
        TransactionFilterDTO(search_query="abc", page=1, page_size=20)
    )

    assert len(list_uc.calls) == 0
    assert len(search_uc.calls) == 1
    _, kwargs = search_uc.calls[0]
    assert kwargs["query"] == "abc"
    assert kwargs["fields"] == ["note", "counterparty.name"]
    assert result.total_count == 1


def test_transaction_coordinator_load_transactions_default_without_filter():
    list_uc = _UseCase(result=TransactionListDTO(transactions=[]))
    coordinator = TransactionCoordinator(
        add_transaction_use_case=_UseCase(),
        update_transaction_use_case=_UseCase(),
        delete_transaction_use_case=_UseCase(),
        get_transaction_use_case=_UseCase(),
        list_transactions_use_case=list_uc,
        search_transactions_use_case=_UseCase(result=TransactionListDTO(transactions=[])),
        get_transaction_statistics_use_case=_UseCase(result=StatisticsDTO()),
    )

    coordinator.load_transactions()

    assert len(list_uc.calls) == 1
    _, kwargs = list_uc.calls[0]
    assert kwargs["skip"] == 0
    assert kwargs["limit"] == 100
    assert kwargs["order_by"] == "date_desc"


def test_counterparty_coordinator_load_counterparties_search_branch():
    list_uc = _UseCase(result=CounterpartyListDTO())
    search_uc = _UseCase(result=CounterpartyListDTO())
    coordinator = CounterpartyCoordinator(
        add_counterparty_use_case=_UseCase(),
        update_counterparty_use_case=_UseCase(),
        delete_counterparty_use_case=_UseCase(result=True),
        list_counterparties_use_case=list_uc,
        search_counterparties_use_case=search_uc,
        get_counterparty_statistics_use_case=_UseCase(result=[]),
    )

    coordinator.load_counterparties(page=3, page_size=25, search_query="shoe")

    assert len(list_uc.calls) == 0
    assert len(search_uc.calls) == 1
    _, kwargs = search_uc.calls[0]
    assert kwargs["query"] == "shoe"
    assert kwargs["skip"] == 50
    assert kwargs["limit"] == 25


def test_counterparty_coordinator_get_statistics_passes_filter():
    stats_uc = _UseCase(result=[])
    coordinator = CounterpartyCoordinator(
        add_counterparty_use_case=_UseCase(),
        update_counterparty_use_case=_UseCase(),
        delete_counterparty_use_case=_UseCase(result=True),
        list_counterparties_use_case=_UseCase(result=CounterpartyListDTO()),
        search_counterparties_use_case=_UseCase(result=CounterpartyListDTO()),
        get_counterparty_statistics_use_case=stats_uc,
    )
    filter_dto = TransactionFilterDTO(search_query="nike")

    coordinator.get_counterparty_statistics(filter_dto=filter_dto)

    assert len(stats_uc.calls) == 1
    _, kwargs = stats_uc.calls[0]
    assert kwargs["filter_dto"] == filter_dto


def test_transaction_coordinator_crud_and_stats_delegate():
    add_uc = _UseCase(result="added")
    update_uc = _UseCase(result="updated")
    delete_uc = _UseCase(result=True)
    get_uc = _UseCase(result=_tx())
    stats_result = StatisticsDTO(total_transactions=7)
    stats_uc = _UseCase(result=stats_result)
    coordinator = TransactionCoordinator(
        add_transaction_use_case=add_uc,
        update_transaction_use_case=update_uc,
        delete_transaction_use_case=delete_uc,
        get_transaction_use_case=get_uc,
        list_transactions_use_case=_UseCase(result=TransactionListDTO(transactions=[])),
        search_transactions_use_case=_UseCase(result=TransactionListDTO(transactions=[])),
        get_transaction_statistics_use_case=stats_uc,
    )
    tx_id = uuid4()
    create_dto = object()
    update_dto = object()
    filter_dto = TransactionFilterDTO(search_query="stats")

    add_result = coordinator.add_transaction(create_dto)
    update_result = coordinator.update_transaction(tx_id, update_dto)
    delete_result = coordinator.delete_transaction(tx_id)
    get_result = coordinator.get_transaction(tx_id)
    get_stats_result = coordinator.get_transaction_statistics(filter_dto=filter_dto)

    assert add_result == "added"
    assert update_result == "updated"
    assert delete_result is True
    assert get_result is not None
    assert get_stats_result == stats_result
    assert add_uc.calls[0][0] == (create_dto,)
    assert update_uc.calls[0][0] == (tx_id, update_dto)
    assert delete_uc.calls[0][0] == (tx_id,)
    assert get_uc.calls[0][0] == (tx_id,)
    assert stats_uc.calls[0][1]["filter_dto"] == filter_dto


def test_counterparty_coordinator_crud_delegate():
    add_uc = _UseCase(result="cp-added")
    update_uc = _UseCase(result="cp-updated")
    delete_uc = _UseCase(result=True)
    coordinator = CounterpartyCoordinator(
        add_counterparty_use_case=add_uc,
        update_counterparty_use_case=update_uc,
        delete_counterparty_use_case=delete_uc,
        list_counterparties_use_case=_UseCase(result=CounterpartyListDTO()),
        search_counterparties_use_case=_UseCase(result=CounterpartyListDTO()),
        get_counterparty_statistics_use_case=_UseCase(result=[]),
    )
    cp_id = uuid4()
    create_dto = object()
    update_dto = object()

    add_result = coordinator.add_counterparty(create_dto)
    update_result = coordinator.update_counterparty(cp_id, update_dto)
    delete_result = coordinator.delete_counterparty(cp_id)

    assert add_result == "cp-added"
    assert update_result == "cp-updated"
    assert delete_result is True
    assert add_uc.calls[0][0] == (create_dto,)
    assert update_uc.calls[0][0] == (cp_id, update_dto)
    assert delete_uc.calls[0][0] == (cp_id,)
