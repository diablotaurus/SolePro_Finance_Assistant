"""
Тесты для MainController.
"""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from solepro.core.application.dto.counterparty_dto import CounterpartyListDTO
from solepro.core.application.dto.statistics_dto import StatisticsDTO
from solepro.core.application.dto.transaction_dto import (
    TransactionCreateDTO,
    TransactionFilterDTO,
    TransactionListDTO,
    TransactionResponseDTO,
    TransactionUpdateDTO,
)
from solepro.presentation.desktop.controllers.coordinators import (
    CounterpartyCoordinator,
    TransactionCoordinator,
)
from solepro.presentation.desktop.controllers.main_controller import MainController


class _UseCase:
    def __init__(self, result=None, side_effect=None):
        self.result = result
        self.side_effect = side_effect
        self.calls = []

    def execute(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.side_effect:
            raise self.side_effect
        return self.result


class _ExportService:
    def __init__(self, side_effect=None):
        self.side_effect = side_effect
        self.calls = []

    def export_to_excel(self, transactions, filepath):
        self.calls.append((transactions, filepath))
        if self.side_effect:
            raise self.side_effect


class _TransactionCoordinatorStub:
    def __init__(self, list_result=None, stats_result=None):
        self.list_result = list_result or TransactionListDTO(transactions=[])
        self.stats_result = stats_result or StatisticsDTO()
        self.calls = {"load_transactions": 0}

    def load_transactions(self, filter_dto=None):
        self.calls["load_transactions"] += 1
        return self.list_result

    def load_statistics(self):
        return self.stats_result

    def add_transaction(self, dto):
        return None

    def update_transaction(self, transaction_id, dto):
        return None

    def delete_transaction(self, transaction_id):
        return False

    def get_transaction(self, transaction_id):
        return None

    def get_transaction_statistics(self, filter_dto=None):
        return self.stats_result


class _CounterpartyCoordinatorStub:
    def load_counterparties(self, page=1, page_size=100, search_query=None):
        return CounterpartyListDTO()

    def add_counterparty(self, dto):
        return None

    def update_counterparty(self, counterparty_id, dto):
        return None

    def delete_counterparty(self, counterparty_id):
        return False

    def get_counterparty_statistics(self, filter_dto=None):
        return []


def _tx(note="n1"):
    now = datetime.now()
    return TransactionResponseDTO(
        id=uuid4(),
        date=now,
        income=Decimal("100"),
        expense=Decimal("10"),
        tax=Decimal("5"),
        profit=Decimal("85"),
        counterparty_id=None,
        counterparty_name=None,
        note=note,
        created_at=now,
        updated_at=now,
    )


def _build_controller(
    *,
    list_result=None,
    search_result=None,
    stats_result=None,
    add_side_effect=None,
    delete_result=True,
    export_service=None,
):
    add_uc = _UseCase(side_effect=add_side_effect)
    update_uc = _UseCase()
    delete_uc = _UseCase(result=delete_result)
    get_uc = _UseCase()
    list_uc = _UseCase(result=list_result or TransactionListDTO(transactions=[]))
    search_uc = _UseCase(result=search_result or TransactionListDTO(transactions=[]))
    stats_uc = _UseCase(result=stats_result or StatisticsDTO())

    add_cp_uc = _UseCase()
    update_cp_uc = _UseCase()
    delete_cp_uc = _UseCase(result=True)
    list_cp_uc = _UseCase(result=CounterpartyListDTO())
    search_cp_uc = _UseCase(result=CounterpartyListDTO())
    cp_stats_uc = _UseCase(result=[])
    transaction_coordinator = TransactionCoordinator(
        add_transaction_use_case=add_uc,
        update_transaction_use_case=update_uc,
        delete_transaction_use_case=delete_uc,
        get_transaction_use_case=get_uc,
        list_transactions_use_case=list_uc,
        search_transactions_use_case=search_uc,
        get_transaction_statistics_use_case=stats_uc,
    )
    counterparty_coordinator = CounterpartyCoordinator(
        add_counterparty_use_case=add_cp_uc,
        update_counterparty_use_case=update_cp_uc,
        delete_counterparty_use_case=delete_cp_uc,
        list_counterparties_use_case=list_cp_uc,
        search_counterparties_use_case=search_cp_uc,
        get_counterparty_statistics_use_case=cp_stats_uc,
    )

    export_service = export_service or _ExportService()
    controller = MainController(
        transaction_coordinator=transaction_coordinator,
        counterparty_coordinator=counterparty_coordinator,
        transaction_export_service=export_service,
    )
    return controller, {
        "add": add_uc,
        "update": update_uc,
        "delete": delete_uc,
        "get": get_uc,
        "list": list_uc,
        "search": search_uc,
        "stats": stats_uc,
        "list_cp": list_cp_uc,
        "cp_stats": cp_stats_uc,
    }


def test_load_transactions_show_all_emits_data_loaded():
    tx_list = TransactionListDTO(transactions=[_tx("show-all")], total_count=1)
    stats = StatisticsDTO(total_transactions=1, total_income=Decimal("100"))
    controller, ucs = _build_controller(list_result=tx_list, stats_result=stats)

    captured = {"page": None, "stats": None, "period_stats": None}
    controller.data_loaded.connect(
        lambda page, statistics, period_statistics: captured.update(
            {"page": page, "stats": statistics, "period_stats": period_statistics}
        )
    )

    controller.load_transactions(TransactionFilterDTO(show_all=True, page=1, page_size=20))

    assert len(ucs["list"].calls) == 1
    assert len(ucs["search"].calls) == 0
    assert captured["page"] is not None
    assert len(captured["page"].transactions) == 1
    assert captured["page"].transactions[0].note == "show-all"
    assert captured["stats"].total_transactions == 1
    assert captured["period_stats"].total_transactions == 1


def test_load_transactions_search_branch_uses_search_use_case():
    tx_list = TransactionListDTO(transactions=[_tx("search-hit")], total_count=1)
    controller, ucs = _build_controller(search_result=tx_list)

    controller.load_transactions(TransactionFilterDTO(search_query="hit", page=1, page_size=10))

    assert len(ucs["search"].calls) == 1
    assert len(ucs["list"].calls) == 0


def test_add_transaction_error_emits_signal():
    controller, _ = _build_controller(add_side_effect=RuntimeError("add-failed"))
    captured = {"message": None}
    controller.error_occurred.connect(lambda message: captured.update({"message": message}))

    controller.add_transaction(
        TransactionCreateDTO(
            date=datetime.now(),
            income=Decimal("1"),
            expense=Decimal("0"),
            tax=Decimal("0"),
            note="x",
        )
    )

    assert captured["message"] is not None
    assert "add-failed" in captured["message"]


def test_add_transaction_success_emits_signal_and_reloads():
    tx_added = _tx("added")
    tx_reloaded = _tx("reloaded")
    tx_list = TransactionListDTO(transactions=[tx_reloaded], total_count=1)
    controller, ucs = _build_controller(list_result=tx_list)
    ucs["add"].result = tx_added
    captured = {"added": None}
    controller.transaction_added.connect(lambda value: captured.update({"added": value}))

    controller.add_transaction(
        TransactionCreateDTO(
            date=datetime.now(),
            income=Decimal("10"),
            expense=Decimal("1"),
            tax=Decimal("0"),
            note="ok",
        )
    )

    assert captured["added"] is tx_added
    assert len(ucs["add"].calls) == 1
    assert len(ucs["list"].calls) == 1
    assert controller.current_transactions[0].note == "reloaded"


def test_update_transaction_success_emits_signal_and_reloads():
    tx_updated = _tx("updated")
    tx_reloaded = _tx("after-update")
    tx_id = uuid4()
    tx_list = TransactionListDTO(transactions=[tx_reloaded], total_count=1)
    controller, ucs = _build_controller(list_result=tx_list)
    ucs["update"].result = tx_updated
    captured = {"updated": None}
    controller.transaction_updated.connect(lambda value: captured.update({"updated": value}))

    controller.update_transaction(
        tx_id,
        TransactionUpdateDTO(
            income=Decimal("20"),
            expense=Decimal("2"),
            tax=Decimal("1"),
            note="upd",
        ),
    )

    assert captured["updated"] is tx_updated
    assert len(ucs["update"].calls) == 1
    assert ucs["update"].calls[0][0][0] == tx_id
    assert len(ucs["list"].calls) == 1
    assert controller.current_transactions[0].note == "after-update"


def test_delete_transaction_false_emits_not_found_error():
    controller, _ = _build_controller(delete_result=False)
    captured = {"message": None}
    controller.error_occurred.connect(lambda message: captured.update({"message": message}))

    controller.delete_transaction(uuid4())

    assert captured["message"] is not None
    assert captured["message"].strip() != ""


def test_delete_transaction_success_emits_signal_and_reloads():
    tx_id = uuid4()
    tx_list = TransactionListDTO(transactions=[_tx("after-delete")], total_count=1)
    controller, ucs = _build_controller(list_result=tx_list, delete_result=True)
    captured = {"deleted": None}
    controller.transaction_deleted.connect(lambda value: captured.update({"deleted": value}))

    controller.delete_transaction(tx_id)

    assert captured["deleted"] == tx_id
    assert len(ucs["delete"].calls) == 1
    assert len(ucs["list"].calls) == 1
    assert controller.current_transactions[0].note == "after-delete"


def test_load_counterparties_error_returns_empty_list():
    controller, ucs = _build_controller()
    ucs["list_cp"].side_effect = RuntimeError("cp-down")
    captured = {"message": None}
    controller.error_occurred.connect(lambda message: captured.update({"message": message}))

    result = controller.load_counterparties()

    assert result.counterparties == []
    assert captured["message"] is not None
    assert "cp-down" in captured["message"]


def test_get_transaction_error_returns_none_and_emits_signal():
    controller, ucs = _build_controller()
    ucs["get"].side_effect = RuntimeError("get-failed")
    captured = {"message": None}
    controller.error_occurred.connect(lambda message: captured.update({"message": message}))

    result = controller.get_transaction(uuid4())

    assert result is None
    assert captured["message"] is not None
    assert "get-failed" in captured["message"]


def test_load_statistics_error_emits_signal():
    controller, ucs = _build_controller()
    ucs["stats"].side_effect = RuntimeError("stats-down")
    captured = {"message": None}
    controller.error_occurred.connect(lambda message: captured.update({"message": message}))

    controller.load_statistics()

    assert captured["message"] is not None
    assert "stats-down" in captured["message"]


def test_get_counterparty_statistics_passes_filter():
    controller, ucs = _build_controller()
    filter_dto = TransactionFilterDTO(search_query="abc")

    controller.get_counterparty_statistics(filter_dto=filter_dto)

    assert len(ucs["cp_stats"].calls) == 1
    args, kwargs = ucs["cp_stats"].calls[0]
    assert args == ()
    assert kwargs["filter_dto"] == filter_dto


def test_refresh_data_uses_current_filter():
    tx_list = TransactionListDTO(transactions=[_tx("refresh-hit")], total_count=1)
    controller, ucs = _build_controller(search_result=tx_list)
    controller.current_filter = TransactionFilterDTO(search_query="refresh", page=1, page_size=10)

    controller.refresh_data()

    assert len(ucs["search"].calls) == 1
    _, kwargs = ucs["search"].calls[0]
    assert kwargs["query"] == "refresh"
    assert controller.current_transactions[0].note == "refresh-hit"


def test_export_to_excel_delegates_to_service():
    export_service = _ExportService()
    export_page = TransactionListDTO(
        transactions=[_tx("exp")], total_count=1, page=1, page_size=1000, total_pages=1
    )
    controller, _ = _build_controller(list_result=export_page, export_service=export_service)
    controller.current_filter = TransactionFilterDTO(show_all=True)

    success = controller.export_to_excel("report.xlsx")

    assert success is True
    assert len(export_service.calls) == 1
    transactions, filepath = export_service.calls[0]
    assert len(transactions) == 1
    assert transactions[0].note == "exp"
    assert filepath == "report.xlsx"


def test_export_to_excel_loads_every_filtered_page():
    export_service = _ExportService()
    first = [_tx(f"page-1-{index}") for index in range(1000)]
    second = [_tx("page-2")]

    class _PagedCoordinator(_TransactionCoordinatorStub):
        def load_transactions(self, filter_dto=None):
            return TransactionListDTO(
                transactions=first if filter_dto.page == 1 else second,
                total_count=1001,
                page=filter_dto.page,
                page_size=1000,
                total_pages=2,
            )

    controller = MainController(
        transaction_coordinator=_PagedCoordinator(),
        counterparty_coordinator=_CounterpartyCoordinatorStub(),
        transaction_export_service=export_service,
    )
    controller.current_filter = TransactionFilterDTO(search_query="invoice")

    assert controller.export_to_excel("all.xlsx") is True
    assert len(export_service.calls[0][0]) == 1001


def test_export_to_excel_emits_error_on_service_failure():
    export_service = _ExportService(side_effect=RuntimeError("excel-failed"))
    controller, _ = _build_controller(export_service=export_service)
    captured = {"message": None}
    controller.error_occurred.connect(lambda message: captured.update({"message": message}))

    success = controller.export_to_excel("report.xlsx")

    assert success is False
    assert captured["message"] is not None
    assert "excel-failed" in captured["message"]


def test_controller_uses_injected_transaction_coordinator():
    tx_list = TransactionListDTO(transactions=[_tx("injected")], total_count=1)
    tx_coordinator = _TransactionCoordinatorStub(list_result=tx_list)
    cp_coordinator = _CounterpartyCoordinatorStub()
    controller = MainController(
        transaction_coordinator=tx_coordinator,
        counterparty_coordinator=cp_coordinator,
        transaction_export_service=_ExportService(),
    )

    controller.load_transactions()

    assert tx_coordinator.calls["load_transactions"] == 1
    assert len(controller.current_transactions) == 1
    assert controller.current_transactions[0].note == "injected"
