"""Main desktop controller orchestrating UI workflows."""

from typing import Callable, List, Optional, TypeVar
from uuid import UUID

from PyQt6.QtCore import QObject, pyqtSignal

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
    TransactionResponseDTO,
    TransactionUpdateDTO,
)
from ..services.transaction_export_service import TransactionExportServiceProtocol
from .coordinators import CounterpartyCoordinatorProtocol, TransactionCoordinatorProtocol

T = TypeVar("T")


class MainController(QObject):
    """Desktop MVC controller."""

    # Signals
    data_loaded = pyqtSignal(list, dict)  # transactions, statistics
    transaction_added = pyqtSignal(TransactionResponseDTO)
    transaction_updated = pyqtSignal(TransactionResponseDTO)
    transaction_deleted = pyqtSignal(UUID)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        transaction_coordinator: TransactionCoordinatorProtocol,
        counterparty_coordinator: CounterpartyCoordinatorProtocol,
        transaction_export_service: TransactionExportServiceProtocol,
    ):
        super().__init__()

        self.transaction_export_service = transaction_export_service
        self.transaction_coordinator = transaction_coordinator
        self.counterparty_coordinator = counterparty_coordinator

        # Cached state
        self.current_transactions: List[TransactionResponseDTO] = []
        self.current_statistics: Optional[StatisticsDTO] = None
        self.current_filter: Optional[TransactionFilterDTO] = None

    def load_transactions(self, filter_dto: Optional[TransactionFilterDTO] = None) -> None:
        """Load transactions and emit updated data."""
        self._execute_with_error(
            action=lambda: self._load_transactions_impl(filter_dto),
            error_prefix="Ошибка загрузки транзакций",
            default_value=None,
        )

    def load_statistics(self) -> None:
        """Load statistics into current cache."""
        self._execute_with_error(
            action=self._load_statistics_impl,
            error_prefix="Ошибка загрузки статистики",
            default_value=None,
        )

    def add_transaction(self, dto: TransactionCreateDTO) -> None:
        """Create transaction and refresh data."""
        self._execute_with_error(
            action=lambda: self._add_transaction_impl(dto),
            error_prefix="Ошибка добавления транзакции",
            default_value=None,
        )

    def update_transaction(self, transaction_id: UUID, dto: TransactionUpdateDTO) -> None:
        """Update transaction and refresh data."""
        self._execute_with_error(
            action=lambda: self._update_transaction_impl(transaction_id, dto),
            error_prefix="Ошибка обновления транзакции",
            default_value=None,
        )

    def delete_transaction(self, transaction_id: UUID) -> None:
        """Delete transaction and refresh data."""
        self._execute_with_error(
            action=lambda: self._delete_transaction_impl(transaction_id),
            error_prefix="Ошибка удаления транзакции",
            default_value=None,
        )

    def get_transaction(self, transaction_id: UUID) -> Optional[TransactionResponseDTO]:
        """Fetch single transaction by identifier."""
        return self._execute_with_error(
            action=lambda: self.transaction_coordinator.get_transaction(transaction_id),
            error_prefix="Ошибка получения транзакции",
            default_value=None,
        )

    def load_counterparties(
        self,
        page: int = 1,
        page_size: int = 100,
        search_query: Optional[str] = None,
    ) -> CounterpartyListDTO:
        """Load counterparties with paging and optional search."""
        return self._execute_with_error(
            action=lambda: self.counterparty_coordinator.load_counterparties(
                page=page,
                page_size=page_size,
                search_query=search_query,
            ),
            error_prefix="Ошибка загрузки контрагентов",
            default_value=CounterpartyListDTO(),
        )

    def add_counterparty(self, dto: CounterpartyCreateDTO) -> Optional[CounterpartyResponseDTO]:
        """Create counterparty."""
        return self._execute_with_error(
            action=lambda: self.counterparty_coordinator.add_counterparty(dto),
            error_prefix="Ошибка добавления контрагента",
            default_value=None,
        )

    def update_counterparty(
        self,
        counterparty_id: UUID,
        dto: CounterpartyUpdateDTO,
    ) -> Optional[CounterpartyResponseDTO]:
        """Update counterparty."""
        return self._execute_with_error(
            action=lambda: self.counterparty_coordinator.update_counterparty(counterparty_id, dto),
            error_prefix="Ошибка обновления контрагента",
            default_value=None,
        )

    def delete_counterparty(self, counterparty_id: UUID) -> bool:
        """Delete counterparty."""
        return self._execute_with_error(
            action=lambda: self.counterparty_coordinator.delete_counterparty(counterparty_id),
            error_prefix="Ошибка удаления контрагента",
            default_value=False,
        )

    def export_to_excel(self, filepath: str) -> bool:
        """Export cached transactions to an Excel file."""
        return self._execute_with_error(
            action=lambda: self._export_to_excel(filepath),
            error_prefix="Ошибка экспорта в Excel",
            default_value=False,
        )

    def _export_to_excel(self, filepath: str) -> bool:
        self.transaction_export_service.export_to_excel(
            transactions=self.current_transactions,
            filepath=filepath,
        )
        return True

    def get_transaction_statistics(
        self,
        filter_dto: Optional[TransactionFilterDTO] = None,
    ) -> Optional[StatisticsDTO]:
        """Get transaction statistics."""
        return self._execute_with_error(
            action=lambda: self.transaction_coordinator.get_transaction_statistics(filter_dto=filter_dto),
            error_prefix="Ошибка получения статистики",
            default_value=None,
        )

    def get_counterparty_statistics(
        self,
        filter_dto: Optional[TransactionFilterDTO] = None,
    ) -> List[CounterpartyStatisticsDTO]:
        """Get counterparty statistics."""
        return self._execute_with_error(
            action=lambda: self.counterparty_coordinator.get_counterparty_statistics(filter_dto=filter_dto),
            error_prefix="Ошибка получения статистики по контрагентам",
            default_value=[],
        )

    def refresh_data(self) -> None:
        """Refresh controller data."""
        self._reload_current_transactions()

    def _emit_data_loaded(self) -> None:
        """Emit current transaction list with cached statistics payload."""
        self.data_loaded.emit(
            self.current_transactions,
            self.current_statistics.model_dump() if self.current_statistics else {},
        )

    def _emit_error(self, message: str) -> None:
        """Emit controller error signal."""
        self.error_occurred.emit(message)

    def _load_transactions_impl(self, filter_dto: Optional[TransactionFilterDTO]) -> None:
        self.current_filter = filter_dto
        result = self.transaction_coordinator.load_transactions(filter_dto=filter_dto)
        self.current_transactions = result.transactions
        self.load_statistics()
        self._emit_data_loaded()

    def _load_statistics_impl(self) -> None:
        self.current_statistics = self.transaction_coordinator.load_statistics()

    def _add_transaction_impl(self, dto: TransactionCreateDTO) -> None:
        transaction = self.transaction_coordinator.add_transaction(dto)
        self.transaction_added.emit(transaction)
        self._reload_current_transactions()

    def _update_transaction_impl(self, transaction_id: UUID, dto: TransactionUpdateDTO) -> None:
        transaction = self.transaction_coordinator.update_transaction(transaction_id, dto)
        self.transaction_updated.emit(transaction)
        self._reload_current_transactions()

    def _delete_transaction_impl(self, transaction_id: UUID) -> None:
        success = self.transaction_coordinator.delete_transaction(transaction_id)
        if success:
            self.transaction_deleted.emit(transaction_id)
            self._reload_current_transactions()
        else:
            self._emit_error("Транзакция не найдена")

    def _execute_with_error(
        self,
        action: Callable[[], T],
        error_prefix: str,
        default_value: T,
    ) -> T:
        try:
            return action()
        except Exception as e:
            self._emit_error(f"{error_prefix}: {str(e)}")
            return default_value

    def _reload_current_transactions(self) -> None:
        """Reload transactions using current filter state."""
        self.load_transactions(self.current_filter)
