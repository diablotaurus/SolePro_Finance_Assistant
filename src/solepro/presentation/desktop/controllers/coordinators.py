"""Coordinator classes for desktop controller responsibilities."""

from __future__ import annotations

from typing import List, Optional, Protocol
from uuid import UUID

from ....core.application.dto.counterparty_dto import (
    CounterpartyCreateDTO,
    CounterpartyListDTO,
    CounterpartyResponseDTO,
    CounterpartyUpdateDTO,
)
from ....core.application.dto.statistics_dto import CounterpartyStatisticsDTO, StatisticsDTO
from ....core.application.dto.transaction_dto import (
    TransactionCreateDTO,
    TransactionFilterDTO,
    TransactionListDTO,
    TransactionResponseDTO,
    TransactionUpdateDTO,
)
from ....core.application.use_cases.counterparty_use_cases import (
    AddCounterpartyUseCase,
    DeleteCounterpartyUseCase,
    GetCounterpartyStatisticsUseCase,
    ListCounterpartiesUseCase,
    SearchCounterpartiesUseCase,
    UpdateCounterpartyUseCase,
)
from ....core.application.use_cases.transaction_use_cases import (
    AddTransactionUseCase,
    DeleteTransactionUseCase,
    GetTransactionStatisticsUseCase,
    GetTransactionUseCase,
    ListTransactionsUseCase,
    SearchTransactionsUseCase,
    UpdateTransactionUseCase,
)

class TransactionCoordinatorProtocol(Protocol):
    """Contract for transaction coordinator behavior used by controller."""

    def load_transactions(
        self,
        filter_dto: Optional[TransactionFilterDTO] = None,
    ) -> TransactionListDTO: ...

    def load_statistics(self) -> StatisticsDTO: ...

    def add_transaction(self, dto: TransactionCreateDTO) -> TransactionResponseDTO: ...

    def update_transaction(
        self, transaction_id: UUID, dto: TransactionUpdateDTO
    ) -> TransactionResponseDTO: ...

    def delete_transaction(self, transaction_id: UUID) -> bool: ...

    def get_transaction(self, transaction_id: UUID) -> Optional[TransactionResponseDTO]: ...

    def get_transaction_statistics(
        self, filter_dto: Optional[TransactionFilterDTO] = None
    ) -> Optional[StatisticsDTO]: ...


class CounterpartyCoordinatorProtocol(Protocol):
    """Contract for counterparty coordinator behavior used by controller."""

    def load_counterparties(
        self,
        page: int = 1,
        page_size: int = 100,
        search_query: Optional[str] = None,
    ) -> CounterpartyListDTO: ...

    def add_counterparty(self, dto: CounterpartyCreateDTO) -> Optional[CounterpartyResponseDTO]: ...

    def update_counterparty(
        self, counterparty_id: UUID, dto: CounterpartyUpdateDTO
    ) -> Optional[CounterpartyResponseDTO]: ...

    def delete_counterparty(self, counterparty_id: UUID) -> bool: ...

    def get_counterparty_statistics(
        self, filter_dto: Optional[TransactionFilterDTO] = None
    ) -> List[CounterpartyStatisticsDTO]: ...


