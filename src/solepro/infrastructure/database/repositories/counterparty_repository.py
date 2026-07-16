"""
Реализация репозитория контрагентов на SQLAlchemy.
"""
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import func, or_, desc, asc
from sqlalchemy.orm import Session, joinedload

from ....core.domain.entities.counterparty import Counterparty
from ....core.domain.exceptions.domain_exceptions import (
    EntityNotFoundException,
    DuplicateEntityException
)
from ....core.domain.repositories.counterparty_repository import CounterpartyRepository

from ..models import CounterpartyModel, TransactionModel


class SQLAlchemyCounterpartyRepository(CounterpartyRepository):
    """
    Реализация репозитория контрагентов на SQLAlchemy.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def _to_entity(self, model: CounterpartyModel) -> Counterparty:
        """Преобразовать SQLAlchemy модель в доменную сущность."""
        return Counterparty(
            id=UUID(str(model.id)),
            name=model.name,
            description=model.description,
            contact_info=model.contact_info,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    def _to_model(self, entity: Counterparty) -> CounterpartyModel:
        """Преобразовать доменную сущность в SQLAlchemy модель."""
        model = CounterpartyModel(
            id=str(entity.id),
            name=entity.name,
            description=entity.description,
            contact_info=entity.contact_info,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        
        return model
    
    def get_by_id(self, counterparty_id: UUID) -> Optional[Counterparty]:
        model = (
            self.session.query(CounterpartyModel)
            .filter(CounterpartyModel.id == str(counterparty_id))
            .first()
        )
        
        return self._to_entity(model) if model else None
    
    def get_by_name(self, name: str) -> Optional[Counterparty]:
        model = (
            self.session.query(CounterpartyModel)
            .filter(CounterpartyModel.name == name.strip())
            .first()
        )
        
        return self._to_entity(model) if model else None
    
    def save(self, counterparty: Counterparty) -> Counterparty:
        # Проверяем уникальность имени (кроме текущей сущности)
        if counterparty.name:
            existing = self.get_by_name(counterparty.name)
            if existing and existing.id != counterparty.id:
                raise DuplicateEntityException(
                    "Контрагент", "name", counterparty.name
                )
        
        # Проверяем, существует ли уже контрагент с таким ID
        existing = self.get_by_id(counterparty.id)
        
        if existing:
            # Обновляем существующего
            model = self._to_model(counterparty)
            model.id = str(counterparty.id)
            self.session.merge(model)
        else:
            # Создаем нового
            model = self._to_model(counterparty)
            self.session.add(model)
        
        self.session.flush()
        
        # Загружаем обновленную модель
        saved_model = (
            self.session.query(CounterpartyModel)
            .filter(CounterpartyModel.id == str(counterparty.id))
            .first()
        )
        
        return self._to_entity(saved_model)
    
    def delete(self, counterparty_id: UUID) -> bool:
        # Явно отвязываем транзакции (SET NULL), не полагаясь на FK-каскад БД:
        # существующие SQLite-базы могли быть созданы без ondelete-правила.
        (
            self.session.query(TransactionModel)
            .filter(TransactionModel.counterparty_id == str(counterparty_id))
            .update(
                {TransactionModel.counterparty_id: None},
                synchronize_session=False,
            )
        )
        result = (
            self.session.query(CounterpartyModel)
            .filter(CounterpartyModel.id == str(counterparty_id))
            .delete()
        )
        self.session.flush()
        return result > 0

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
    
    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "name_asc"
    ) -> List[Counterparty]:
        # Определяем порядок сортировки
        order_mapping = {
            "name_asc": asc(CounterpartyModel.name),
            "name_desc": desc(CounterpartyModel.name),
            "created_desc": desc(CounterpartyModel.created_at),
            "created_asc": asc(CounterpartyModel.created_at),
            "transaction_count_desc": desc(
                func.count(TransactionModel.id)
            ),
        }
        
        order = order_mapping.get(order_by, asc(CounterpartyModel.name))
        
        # Для сортировки по количеству транзакций нужен join
        if order_by == "transaction_count_desc":
            models = (
                self.session.query(
                    CounterpartyModel,
                    func.count(TransactionModel.id).label("transaction_count")
                )
                .outerjoin(TransactionModel)
                .group_by(CounterpartyModel.id)
                .order_by(order)
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [self._to_entity(model[0]) for model in models]
        else:
            models = (
                self.session.query(CounterpartyModel)
                .order_by(order)
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [self._to_entity(model) for model in models]
    
    def search(
        self,
        query: str,
        fields: List[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Counterparty]:
        if not query:
            return self.find_all(skip=skip, limit=limit)
        
        # Если fields не указаны, ищем во всех полях
        if fields is None:
            fields = ["name", "description", "contact_info"]
        
        # Строим условия поиска
        conditions = []
        search_pattern = f"%{query}%"
        
        if "name" in fields:
            conditions.append(CounterpartyModel.name.ilike(search_pattern))
        
        if "description" in fields:
            conditions.append(CounterpartyModel.description.ilike(search_pattern))
        
        if "contact_info" in fields:
            conditions.append(CounterpartyModel.contact_info.ilike(search_pattern))
        
        if not conditions:
            return []
        
        models = (
            self.session.query(CounterpartyModel)
            .filter(or_(*conditions))
            .order_by(asc(CounterpartyModel.name))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [self._to_entity(model) for model in models]
    
    def get_statistics(self) -> Dict[str, Any]:
        # Общее количество контрагентов
        total_count = self.session.query(func.count(CounterpartyModel.id)).scalar()
        
        # Количество контрагентов с транзакциями
        with_transactions = (
            self.session.query(func.count(func.distinct(TransactionModel.counterparty_id)))
            .scalar()
        )
        
        # Количество контрагентов без транзакций
        without_transactions = total_count - with_transactions
        
        # Среднее количество транзакций на контрагента
        avg_transactions = None
        if total_count > 0:
            total_transactions = self.session.query(func.count(TransactionModel.id)).scalar()
            avg_transactions = total_transactions / total_count if total_count > 0 else 0
        
        total_income_col = func.coalesce(func.sum(TransactionModel.income), 0).label("total_income")
        total_expense_col = func.coalesce(func.sum(TransactionModel.expense), 0).label("total_expense")
        total_tax_col = func.coalesce(func.sum(TransactionModel.tax), 0).label("total_tax")
        transaction_count_col = func.count(TransactionModel.id).label("transaction_count")

        total_income_sum = self.session.query(
            func.coalesce(func.sum(TransactionModel.income), 0)
        ).scalar() or 0

        totals_query = (
            self.session.query(
                CounterpartyModel.id,
                CounterpartyModel.name,
                transaction_count_col,
                total_income_col,
                total_expense_col,
                total_tax_col,
            )
            .outerjoin(TransactionModel)
            .group_by(CounterpartyModel.id, CounterpartyModel.name)
            .order_by(desc(total_income_col))
        )

        top_counterparties = []
        total_income_sum = Decimal(str(total_income_sum or 0))
        for row in totals_query.all():
            if row.transaction_count == 0:
                continue
            # Денежные суммы держим в Decimal до самого DTO — без прохода
            # через float (единообразно с остальными денежными расчетами).
            income = Decimal(str(row.total_income or 0))
            expense = Decimal(str(row.total_expense or 0))
            tax = Decimal(str(row.total_tax or 0))
            total_profit = income - expense - tax
            percentage = (
                float(income / total_income_sum * 100)
                if total_income_sum else 0.0
            )
            top_counterparties.append(
                {
                    "counterparty_id": str(row.id),
                    "counterparty_name": row.name,
                    "transaction_count": int(row.transaction_count),
                    "total_income": income,
                    "total_expense": expense,
                    "total_tax": tax,
                    "total_profit": total_profit,
                    "percentage_of_total": percentage,
                }
            )
        
        return {
            "total_count": total_count,
            "with_transactions": with_transactions,
            "without_transactions": without_transactions,
            "avg_transactions_per_counterparty": avg_transactions,
            "top_counterparties": top_counterparties,
        }

    def get_transaction_aggregates(
        self,
        counterparty_ids: List[UUID]
    ) -> Dict[UUID, Dict[str, Any]]:
        if not counterparty_ids:
            return {}

        ids = [str(counterparty_id) for counterparty_id in counterparty_ids]
        rows = (
            self.session.query(
                TransactionModel.counterparty_id,
                func.count(TransactionModel.id).label("transaction_count"),
                func.coalesce(func.sum(TransactionModel.income), 0).label("total_income"),
            )
            .filter(TransactionModel.counterparty_id.in_(ids))
            .group_by(TransactionModel.counterparty_id)
            .all()
        )

        aggregates: Dict[UUID, Dict[str, Any]] = {}
        for row in rows:
            if not row.counterparty_id:
                continue
            counterparty_id = UUID(str(row.counterparty_id))
            aggregates[counterparty_id] = {
                "transaction_count": int(row.transaction_count or 0),
                "total_income": Decimal(str(row.total_income or 0)),
            }

        return aggregates
    
    def count(self) -> int:
        return self.session.query(func.count(CounterpartyModel.id)).scalar()
    
    def exists(self, counterparty_id: UUID) -> bool:
        count = (
            self.session.query(func.count(CounterpartyModel.id))
            .filter(CounterpartyModel.id == str(counterparty_id))
            .scalar()
        )
        
        return count > 0
    
    def exists_by_name(self, name: str) -> bool:
        count = (
            self.session.query(func.count(CounterpartyModel.id))
            .filter(CounterpartyModel.name == name.strip())
            .scalar()
        )
        
        return count > 0
