"""
Тесты для Telegram handlers.
"""
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from telegram.ext import ConversationHandler

from solepro.core.application.dto.transaction_dto import TransactionResponseDTO
from solepro.presentation.telegram import handlers


class _FakeMessage:
    def __init__(self, text=""):
        self.text = text
        self.replies = []

    async def reply_text(self, text, reply_markup=None):
        self.replies.append((text, reply_markup))


class _FakeUpdate:
    def __init__(self, message):
        self.message = message
        self.effective_message = message


class _DummyUseCase:
    def __init__(self, result=None, side_effect=None):
        self._result = result
        self._side_effect = side_effect
        self.calls = []

    def execute(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self._side_effect:
            raise self._side_effect
        return self._result


class _DummyContainer:
    def __init__(
        self,
        *,
        stats_result=None,
        counterparties_result=None,
        add_result=None,
        stats_side_effect=None,
        counterparties_side_effect=None,
        add_side_effect=None,
    ):
        self._stats = _DummyUseCase(stats_result, stats_side_effect)
        self._counterparties = _DummyUseCase(counterparties_result, counterparties_side_effect)
        self._add = _DummyUseCase(add_result, add_side_effect)

    def get_transaction_statistics_use_case(self):
        return self._stats

    def list_counterparties_use_case(self):
        return self._counterparties

    def add_transaction_use_case(self):
        return self._add


def _to_dependencies(dummy_container):
    return handlers.HandlerDependencies(
        get_transaction_statistics_use_case=dummy_container.get_transaction_statistics_use_case,
        list_counterparties_use_case=dummy_container.list_counterparties_use_case,
        add_transaction_use_case=dummy_container.add_transaction_use_case,
    )


@pytest.fixture
def fake_context():
    return SimpleNamespace(user_data={})


@pytest.mark.asyncio
async def test_start_and_help_content(fake_context):
    message = _FakeMessage()
    update = _FakeUpdate(message)

    await handlers.start(update, fake_context)
    await handlers.help_command(update, fake_context)

    assert len(message.replies) == 2
    assert "SolePro bot is running" in message.replies[0][0]
    assert "Как пользоваться ботом" in message.replies[1][0]


@pytest.mark.asyncio
async def test_stats_and_counterparties_content(monkeypatch, fake_context):
    message = _FakeMessage()
    update = _FakeUpdate(message)

    stats = SimpleNamespace(
        total_transactions=2,
        total_income=100,
        total_expense=20,
        total_tax=5,
        total_profit=75,
        first_transaction_date=datetime(2026, 2, 1),
        last_transaction_date=datetime(2026, 2, 10),
    )
    counterparties = SimpleNamespace(
        counterparties=[SimpleNamespace(name="Alpha"), SimpleNamespace(name="Beta")]
    )
    dummy_container = _DummyContainer(stats_result=stats, counterparties_result=counterparties)
    monkeypatch.setattr(handlers, "_dependencies", _to_dependencies(dummy_container))

    await handlers.stats_command(update, fake_context)
    await handlers.counterparties_command(update, fake_context)

    assert "Общая статистика" in message.replies[0][0]
    assert "Транзакции: 2" in message.replies[0][0]
    assert "Контрагенты:\nAlpha\nBeta" == message.replies[1][0]


@pytest.mark.asyncio
async def test_stats_and_counterparties_error_paths(monkeypatch, fake_context):
    message = _FakeMessage()
    update = _FakeUpdate(message)
    dummy_container = _DummyContainer(
        stats_side_effect=RuntimeError("stats-failed"),
        counterparties_side_effect=RuntimeError("cp-failed"),
    )
    monkeypatch.setattr(handlers, "_dependencies", _to_dependencies(dummy_container))

    await handlers.stats_command(update, fake_context)
    await handlers.counterparties_command(update, fake_context)

    assert "Ошибка получения статистики" in message.replies[0][0]
    assert "Ошибка получения контрагентов" in message.replies[1][0]


@pytest.mark.asyncio
async def test_add_flow_happy_path(monkeypatch, fake_context):
    created = TransactionResponseDTO(
        id=uuid4(),
        date=datetime(2026, 2, 10, 12, 0, 0),
        income=Decimal("100"),
        expense=Decimal("10"),
        tax=Decimal("5"),
        profit=Decimal("85"),
        counterparty_id=None,
        counterparty_name="Alpha",
        note="ok",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    dummy_container = _DummyContainer(
        add_result=created,
        counterparties_result=SimpleNamespace(counterparties=[SimpleNamespace(name="Alpha")]),
    )
    monkeypatch.setattr(handlers, "_dependencies", _to_dependencies(dummy_container))

    monkeypatch.setattr(
        handlers,
        "get_app_config",
        lambda: SimpleNamespace(date_format="%d.%m.%Y"),
    )

    msg = _FakeMessage()
    update = _FakeUpdate(msg)

    state = await handlers.add_command(update, fake_context)
    assert state == handlers.DATE

    msg.text = "10.02.2026"
    state = await handlers.add_date(update, fake_context)
    assert state == handlers.INCOME

    msg.text = "100"
    state = await handlers.add_income(update, fake_context)
    assert state == handlers.EXPENSE

    msg.text = "10"
    state = await handlers.add_expense(update, fake_context)
    assert state == handlers.TAX

    msg.text = "5"
    state = await handlers.add_tax(update, fake_context)
    assert state == handlers.COUNTERPARTY

    msg.text = "Alpha"
    state = await handlers.add_counterparty(update, fake_context)
    assert state == handlers.NOTE

    msg.text = "Test note"
    state = await handlers.add_note(update, fake_context)
    assert state == handlers.CONFIRM
    assert "Проверьте данные" in msg.replies[-1][0]

    msg.text = "да"
    state = await handlers.add_confirm(update, fake_context)
    assert state == ConversationHandler.END
    assert "Транзакция добавлена" in msg.replies[-1][0]
    assert fake_context.user_data == {}


@pytest.mark.asyncio
async def test_add_flow_invalid_values_and_cancel(fake_context, monkeypatch):
    monkeypatch.setattr(
        handlers,
        "get_app_config",
        lambda: SimpleNamespace(date_format="%d.%m.%Y"),
    )
    monkeypatch.setattr(handlers, "_dependencies", _to_dependencies(_DummyContainer()))

    msg = _FakeMessage("31-01-2026")
    update = _FakeUpdate(msg)

    state = await handlers.add_date(update, fake_context)
    assert state == handlers.DATE
    assert "Неверная дата" in msg.replies[-1][0]

    msg.text = "-1"
    state = await handlers.add_income(update, fake_context)
    assert state == handlers.INCOME
    assert "Неверная сумма" in msg.replies[-1][0]

    msg.text = "123"
    await handlers.add_income(update, fake_context)
    msg.text = "-1"
    state = await handlers.add_expense(update, fake_context)
    assert state == handlers.EXPENSE

    msg.text = "50"
    await handlers.add_expense(update, fake_context)
    msg.text = "-2"
    state = await handlers.add_tax(update, fake_context)
    assert state == handlers.TAX

    msg.text = "любое"
    state = await handlers.add_cancel(update, fake_context)
    assert state == ConversationHandler.END
    assert fake_context.user_data == {}


@pytest.mark.asyncio
async def test_add_confirm_no_branch(fake_context, monkeypatch):
    monkeypatch.setattr(handlers, "_dependencies", _to_dependencies(_DummyContainer()))
    msg = _FakeMessage("нет")
    update = _FakeUpdate(msg)
    fake_context.user_data = {"date": datetime.now()}

    state = await handlers.add_confirm(update, fake_context)
    assert state == ConversationHandler.END
    assert "Создание отменено" in msg.replies[-1][0]
    assert fake_context.user_data == {}


@pytest.mark.asyncio
async def test_unknown_command(fake_context):
    msg = _FakeMessage("/oops")
    update = _FakeUpdate(msg)

    await handlers.unknown_command(update, fake_context)
    assert msg.replies[-1][0] == "Unknown command. Use /help."
