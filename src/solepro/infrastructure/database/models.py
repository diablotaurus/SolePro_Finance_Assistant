"""
SQLAlchemy модели для базы данных.
"""
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.types import CHAR, TypeDecorator

from ...core.domain.constants import (
    MAX_COUNTERPARTY_NAME_LENGTH,
    MAX_MONEY_AMOUNT,
    MONEY_QUANTUM,
)

Base = declarative_base()


class GUID(TypeDecorator):
    """Dialect-safe UUID type."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        if dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class CounterpartyModel(Base):
    """
    Модель контрагента для SQLAlchemy.
    """
    __tablename__ = "counterparties"

    # PostgreSQL использует UUID, SQLite - строки
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name = Column(String(MAX_COUNTERPARTY_NAME_LENGTH), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    contact_info = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Связи. Каскадного удаления НЕТ намеренно: при удалении контрагента его
    # транзакции (финансовые записи) должны сохраняться с counterparty_id=NULL,
    # что соответствует ondelete="SET NULL" внешнего ключа.
    transactions = relationship(
        "TransactionModel",
        back_populates="counterparty",
        passive_deletes=True,
        lazy="dynamic"
    )

    @validates("name")
    def validate_name(self, key: str, name: str) -> str:
        """Валидация имени контрагента."""
        if not name or not name.strip():
            raise ValueError("Имя контрагента не может быть пустым")
        if len(name.strip()) > MAX_COUNTERPARTY_NAME_LENGTH:
            raise ValueError(
                f"Имя контрагента не должно превышать "
                f"{MAX_COUNTERPARTY_NAME_LENGTH} символов"
            )
        return name.strip()

    def __repr__(self) -> str:
        return f"<CounterpartyModel(id={self.id}, name='{self.name}')>"


class TransactionModel(Base):
    """
    Модель транзакции для SQLAlchemy.
    """
    __tablename__ = "transactions"

    # PostgreSQL использует UUID, SQLite - строки
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    date = Column(DateTime, nullable=False, index=True)
    income = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    expense = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    tax = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Внешний ключ
    counterparty_id = Column(
        GUID(),
        ForeignKey("counterparties.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Связи
    counterparty = relationship(
        "CounterpartyModel",
        back_populates="transactions",
        lazy="joined"
    )

    # Вычисляемые поля (не хранятся в БД)
    @property
    def profit(self) -> Decimal:
        """Рассчитать прибыль."""
        return self.income - self.expense - self.tax

    @validates("income", "expense", "tax")
    def validate_amounts(self, key: str, value: Decimal) -> Decimal:
        """Валидация денежных сумм."""
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        if value < 0:
            raise ValueError(f"{key} не может быть отрицательным")
        if value > MAX_MONEY_AMOUNT:
            raise ValueError(f"{key} слишком большая сумма")
        return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)

    @validates("date")
    def validate_date(self, key: str, date: datetime) -> datetime:
        """Валидация даты."""
        if date > datetime.now():
            raise ValueError("Дата транзакции не может быть в будущем")
        return date

    def __repr__(self) -> str:
        return f"<TransactionModel(id={self.id}, date={self.date}, income={self.income})>"


# Создаем индексы для улучшения производительности
@event.listens_for(Base.metadata, "after_create")
def create_indexes(target, connection, **kw):
    """Создать дополнительные индексы после создания таблиц."""
    # Индекс для поиска по дате (часто используется)
    connection.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_transactions_date_desc "
        "ON transactions(date DESC)"
    ))
    
    # Индекс для поиска по контрагенту и дате
    connection.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_transactions_counterparty_date "
        "ON transactions(counterparty_id, date DESC)"
    ))
    
    # Индекс для поиска по сумме дохода (для статистики)
    connection.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_transactions_income "
        "ON transactions(income)"
    ))
    
    # Индекс для поиска по тегам контрагентов удален вместе с функциональностью тегов.
