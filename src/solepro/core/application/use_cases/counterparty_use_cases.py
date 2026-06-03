"""
Use Cases для работы с контрагентами.
"""
from typing import Optional, List, Dict, Any
from decimal import Decimal
from uuid import UUID

from ....core.domain.entities.counterparty import Counterparty
from ....core.domain.exceptions.domain_exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
)
from ....core.domain.repositories.counterparty_repository import CounterpartyRepository
from ....core.domain.repositories.transaction_repository import TransactionRepository
from ..unit_of_work import RepositoryUnitOfWork, UnitOfWork
from ..specifications import TransactionFilterSpecification
from ..mappers import (
    to_counterparty_response_dto,
    to_counterparty_statistics_dto,
)

from ..dto.counterparty_dto import (
    CounterpartyCreateDTO,
    CounterpartyUpdateDTO,
    CounterpartyResponseDTO,
    CounterpartyListDTO,
    CounterpartyFilterDTO,
)
from ..dto.transaction_dto import TransactionFilterDTO
from ..dto.statistics_dto import CounterpartyStatisticsDTO


def _get_counterparty_repository(uow: UnitOfWork) -> CounterpartyRepository:
    if uow.counterparties is None:
        raise RuntimeError("Counterparty repository is not configured in UnitOfWork")
    return uow.counterparties


class AddCounterpartyUseCase:
    """Use Case для добавления нового контрагента."""

    def __init__(
        self,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            counterparty_repository=counterparty_repository,
        )

    def execute(self, dto: CounterpartyCreateDTO) -> CounterpartyResponseDTO:
        with self.unit_of_work as uow:
            result = self._execute_impl(_get_counterparty_repository(uow), dto)
            uow.commit()
            return result

    def _execute_impl(
        self,
        counterparty_repository: CounterpartyRepository,
        dto: CounterpartyCreateDTO,
    ) -> CounterpartyResponseDTO:
        """
        Добавить нового контрагента.

        Args:
            dto: Данные для создания контрагента

        Returns:
            Созданный контрагент

        Raises:
            DuplicateEntityException: Если контрагент с таким именем уже существует
        """
        # Проверяем уникальность имени
        if counterparty_repository.exists_by_name(dto.name):
            raise DuplicateEntityException("Контрагент", "name", dto.name)

        # Создаем доменную сущность
        counterparty = Counterparty(
            name=dto.name,
            description=dto.description,
            contact_info=dto.contact_info,
        )

        # Сохраняем контрагента
        saved_counterparty = counterparty_repository.save(counterparty)

        # Преобразуем в DTO
        return to_counterparty_response_dto(saved_counterparty)


class UpdateCounterpartyUseCase:
    """Use Case для обновления контрагента."""

    def __init__(
        self,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            counterparty_repository=counterparty_repository,
        )

    def execute(
        self,
        counterparty_id: UUID,
        dto: CounterpartyUpdateDTO
    ) -> CounterpartyResponseDTO:
        with self.unit_of_work as uow:
            repository = _get_counterparty_repository(uow)
            result = self._execute_impl(repository, counterparty_id, dto)
            uow.commit()
            return result

    def _execute_impl(
        self,
        counterparty_repository: CounterpartyRepository,
        counterparty_id: UUID,
        dto: CounterpartyUpdateDTO
    ) -> CounterpartyResponseDTO:
        """
        Обновить контрагента.

        Args:
            counterparty_id: ID контрагента
            dto: Данные для обновления

        Returns:
            Обновленный контрагент

        Raises:
            EntityNotFoundException: Если контрагент не найден
            DuplicateEntityException: Если новое имя уже используется другим контрагентом
        """
        # Получаем существующего контрагента
        counterparty = counterparty_repository.get_by_id(counterparty_id)
        if not counterparty:
            raise EntityNotFoundException("Контрагент", str(counterparty_id))

        # Проверяем уникальность нового имени (если оно меняется)
        if dto.name is not None and dto.name != counterparty.name:
            if counterparty_repository.exists_by_name(dto.name):
                raise DuplicateEntityException("Контрагент", "name", dto.name)

        # Подготавливаем данные для обновления
        update_data = {}

        if dto.name is not None:
            update_data["name"] = dto.name

        if dto.description is not None:
            update_data["description"] = dto.description

        if dto.contact_info is not None:
            update_data["contact_info"] = dto.contact_info


        # Создаем обновленную сущность
        updated_counterparty = counterparty.update(**update_data)

        # Сохраняем
        saved_counterparty = counterparty_repository.save(updated_counterparty)

        aggregates = counterparty_repository.get_transaction_aggregates(
            [saved_counterparty.id]
        )
        aggregate = aggregates.get(saved_counterparty.id, {})

        # Преобразуем в DTO
        return to_counterparty_response_dto(
            saved_counterparty,
            aggregate=aggregate,
        )


