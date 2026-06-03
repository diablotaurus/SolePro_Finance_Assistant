"""
Тесты валидации DTO.
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from solepro.core.application.dto.counterparty_dto import CounterpartyCreateDTO
from solepro.core.application.dto.transaction_dto import TransactionCreateDTO


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

    def test_transaction_negative_amounts(self):
        now = datetime.now()
        with pytest.raises(ValueError):
            TransactionCreateDTO(date=now, income=Decimal("-1"))

        with pytest.raises(ValueError):
            TransactionCreateDTO(date=now, expense=Decimal("-1"))

        with pytest.raises(ValueError):
            TransactionCreateDTO(date=now, tax=Decimal("-1"))
