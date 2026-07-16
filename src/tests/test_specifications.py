"""
Тесты TransactionFilterSpecification: нормализация границ периода.

Регрессия v1.4.19: date-пикеры отдают дату без времени, pydantic приводит её
к datetime полуночи, из-за чего конечная граница отсекала транзакции
с ненулевым временем (например, добавленные ботом через «сегодня»).
"""
from datetime import date, datetime, time
from decimal import Decimal

from solepro.core.application.dto.transaction_dto import TransactionFilterDTO
from solepro.core.application.specifications import TransactionFilterSpecification
from solepro.core.domain.entities.transaction import Transaction
from solepro.core.domain.value_objects.money import Money


def _tx(dt: datetime) -> Transaction:
    return Transaction(date=dt, income=Money(Decimal("100")))


class TestEndDateNormalization:
    def test_end_datetime_at_midnight_covers_whole_day(self):
        spec = TransactionFilterSpecification(
            end_date=datetime(2024, 7, 10)  # полночь — как после pydantic-коэрции
        )
        assert spec.is_satisfied_by(_tx(datetime(2024, 7, 10, 14, 30))) is True
        assert spec.is_satisfied_by(_tx(datetime(2024, 7, 10, 23, 59, 59))) is True
        assert spec.is_satisfied_by(_tx(datetime(2024, 7, 11, 0, 30))) is False

    def test_end_datetime_with_explicit_time_is_preserved(self):
        spec = TransactionFilterSpecification(
            end_date=datetime(2024, 7, 10, 12, 0)
        )
        assert spec.is_satisfied_by(_tx(datetime(2024, 7, 10, 11, 0))) is True
        assert spec.is_satisfied_by(_tx(datetime(2024, 7, 10, 14, 30))) is False

    def test_end_date_object_covers_whole_day(self):
        spec = TransactionFilterSpecification(end_date=date(2024, 7, 10))
        assert spec.end_datetime == datetime.combine(date(2024, 7, 10), time.max)

    def test_filter_dto_from_date_picker_includes_bot_transactions(self):
        # FilterPanel кладёт date-объекты; pydantic превращает их в datetime 00:00.
        dto = TransactionFilterDTO(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 7, 10),
        )
        spec = TransactionFilterSpecification.from_filter_dto(dto)
        # Транзакция, добавленная ботом «сегодня», хранит реальное время.
        assert spec.is_satisfied_by(_tx(datetime(2024, 7, 10, 14, 30))) is True

    def test_start_datetime_at_midnight_unchanged(self):
        spec = TransactionFilterSpecification(start_date=datetime(2024, 7, 10))
        assert spec.is_satisfied_by(_tx(datetime(2024, 7, 9, 23, 0))) is False
        assert spec.is_satisfied_by(_tx(datetime(2024, 7, 10, 0, 0))) is True