class TransactionCoordinator:
    """Coordinates transaction operations for desktop flows."""

    def __init__(
        self,
        add_transaction_use_case: AddTransactionUseCase,
        update_transaction_use_case: UpdateTransactionUseCase,
        delete_transaction_use_case: DeleteTransactionUseCase,
        get_transaction_use_case: GetTransactionUseCase,
        list_transactions_use_case: ListTransactionsUseCase,
        search_transactions_use_case: SearchTransactionsUseCase,
        get_transaction_statistics_use_case: GetTransactionStatisticsUseCase,
    ):
        self.add_transaction_use_case = add_transaction_use_case
        self.update_transaction_use_case = update_transaction_use_case
        self.delete_transaction_use_case = delete_transaction_use_case
        self.get_transaction_use_case = get_transaction_use_case
        self.list_transactions_use_case = list_transactions_use_case
        self.search_transactions_use_case = search_transactions_use_case
        self.get_transaction_statistics_use_case = get_transaction_statistics_use_case

    def load_transactions(
        self,
        filter_dto: Optional[TransactionFilterDTO] = None,
    ) -> TransactionListDTO:
        if filter_dto and filter_dto.show_all:
            return self.list_transactions_use_case.execute(
                skip=(filter_dto.page - 1) * filter_dto.page_size,
                limit=filter_dto.page_size,
                order_by=filter_dto.order_by,
            )

        if filter_dto and filter_dto.search_query:
            return self.search_transactions_use_case.execute(
                query=filter_dto.search_query,
                fields=["note", "counterparty.name"],
                skip=(filter_dto.page - 1) * filter_dto.page_size,
                limit=filter_dto.page_size,
                start_date=filter_dto.start_date,
                end_date=filter_dto.end_date,
                transaction_type=filter_dto.transaction_type,
                has_tax=filter_dto.has_tax,
                no_tax=filter_dto.no_tax,
                min_amount=filter_dto.min_amount,
                max_amount=filter_dto.max_amount,
            )

        return self.list_transactions_use_case.execute(
            skip=(filter_dto.page - 1) * filter_dto.page_size if filter_dto else 0,
            limit=filter_dto.page_size if filter_dto else 100,
            order_by=filter_dto.order_by if filter_dto else "date_desc",
            start_date=filter_dto.start_date if filter_dto else None,
            end_date=filter_dto.end_date if filter_dto else None,
            transaction_type=filter_dto.transaction_type if filter_dto else None,
            has_tax=filter_dto.has_tax if filter_dto else None,
            no_tax=filter_dto.no_tax if filter_dto else None,
            min_amount=filter_dto.min_amount if filter_dto else None,
            max_amount=filter_dto.max_amount if filter_dto else None,
        )

    def load_statistics(self) -> StatisticsDTO:
        return self.get_transaction_statistics_use_case.execute()

    def add_transaction(self, dto: TransactionCreateDTO) -> TransactionResponseDTO:
        return self.add_transaction_use_case.execute(dto)

    def update_transaction(
        self, transaction_id: UUID, dto: TransactionUpdateDTO
    ) -> TransactionResponseDTO:
        return self.update_transaction_use_case.execute(transaction_id, dto)

    def delete_transaction(self, transaction_id: UUID) -> bool:
        return self.delete_transaction_use_case.execute(transaction_id)

    def get_transaction(self, transaction_id: UUID) -> Optional[TransactionResponseDTO]:
        return self.get_transaction_use_case.execute(transaction_id)

    def get_transaction_statistics(
        self, filter_dto: Optional[TransactionFilterDTO] = None
    ) -> Optional[StatisticsDTO]:
        return self.get_transaction_statistics_use_case.execute(filter_dto=filter_dto)


class CounterpartyCoordinator:
    """Coordinates counterparty operations for desktop flows."""

    def __init__(
        self,
        add_counterparty_use_case: AddCounterpartyUseCase,
        update_counterparty_use_case: UpdateCounterpartyUseCase,
        delete_counterparty_use_case: DeleteCounterpartyUseCase,
        list_counterparties_use_case: ListCounterpartiesUseCase,
        search_counterparties_use_case: SearchCounterpartiesUseCase,
        get_counterparty_statistics_use_case: GetCounterpartyStatisticsUseCase,
    ):
        self.add_counterparty_use_case = add_counterparty_use_case
        self.update_counterparty_use_case = update_counterparty_use_case
        self.delete_counterparty_use_case = delete_counterparty_use_case
        self.list_counterparties_use_case = list_counterparties_use_case
        self.search_counterparties_use_case = search_counterparties_use_case
        self.get_counterparty_statistics_use_case = get_counterparty_statistics_use_case

    def load_counterparties(
        self,
        page: int = 1,
        page_size: int = 100,
        search_query: Optional[str] = None,
    ) -> CounterpartyListDTO:
        if search_query:
            return self.search_counterparties_use_case.execute(
                query=search_query,
                skip=(page - 1) * page_size,
                limit=page_size,
            )
        return self.list_counterparties_use_case.execute(
            skip=(page - 1) * page_size,
            limit=page_size,
        )

    def add_counterparty(self, dto: CounterpartyCreateDTO) -> Optional[CounterpartyResponseDTO]:
        return self.add_counterparty_use_case.execute(dto)

    def update_counterparty(
        self, counterparty_id: UUID, dto: CounterpartyUpdateDTO
    ) -> Optional[CounterpartyResponseDTO]:
        return self.update_counterparty_use_case.execute(counterparty_id, dto)

    def delete_counterparty(self, counterparty_id: UUID) -> bool:
        return self.delete_counterparty_use_case.execute(counterparty_id)

    def get_counterparty_statistics(
        self, filter_dto: Optional[TransactionFilterDTO] = None
    ) -> List[CounterpartyStatisticsDTO]:
        return self.get_counterparty_statistics_use_case.execute(filter_dto=filter_dto)
