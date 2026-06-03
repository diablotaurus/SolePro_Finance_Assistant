"""
Use Cases для работы с транзакциями.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from ....core.domain.entities.transaction import Transaction
from ....core.domain.entities.counterparty import Counterparty
from ....core.domain.value_objects.money import Money
from ....core.domain.enums.transaction_type import TransactionType
from ....core.domain.exceptions.domain_exceptions import (
    EntityNotFoundException,
    InvalidTransactionException,
)
from ....core.domain.repositories.transaction_repository import TransactionRepository
from ....core.domain.repositories.counterparty_repository import CounterpartyRepository
from ..unit_of_work import RepositoryUnitOfWork, UnitOfWork
from ..mappers import to_transaction_response_dto
from ..specifications import TransactionFilterSpecification

from ..dto.transaction_dto import (
    TransactionCreateDTO,
    TransactionUpdateDTO,
    TransactionResponseDTO,
    TransactionListDTO,
    TransactionFilterDTO,
)
from ..dto.statistics_dto import StatisticsDTO, MonthlyStatisticsDTO, PeriodComparisonDTO


def _get_transaction_repository(uow: UnitOfWork) -> TransactionRepository:
    if uow.transactions is None:
        raise RuntimeError("Transaction repository is not configured in UnitOfWork")
    return uow.transactions


def _get_counterparty_repository(uow: UnitOfWork) -> CounterpartyRepository:
    if uow.counterparties is None:
        raise RuntimeError("Counterparty repository is not configured in UnitOfWork")
    return uow.counterparties


class AddTransactionUseCase:
    """Use Case для добавления новой транзакции."""

    def __init__(
        self,
        transaction_repository: Optional[TransactionRepository] = None,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            transaction_repository=transaction_repository,
            counterparty_repository=counterparty_repository,
        )

    def execute(self, dto: TransactionCreateDTO) -> TransactionResponseDTO:
        """
        Добавить новую транзакцию.

        Args:
            dto: Данные для создания транзакции

        Returns:
            Созданная транзакция

        Raises:
            EntityNotFoundException: Если контрагент не найден
            InvalidTransactionException: Если данные транзакции невалидны
        """
        with self.unit_of_work as uow:
            transaction_repository = _get_transaction_repository(uow)
            counterparty_repository = _get_counterparty_repository(uow)
            # Получаем или создаем контрагента
            counterparty_id = dto.counterparty_id

            if not counterparty_id and dto.counterparty_name:
                # Ищем контрагента по имени
                counterparty = counterparty_repository.get_by_name(dto.counterparty_name)
                if counterparty:
                    counterparty_id = counterparty.id
                else:
                    # Создаем нового контрагента
                    counterparty = Counterparty(
                        name=dto.counterparty_name
                    )
                    counterparty = counterparty_repository.save(counterparty)
                    counterparty_id = counterparty.id

            # Создаем доменную сущность
            transaction = Transaction(
                date=dto.date,
                income=Money.from_string(str(dto.income)),
                expense=Money.from_string(str(dto.expense)),
                tax=Money.from_string(str(dto.tax)),
                counterparty_id=counterparty_id,
                note=dto.note or "",
            )

            # Сохраняем транзакцию
            saved_transaction = transaction_repository.save(transaction)

            # Получаем имя контрагента для ответа
            counterparty_name = None
            if saved_transaction.counterparty_id:
                counterparty = counterparty_repository.get_by_id(saved_transaction.counterparty_id)
                if counterparty:
                    counterparty_name = counterparty.name

            uow.commit()

            # Преобразуем в DTO
            return to_transaction_response_dto(
                saved_transaction,
                counterparty_name=counterparty_name,
            )


class UpdateTransactionUseCase:
    """Use Case для обновления транзакции."""

    def __init__(
        self,
        transaction_repository: Optional[TransactionRepository] = None,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            transaction_repository=transaction_repository,
            counterparty_repository=counterparty_repository,
        )

    def execute(
        self,
        transaction_id: UUID,
        dto: TransactionUpdateDTO
    ) -> TransactionResponseDTO:
        """
        Обновить транзакцию.

        Args:
            transaction_id: ID транзакции
            dto: Данные для обновления

        Returns:
            Обновленная транзакция

        Raises:
            EntityNotFoundException: Если транзакция или контрагент не найдены
        """
        with self.unit_of_work as uow:
            transaction_repository = _get_transaction_repository(uow)
            counterparty_repository = _get_counterparty_repository(uow)
            # Получаем существующую транзакцию
            transaction = transaction_repository.get_by_id(transaction_id)
            if not transaction:
                raise EntityNotFoundException("Транзакция", str(transaction_id))

            # Подготавливаем данные для обновления
            update_data = {}

            if dto.date is not None:
                update_data["date"] = dto.date

            if dto.income is not None:
                update_data["income"] = Money.from_string(str(dto.income))

            if dto.expense is not None:
                update_data["expense"] = Money.from_string(str(dto.expense))

            if dto.tax is not None:
                update_data["tax"] = Money.from_string(str(dto.tax))

            if dto.note is not None:
                update_data["note"] = dto.note

            if dto.counterparty_id is not None:
                # Проверяем существование контрагента
                counterparty = counterparty_repository.get_by_id(dto.counterparty_id)
                if not counterparty:
                    raise EntityNotFoundException("Контрагент", str(dto.counterparty_id))
                update_data["counterparty_id"] = dto.counterparty_id

            # Создаем обновленную сущность
            updated_transaction = transaction.update(**update_data)

            # Сохраняем
            saved_transaction = transaction_repository.save(updated_transaction)

            # Получаем имя контрагента для ответа
            counterparty_name = None
            if saved_transaction.counterparty_id:
                counterparty = counterparty_repository.get_by_id(saved_transaction.counterparty_id)
                if counterparty:
                    counterparty_name = counterparty.name

            uow.commit()

            # Преобразуем в DTO
            return to_transaction_response_dto(
                saved_transaction,
                counterparty_name=counterparty_name,
            )


class DeleteTransactionUseCase:
    """Use Case для удаления транзакции."""

    def __init__(
        self,
        transaction_repository: Optional[TransactionRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            transaction_repository=transaction_repository,
        )

    def execute(self, transaction_id: UUID) -> bool:
        """
        Удалить транзакцию.

        Args:
            transaction_id: ID транзакции

        Returns:
            True если удалено, False если не найдено
        """
        with self.unit_of_work as uow:
            transaction_repository = _get_transaction_repository(uow)
            result = transaction_repository.delete(transaction_id)
            uow.commit()
            return result


class GetTransactionUseCase:
    """Use Case для получения транзакции по ID."""

    def __init__(
        self,
        transaction_repository: Optional[TransactionRepository] = None,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            transaction_repository=transaction_repository,
            counterparty_repository=counterparty_repository,
        )

    def execute(self, transaction_id: UUID) -> Optional[TransactionResponseDTO]:
        """
        Получить транзакцию по ID.

        Args:
            transaction_id: ID транзакции

        Returns:
            Транзакция или None если не найдена
        """
        with self.unit_of_work as uow:
            transaction_repository = _get_transaction_repository(uow)

            view = transaction_repository.get_by_id_with_counterparty(transaction_id)
            if not view:
                return None

            return to_transaction_response_dto(
                view.transaction,
                counterparty_name=view.counterparty_name,
            )


class ListTransactionsUseCase:
    """Use Case для получения списка транзакций."""

    def __init__(
        self,
        transaction_repository: Optional[TransactionRepository] = None,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            transaction_repository=transaction_repository,
            counterparty_repository=counterparty_repository,
        )

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "date_desc",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[TransactionType] = None,
        has_tax: Optional[bool] = None,
        no_tax: Optional[bool] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None
    ) -> TransactionListDTO:
        """
        Получить список транзакций.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            order_by: Поле и направление сортировки

        Returns:
            Список транзакций с пагинацией
        """
        use_filters = any([
            start_date,
            end_date,
            transaction_type,
            has_tax,
            no_tax,
            min_amount is not None,
            max_amount is not None
        ])
        total_count = 0

        # Преобразуем в DTO
        transaction_dtos = []

        specification = TransactionFilterSpecification(
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type,
            has_tax=has_tax,
            no_tax=no_tax,
            min_amount=min_amount,
            max_amount=max_amount,
        )

        with self.unit_of_work as uow:
            transaction_repository = _get_transaction_repository(uow)

            if use_filters:
                offset = 0
                batch_size = max(limit, 500)
                while True:
                    views = transaction_repository.find_all_with_counterparty(
                        skip=offset,
                        limit=batch_size,
                        order_by=order_by
                    )
                    if not views:
                        break

                    for view in views:
                        transaction = view.transaction
                        if not specification.is_satisfied_by(transaction):
                            continue

                        if total_count >= skip and len(transaction_dtos) < limit:
                            transaction_dtos.append(
                                to_transaction_response_dto(
                                    transaction,
                                    counterparty_name=view.counterparty_name,
                                )
                            )
                        total_count += 1

                    offset += len(views)
                    if len(views) < batch_size:
                        break
            else:
                views = transaction_repository.find_all_with_counterparty(
                    skip=skip,
                    limit=limit,
                    order_by=order_by
                )
                total_count = transaction_repository.count()
                for view in views:
                    transaction_dtos.append(
                        to_transaction_response_dto(
                            view.transaction,
                            counterparty_name=view.counterparty_name,
                        )
                    )

        # Рассчитываем пагинацию
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 0
        page = (skip // limit) + 1 if limit > 0 else 1

        return TransactionListDTO(
            transactions=transaction_dtos,
            total_count=total_count,
            page=page,
            page_size=limit,
            total_pages=total_pages,
        )


class SearchTransactionsUseCase:
    """Use Case для поиска транзакций."""

    def __init__(
        self,
        transaction_repository: Optional[TransactionRepository] = None,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            transaction_repository=transaction_repository,
            counterparty_repository=counterparty_repository,
        )

    def execute(
        self,
        query: str,
        fields: List[str] = None,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[TransactionType] = None,
        has_tax: Optional[bool] = None,
        no_tax: Optional[bool] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None
    ) -> TransactionListDTO:
        """
        Поиск транзакций по тексту.

        Args:
            query: Текст для поиска
            fields: Поля для поиска
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список найденных транзакций
        """
        # Выполняем поиск
        total_count = 0
        offset = 0
        batch_size = max(limit, 500)

        # Преобразуем в DTO
        transaction_dtos = []

        specification = TransactionFilterSpecification(
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type,
            has_tax=has_tax,
            no_tax=no_tax,
            min_amount=min_amount,
            max_amount=max_amount,
        )

        with self.unit_of_work as uow:
            transaction_repository = _get_transaction_repository(uow)

            while True:
                views = transaction_repository.search_with_counterparty(
                    query=query,
                    fields=fields,
                    skip=offset,
                    limit=batch_size
                )
                if not views:
                    break

                for view in views:
                    transaction = view.transaction
                    if not specification.is_satisfied_by(transaction):
                        continue

                    if total_count >= skip and len(transaction_dtos) < limit:
                        transaction_dtos.append(
                            to_transaction_response_dto(
                                transaction,
                                counterparty_name=view.counterparty_name,
                            )
                        )
                    total_count += 1

                offset += len(views)
                if len(views) < batch_size:
                    break

        return TransactionListDTO(
            transactions=transaction_dtos,
            total_count=total_count,
            page=(skip // limit) + 1 if limit > 0 else 1,
            page_size=limit,
            total_pages=(total_count + limit - 1) // limit if limit > 0 else 0,
        )


class GetTransactionStatisticsUseCase:
    """Use Case для получения статистики по транзакциям."""

    def __init__(
        self,
        transaction_repository: Optional[TransactionRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            transaction_repository=transaction_repository,
        )

    @staticmethod
    def _previous_period(
        start_dt: datetime, end_dt: datetime
    ) -> tuple[datetime, datetime]:
        """Вычислить границы предыдущего периода той же длительности."""
        period_delta = end_dt - start_dt
        previous_end = start_dt - timedelta(microseconds=1)
        previous_start = previous_end - period_delta
        return previous_start, previous_end

    @classmethod
    def _statistics_load_window(
        cls,
        start_dt: Optional[datetime],
        end_dt: Optional[datetime],
    ) -> tuple[datetime, datetime]:
        """
        Определить диапазон дат для загрузки из БД.

        Если задан полноценный период (обе границы), включаем и предыдущий
        период — он нужен для сравнения периодов. Отсутствующая граница
        заменяется на минимально/максимально возможную дату.
        """
        if start_dt and end_dt and start_dt <= end_dt:
            previous_start, _ = cls._previous_period(start_dt, end_dt)
            load_start = previous_start
        else:
            load_start = start_dt if start_dt is not None else datetime.min
        load_end = end_dt if end_dt is not None else datetime.max
        return load_start, load_end

    @staticmethod
    def _load_transactions_in_range(
        transaction_repository: TransactionRepository,
        start_dt: datetime,
        end_dt: datetime,
    ) -> List[Transaction]:
        """Загрузить все транзакции в диапазоне дат постранично."""
        results: List[Transaction] = []
        offset = 0
        batch_size = 1000
        while True:
            batch = transaction_repository.find_by_date_range(
                start_date=start_dt,
                end_date=end_dt,
                skip=offset,
                limit=batch_size,
            )
            if not batch:
                break
            results.extend(batch)
            offset += len(batch)
            if len(batch) < batch_size:
                break
        return results

    def _build_period_comparison(
        self,
        *,
        transactions: List[Transaction],
        specification: TransactionFilterSpecification,
    ) -> PeriodComparisonDTO:
        start_dt = specification.start_datetime
        end_dt = specification.end_datetime
        previous_start, previous_end = self._previous_period(start_dt, end_dt)

        previous_specification = specification.for_period(previous_start, previous_end)

        current_transactions = [
            tx for tx in transactions if specification.is_satisfied_by(tx)
        ]
        previous_transactions = [
            tx for tx in transactions if previous_specification.is_satisfied_by(tx)
        ]

        current_income = sum((tx.income.to_decimal() for tx in current_transactions), Decimal("0"))
        previous_income = sum((tx.income.to_decimal() for tx in previous_transactions), Decimal("0"))
        current_expense = sum((tx.expense.to_decimal() for tx in current_transactions), Decimal("0"))
        previous_expense = sum((tx.expense.to_decimal() for tx in previous_transactions), Decimal("0"))
        current_tax = sum((tx.tax.to_decimal() for tx in current_transactions), Decimal("0"))
        previous_tax = sum((tx.tax.to_decimal() for tx in previous_transactions), Decimal("0"))

        current_profit = current_income - current_expense - current_tax
        previous_profit = previous_income - previous_expense - previous_tax

        income_delta = current_income - previous_income
        expense_delta = current_expense - previous_expense
        tax_delta = current_tax - previous_tax
        profit_delta = current_profit - previous_profit

        current_count = len(current_transactions)
        previous_count = len(previous_transactions)
        transactions_delta = current_count - previous_count

        def percent_change(current_value, previous_value) -> Optional[float]:
            if previous_value == 0:
                return None
            return float((current_value - previous_value) / previous_value * Decimal("100"))

        return PeriodComparisonDTO(
            current_start=start_dt,
            current_end=end_dt,
            previous_start=previous_start,
            previous_end=previous_end,
            current_transactions=current_count,
            previous_transactions=previous_count,
            current_income=current_income,
            previous_income=previous_income,
            income_delta=income_delta,
            income_delta_percent=percent_change(current_income, previous_income),
            current_expense=current_expense,
            previous_expense=previous_expense,
            expense_delta=expense_delta,
            expense_delta_percent=percent_change(current_expense, previous_expense),
            current_tax=current_tax,
            previous_tax=previous_tax,
            tax_delta=tax_delta,
            tax_delta_percent=percent_change(current_tax, previous_tax),
            current_profit=current_profit,
            previous_profit=previous_profit,
            profit_delta=profit_delta,
            profit_delta_percent=percent_change(current_profit, previous_profit),
            transactions_delta=transactions_delta,
            transactions_delta_percent=percent_change(Decimal(current_count), Decimal(previous_count)),
        )

    def execute(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filter_dto: Optional[TransactionFilterDTO] = None,
    ) -> StatisticsDTO:
        """
        Get transaction statistics.

        Args:
            start_date: Start date.
            end_date: End date.

        Returns:
            Transaction statistics.
        """
        start_dt = start_date
        end_dt = end_date
        counterparty_id = None
        transaction_type = None
        has_tax = None
        no_tax = None
        min_amount = None
        max_amount = None
        search_query = None

        if filter_dto and not filter_dto.show_all:
            if filter_dto.start_date is not None:
                start_dt = filter_dto.start_date
            if filter_dto.end_date is not None:
                end_dt = filter_dto.end_date
            counterparty_id = filter_dto.counterparty_id
            transaction_type = filter_dto.transaction_type
            has_tax = filter_dto.has_tax
            no_tax = filter_dto.no_tax
            min_amount = filter_dto.min_amount
            max_amount = filter_dto.max_amount
            search_query = filter_dto.search_query

        specification = TransactionFilterSpecification(
            start_date=start_dt,
            end_date=end_dt,
            counterparty_id=counterparty_id,
            transaction_type=transaction_type,
            has_tax=has_tax,
            no_tax=no_tax,
            min_amount=min_amount,
            max_amount=max_amount,
        )

        with self.unit_of_work as uow:
            transaction_repository = _get_transaction_repository(uow)

            if search_query:
                transactions = transaction_repository.search(
                    query=search_query,
                    fields=["note", "counterparty.name"],
                    skip=0,
                    limit=100000,
                )
            else:
                norm_start = specification.start_datetime
                norm_end = specification.end_datetime
                if norm_start is not None or norm_end is not None:
                    # Грузим только нужный диапазон дат (а не всю таблицу).
                    load_start, load_end = self._statistics_load_window(norm_start, norm_end)
                    transactions = self._load_transactions_in_range(
                        transaction_repository, load_start, load_end
                    )
                else:
                    # Период не задан (показать всё) — поведение без изменений.
                    total_count = transaction_repository.count()
                    transactions = (
                        transaction_repository.find_all(
                            skip=0,
                            limit=total_count,
                            order_by="date_asc",
                        )
                        if total_count
                        else []
                    )

            filtered_transactions = [
                tx for tx in transactions if specification.is_satisfied_by(tx)
            ]

            monthly_map: Dict[tuple[int, int], Dict[str, Any]] = {}
            income_count = 0
            expense_count = 0
            mixed_count = 0

            for transaction in filtered_transactions:
                tx_type = transaction.get_transaction_type()
                if tx_type == TransactionType.INCOME:
                    income_count += 1
                elif tx_type == TransactionType.EXPENSE:
                    expense_count += 1
                elif tx_type == TransactionType.MIXED:
                    mixed_count += 1

                key = (transaction.date.year, transaction.date.month)
                if key not in monthly_map:
                    monthly_map[key] = {
                        "income": Decimal("0"),
                        "expense": Decimal("0"),
                        "tax": Decimal("0"),
                        "profit": Decimal("0"),
                        "count": 0,
                    }

                monthly_map[key]["income"] += transaction.income.to_decimal()
                monthly_map[key]["expense"] += transaction.expense.to_decimal()
                monthly_map[key]["tax"] += transaction.tax.to_decimal()
                monthly_map[key]["profit"] += transaction.calculate_profit().to_decimal()
                monthly_map[key]["count"] += 1

            monthly_statistics = [
                MonthlyStatisticsDTO(
                    year=year,
                    month=month,
                    income=stats["income"],
                    expense=stats["expense"],
                    tax=stats["tax"],
                    profit=stats["profit"],
                    transaction_count=stats["count"],
                )
                for (year, month), stats in sorted(monthly_map.items())
            ]

            total_transactions = len(filtered_transactions)
            total_income = sum((transaction.income.to_decimal() for transaction in filtered_transactions), Decimal("0"))
            total_expense = sum((transaction.expense.to_decimal() for transaction in filtered_transactions), Decimal("0"))
            total_tax = sum((transaction.tax.to_decimal() for transaction in filtered_transactions), Decimal("0"))
            total_profit = total_income - total_expense - total_tax

            avg_income = None
            avg_expense = None
            avg_tax = None
            avg_profit = None
            if total_transactions > 0:
                avg_income = total_income / total_transactions if total_income > 0 else Decimal("0")
                avg_expense = total_expense / total_transactions if total_expense > 0 else Decimal("0")
                avg_tax = total_tax / total_transactions if total_tax > 0 else Decimal("0")
                avg_profit = total_profit / total_transactions

            first_transaction_date = min((transaction.date for transaction in filtered_transactions), default=None)
            last_transaction_date = max((transaction.date for transaction in filtered_transactions), default=None)

            period_comparison = None
            if (
                specification.start_datetime
                and specification.end_datetime
                and specification.start_datetime <= specification.end_datetime
            ):
                period_comparison = self._build_period_comparison(
                    transactions=transactions,
                    specification=specification,
                )

            return StatisticsDTO(
                total_transactions=total_transactions,
                total_income=total_income,
                total_expense=total_expense,
                total_tax=total_tax,
                total_profit=total_profit,
                avg_income=avg_income,
                avg_expense=avg_expense,
                avg_tax=avg_tax,
                avg_profit=avg_profit,
                first_transaction_date=first_transaction_date,
                last_transaction_date=last_transaction_date,
                monthly_statistics=monthly_statistics,
                period_comparison=period_comparison,
                top_counterparties=[],
                income_transaction_count=income_count,
                expense_transaction_count=expense_count,
                mixed_transaction_count=mixed_count,
            )