class DeleteCounterpartyUseCase:
    """Use Case для удаления контрагента."""

    def __init__(
        self,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            counterparty_repository=counterparty_repository,
        )

    def execute(self, counterparty_id: UUID) -> bool:
        with self.unit_of_work as uow:
            result = self._execute_impl(_get_counterparty_repository(uow), counterparty_id)
            uow.commit()
            return result

    def _execute_impl(
        self,
        counterparty_repository: CounterpartyRepository,
        counterparty_id: UUID,
    ) -> bool:
        """
        Удалить контрагента.

        Args:
            counterparty_id: ID контрагента

        Returns:
            True если удалено, False если не найдено
        """
        return counterparty_repository.delete(counterparty_id)


class GetCounterpartyUseCase:
    """Use Case для получения контрагента по ID."""

    def __init__(
        self,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            counterparty_repository=counterparty_repository,
        )

    def execute(self, counterparty_id: UUID) -> Optional[CounterpartyResponseDTO]:
        """
        Получить контрагента по ID.

        Args:
            counterparty_id: ID контрагента

        Returns:
            Контрагент или None если не найден
        """
        with self.unit_of_work as uow:
            counterparty_repository = _get_counterparty_repository(uow)
            counterparty = counterparty_repository.get_by_id(counterparty_id)
            if not counterparty:
                return None

            aggregates = counterparty_repository.get_transaction_aggregates(
                [counterparty.id]
            )
            aggregate = aggregates.get(counterparty.id, {})

            return to_counterparty_response_dto(
                counterparty,
                aggregate=aggregate,
            )


