"""
Тесты валидации DTO.
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from uuid import uuid4

from solepro.core.application.dto.counterparty_dto import CounterpartyCreateDTO
from solepro.core.application.dto.transaction_dto import (
    TransactionCreateDTO,
    TransactionResponseDTO,
)


class TestCounterpartyDTOValidation:
    def test_counterparty_name_required(self):
        with pytest.raises(ValueError):
            CounterpartyCreateDTO(name="")

    def test_counterparty_name_trim(self):
        dto = CounterpartyCreateDTO(name="  Контрагент  ")
        assert dto.name == "Контрагент"


class TestTransactionDTOValidation:
    def test_transaction_future_date(self):
        future = datetime.now() + timedelta(days=1)
        with pytest.raises(ValueError):
            TransactionCreateDTO(date=future)

    def test_response_dto_accepts_future_date(self):
        """Регрессия v1.4.20: response-DTO не валидирует бизнес-правила
        ввода — перевод системных часов назад не должен ломать чтение
        уже сохранённых транзакций."""
        now = datetime.now()
        dto = TransactionResponseDTO(
            id=uuid4(),
            date=now + timedelta(hours=3),  # «будущая» после перевода часов
            income=Decimal("100"),
            expense=Decimal("0"),
            tax=Decimal("0"),
            profit=Decimal("100"),
            created_at=now,
            updated_at=now,
        )
        assert dto.profit == Decimal("100")

    def test_transaction_negative_amounts(self):
        now = datetime.now()
        with pytest.raises(ValueError):
            TransactionCreateDTO(date=now, income=Decimal("-1"))

        with pytest.raises(ValueError):
            TransactionCreateDTO(date=now, expense=Decimal("-1"))

        with pytest.raises(ValueError):
            TransactionCreateDTO(date=now, tax=Decimal("-1"))
