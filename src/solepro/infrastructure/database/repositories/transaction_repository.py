"""
Реализация репозитория транзакций на SQLAlchemy.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.orm import Session, joinedload

from ....core.domain.entities.transaction import Transaction
from ....core.domain.value_objects.money import Money
from ....core.domain.enums.transaction_type import TransactionType
from ....core.domain.exceptions.domain_exceptions import EntityNotFoundException
from ....core.domain.repositories.transaction_repository import (
    TransactionRepository,
    TransactionView,
)

from ..models import TransactionModel, CounterpartyModel


class SQLAlchemyTransactionRepository(TransactionRepository):
    """
    Реализация репозитория транзакций на SQLAlchemy.
    """

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _as_decimal(value: Any) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    def _to_entity(self, model: TransactionModel) -> Transaction:
        """Преобразовать SQLAlchemy модель в доменную сущность."""
        counterparty_id = UUID(str(model.counterparty_id)) if model.counterparty_id else None

        return Transaction(
            id=UUID(str(model.id)),
            date=model.date,
            income=Money(value=self._as_decimal(model.income)),
            expense=Money(value=self._as_decimal(model.expense)),
            tax=Money(value=self._as_decimal(model.tax)),
            counterparty_id=counterparty_id,
            note=model.note or "",
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_view(self, model: TransactionModel) -> TransactionView:
        """
        Преобразовать модель в read-model с именем контрагента.

        Имя берётся из уже загруженной связи (lazy="joined"), поэтому
        дополнительных запросов к БД не выполняется.
        """
        counterparty_name = model.counterparty.name if model.counterparty else None
        return TransactionView(
            transaction=self._to_entity(model),
            counterparty_name=counterparty_name,
        )

    def _to_model(self, entity: Transaction) -> TransactionModel:
        """Преобразовать доменную сущность в SQLAlchemy модель."""
        model = TransactionModel(
            id=str(entity.id),
            date=entity.date,
            income=entity.income.to_decimal(),
            expense=entity.expense.to_decimal(),
            tax=entity.tax.to_decimal(),
            note=entity.note,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

        # Выставляем всегда (в т.ч. None): merge() копирует только явно
        # заданные атрибуты, иначе снятие контрагента не сохранялось бы.
        model.counterparty_id = (
            str(entity.counterparty_id) if entity.counterparty_id else None
        )

        return model

    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        model = self._query_by_id(transaction_id)
        return self._to_entity(model) if model else None

    def get_by_id_with_counterparty(
        self, transaction_id: UUID
    ) -> Optional[TransactionView]:
        model = self._query_by_id(transaction_id)
        return self._to_view(model) if model else None

    def _query_by_id(self, transaction_id: UUID) -> Optional[TransactionModel]:
        return (
            self.session.query(TransactionModel)
            .options(joinedload(TransactionModel.counterparty))
            .filter(TransactionModel.id == str(transaction_id))
            .first()
        )

    def save(self, transaction: Transaction) -> Transaction:
        # Проверяем существование контрагента
        if transaction.counterparty_id:
            counterparty = (
                self.session.query(CounterpartyModel)
                .filter(CounterpartyModel.id == str(transaction.counterparty_id))
                .first()
            )
            if not counterparty:
                raise EntityNotFoundException("Контрагент", str(transaction.counterparty_id))

        # Проверяем, существует ли уже транзакция с таким ID
        existing = self.get_by_id(transaction.id)

        if existing:
            # Обновляем существующую
            model = self._to_model(transaction)
            model.id = str(transaction.id)
            self.session.merge(model)
        else:
            # Создаем новую
            model = self._to_model(transaction)
            self.session.add(model)

        self.session.flush()

        # Загружаем с отношениями
        saved_model = (
            self.session.query(TransactionModel)
            .options(joinedload(TransactionModel.counterparty))
            .filter(TransactionModel.id == str(transaction.id))
            .first()
        )

        return self._to_entity(saved_model)

    def delete(self, transaction_id: UUID) -> bool:
        result = (
            self.session.query(TransactionModel)
            .filter(TransactionModel.id == str(transaction_id))
            .delete()
        )
        self.session.flush()
        return result > 0

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def _query_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "date_desc"
    ) -> List[TransactionModel]:
        """Построить запрос списка транзакций (общий для сущностей и read-моделей)."""
        # Определяем порядок сортировки
        order_mapping = {
            "date_desc": desc(TransactionModel.date),
            "date_asc": asc(TransactionModel.date),
            "income_desc": desc(TransactionModel.income),
            "income_asc": asc(TransactionModel.income),
            "created_desc": desc(TransactionModel.created_at),
            "created_asc": asc(TransactionModel.created_at),
        }

        order = order_mapping.get(order_by, desc(TransactionModel.date))

        return (
            self.session.query(TransactionModel)
            .options(joinedload(TransactionModel.counterparty))
            .order_by(order)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "date_desc"
    ) -> List[Transaction]:
        return [
            self._to_entity(model)
            for model in self._query_all(skip=skip, limit=limit, order_by=order_by)
        ]

    def find_all_with_counterparty(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "date_desc"
    ) -> List[TransactionView]:
        return [
            self._to_view(model)
            for model in self._query_all(skip=skip, limit=limit, order_by=order_by)
        ]

    def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        models = (
            self.session.query(TransactionModel)
            .options(joinedload(TransactionModel.counterparty))
            .filter(
                and_(
                    TransactionModel.date >= start_date,
                    TransactionModel.date <= end_date
                )
            )
            .order_by(desc(TransactionModel.date))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [self._to_entity(model) for model in models]

    def find_by_counterparty(
        self,
        counterparty_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        models = (
            self.session.query(TransactionModel)
            .options(joinedload(TransactionModel.counterparty))
            .filter(TransactionModel.counterparty_id == str(counterparty_id))
            .order_by(desc(TransactionModel.date))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [self._to_entity(model) for model in models]

    def find_by_type(
        self,
        transaction_type: TransactionType,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        # Определяем условия для каждого типа
        conditions = {
            TransactionType.INCOME: and_(
                TransactionModel.income > 0,
                TransactionModel.expense == 0
            ),
            TransactionType.EXPENSE: and_(
                TransactionModel.income == 0,
                TransactionModel.expense > 0
            ),
            TransactionType.MIXED: and_(
                TransactionModel.income > 0,
                TransactionModel.expense > 0
            ),
            TransactionType.NEUTRAL: and_(
                TransactionModel.income == 0,
                TransactionModel.expense == 0
            ),
        }

        condition = conditions.get(transaction_type)
        if condition is None:
            return []

        models = (
            self.session.query(TransactionModel)
            .options(joinedload(TransactionModel.counterparty))
            .filter(condition)
            .order_by(desc(TransactionModel.date))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [self._to_entity(model) for model in models]

    def _query_search(
        self,
        query: str,
        fields: List[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionModel]:
        """Построить запрос поиска транзакций (общий для сущностей и read-моделей)."""
        if not query:
            return self._query_all(skip=skip, limit=limit)

        # Если fields не указаны, ищем во всех полях
        if fields is None:
            fields = ["note", "counterparty.name"]

        # Строим условия поиска
        conditions = []
        search_pattern = f"%{query}%"

        if "note" in fields:
            conditions.append(TransactionModel.note.ilike(search_pattern))

        if "counterparty.name" in fields:
            conditions.append(CounterpartyModel.name.ilike(search_pattern))

        if not conditions:
            return []

        return (
            self.session.query(TransactionModel)
            .options(joinedload(TransactionModel.counterparty))
            .join(CounterpartyModel, isouter=True)
            .filter(or_(*conditions))
            .order_by(desc(TransactionModel.date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(
        self,
        query: str,
        fields: List[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        return [
            self._to_entity(model)
            for model in self._query_search(query, fields=fields, skip=skip, limit=limit)
        ]

    def search_with_counterparty(
        self,
        query: str,
        fields: List[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionView]:
        return [
            self._to_view(model)
            for model in self._query_search(query, fields=fields, skip=skip, limit=limit)
        ]

    def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        # Базовый запрос
        query = self.session.query(
            func.count(TransactionModel.id).label("count"),
            func.coalesce(func.sum(TransactionModel.income), 0).label("total_income"),
            func.coalesce(func.sum(TransactionModel.expense), 0).label("total_expense"),
            func.coalesce(func.sum(TransactionModel.tax), 0).label("total_tax"),
            func.min(TransactionModel.date).label("first_date"),
            func.max(TransactionModel.date).label("last_date"),
        )

        # Фильтрация по дате
        if start_date:
            query = query.filter(TransactionModel.date >= start_date)
        if end_date:
            query = query.filter(TransactionModel.date <= end_date)

        result = query.first()

        total_income = self._as_decimal(result.total_income)
        total_expense = self._as_decimal(result.total_expense)
        total_tax = self._as_decimal(result.total_tax)
        total_profit = total_income - total_expense - total_tax

        # Средние значения (только для транзакций с доходом/расходом)
        avg_income = None
        avg_expense = None
        avg_profit = None

        if result.count > 0:
            avg_income = total_income / result.count if total_income > 0 else Decimal("0")
            avg_expense = total_expense / result.count if total_expense > 0 else Decimal("0")
            avg_profit = total_profit / result.count

        return {
            "total_count": result.count,
            "total_income": total_income,
            "total_expense": total_expense,
            "total_tax": total_tax,
            "total_profit": total_profit,
            "avg_income": avg_income,
            "avg_expense": avg_expense,
            "avg_profit": avg_profit,
            "first_transaction_date": result.first_date,
            "last_transaction_date": result.last_date,
        }

    def get_monthly_summary(
        self,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        # Получаем статистику за конкретный месяц
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        return self.get_statistics(start_date=start_date, end_date=end_date)

    def get_total_income(self) -> Money:
        result = self.session.query(
            func.coalesce(func.sum(TransactionModel.income), 0)
        ).scalar()

        return Money(value=self._as_decimal(result))

    def get_total_expense(self) -> Money:
        result = self.session.query(
            func.coalesce(func.sum(TransactionModel.expense), 0)
        ).scalar()

        return Money(value=self._as_decimal(result))

    def get_total_tax(self) -> Money:
        result = self.session.query(
            func.coalesce(func.sum(TransactionModel.tax), 0)
        ).scalar()

        return Money(value=self._as_decimal(result))

    def get_total_profit(self) -> Money:
        income = self.get_total_income().to_decimal()
        expense = self.get_total_expense().to_decimal()
        tax = self.get_total_tax().to_decimal()

        return Money(value=income - expense - tax)

    def count(self) -> int:
        return self.session.query(func.count(TransactionModel.id)).scalar()

    def exists(self, transaction_id: UUID) -> bool:
        count = (
            self.session.query(func.count(TransactionModel.id))
            .filter(TransactionModel.id == str(transaction_id))
            .scalar()
        )

        return count > 0