class ListCounterpartiesUseCase:
    """Use Case для получения списка контрагентов."""

    def __init__(
        self,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            counterparty_repository=counterparty_repository,
        )

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "name_asc"
    ) -> CounterpartyListDTO:
        """
        Получить список контрагентов.

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            order_by: Поле и направление сортировки

        Returns:
            Список контрагентов с пагинацией
        """
        with self.unit_of_work as uow:
            counterparty_repository = _get_counterparty_repository(uow)
            counterparties = counterparty_repository.find_all(
                skip=skip,
                limit=limit,
                order_by=order_by
            )
            total_count = counterparty_repository.count()
            aggregates = counterparty_repository.get_transaction_aggregates(
                [counterparty.id for counterparty in counterparties]
            )

            counterparty_dtos = []
            for counterparty in counterparties:
                aggregate = aggregates.get(counterparty.id, {})
                counterparty_dtos.append(
                    to_counterparty_response_dto(
                        counterparty,
                        aggregate=aggregate,
                    )
                )

            total_pages = (total_count + limit - 1) // limit if limit > 0 else 0
            page = (skip // limit) + 1 if limit > 0 else 1

            return CounterpartyListDTO(
                counterparties=counterparty_dtos,
                total_count=total_count,
                page=page,
                page_size=limit,
                total_pages=total_pages,
            )


class SearchCounterpartiesUseCase:
    """Use Case для поиска контрагентов."""

    def __init__(
        self,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            counterparty_repository=counterparty_repository,
        )

    def execute(
        self,
        query: str,
        fields: List[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> CounterpartyListDTO:
        """
        Поиск контрагентов по тексту.

        Args:
            query: Текст для поиска
            fields: Поля для поиска
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список найденных контрагентов
        """
        with self.unit_of_work as uow:
            counterparty_repository = _get_counterparty_repository(uow)
            search_limit = counterparty_repository.count()
            all_counterparties = counterparty_repository.search(
                query=query,
                fields=fields,
                skip=0,
                limit=search_limit
            )
            total_count = len(all_counterparties)
            counterparties = all_counterparties[skip: skip + limit]
            aggregates = counterparty_repository.get_transaction_aggregates(
                [counterparty.id for counterparty in counterparties]
            )

            counterparty_dtos = []
            for counterparty in counterparties:
                aggregate = aggregates.get(counterparty.id, {})
                counterparty_dtos.append(
                    to_counterparty_response_dto(
                        counterparty,
                        aggregate=aggregate,
                    )
                )

            return CounterpartyListDTO(
                counterparties=counterparty_dtos,
                total_count=total_count,
                page=(skip // limit) + 1 if limit > 0 else 1,
                page_size=limit,
                total_pages=(total_count + limit - 1) // limit if limit > 0 else 0,
            )


class GetCounterpartyStatisticsUseCase:
    """Use Case для получения статистики по контрагентам."""

    def __init__(
        self,
        counterparty_repository: Optional[CounterpartyRepository] = None,
        transaction_repository: Optional[TransactionRepository] = None,
        unit_of_work: Optional[UnitOfWork] = None,
    ):
        self.unit_of_work = unit_of_work or RepositoryUnitOfWork(
            transaction_repository=transaction_repository,
            counterparty_repository=counterparty_repository,
        )

    def execute(
        self,
        filter_dto: Optional[TransactionFilterDTO] = None
    ) -> List[CounterpartyStatisticsDTO]:
        """
        Получить статистику по контрагентам.

        Returns:
            Статистика по контрагентам
        """
        with self.unit_of_work as uow:
            counterparty_repository = _get_counterparty_repository(uow)
            transaction_repository = uow.transactions

            if (
                filter_dto is None
                or filter_dto.show_all
                or transaction_repository is None
            ):
                raw_statistics = counterparty_repository.get_statistics()
                top_counterparties = raw_statistics.get("top_counterparties", [])
                return self._to_dto_list(top_counterparties)

            specification = TransactionFilterSpecification.from_filter_dto(filter_dto)

            records: Dict[UUID, Dict[str, Any]] = {}
            counterparty_name_cache: Dict[UUID, str] = {}
            offset = 0
            batch_size = 500

            while True:
                if filter_dto.search_query:
                    views = transaction_repository.search_with_counterparty(
                        query=filter_dto.search_query,
                        fields=["note", "counterparty.name"],
                        skip=offset,
                        limit=batch_size
                    )
                else:
                    views = transaction_repository.find_all_with_counterparty(
                        skip=offset,
                        limit=batch_size,
                        order_by="date_desc"
                    )

                if not views:
                    break

                for view in views:
                    transaction = view.transaction
                    if not specification.is_satisfied_by(transaction):
                        continue
                    if not transaction.counterparty_id:
                        continue

                    counterparty_id = transaction.counterparty_id
                    if counterparty_id not in records:
                        records[counterparty_id] = {
                            "transaction_count": 0,
                            "total_income": Decimal("0"),
                            "total_expense": Decimal("0"),
                            "total_tax": Decimal("0"),
                        }
                    records[counterparty_id]["transaction_count"] += 1
                    records[counterparty_id]["total_income"] += transaction.income.to_decimal()
                    records[counterparty_id]["total_expense"] += transaction.expense.to_decimal()
                    records[counterparty_id]["total_tax"] += transaction.tax.to_decimal()

                    if counterparty_id not in counterparty_name_cache:
                        counterparty_name_cache[counterparty_id] = (
                            view.counterparty_name or str(counterparty_id)
                        )

                offset += len(views)
                if len(views) < batch_size:
                    break

            total_income_sum = sum(
                (item["total_income"] for item in records.values()),
                Decimal("0")
            )

            raw_top_counterparties = []
            for counterparty_id, values in records.items():
                income = values["total_income"]
                expense = values["total_expense"]
                tax = values["total_tax"]
                profit = income - expense - tax
                percentage = float(income / total_income_sum * 100) if total_income_sum > 0 else 0.0

                raw_top_counterparties.append(
                    {
                        "counterparty_id": str(counterparty_id),
                        "counterparty_name": counterparty_name_cache.get(counterparty_id, str(counterparty_id)),
                        "transaction_count": int(values["transaction_count"]),
                        "total_income": income,
                        "total_expense": expense,
                        "total_tax": tax,
                        "total_profit": profit,
                        "percentage_of_total": percentage,
                    }
                )

            raw_top_counterparties.sort(
                key=lambda item: Decimal(str(item.get("total_income", 0))),
                reverse=True
            )
            return self._to_dto_list(raw_top_counterparties)

    @staticmethod
    def _to_dto_list(raw_items: List[Dict[str, Any]]) -> List[CounterpartyStatisticsDTO]:
        result: List[CounterpartyStatisticsDTO] = []
        for item in raw_items:
            result.append(to_counterparty_statistics_dto(item))
        return result
