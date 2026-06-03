"""
Tests for telegram handlers setup wiring.
"""
from __future__ import annotations

from telegram.ext import CommandHandler, ConversationHandler, MessageHandler

from solepro.presentation.telegram import handlers


class _FakeApplication:
    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)


def test_setup_handlers_registers_expected_handlers_and_conversation(monkeypatch):
    configured = {"deps": None}
    monkeypatch.setattr(
        handlers,
        "configure_dependencies",
        lambda deps: configured.__setitem__("deps", deps),
    )

    app = _FakeApplication()
    deps = handlers.HandlerDependencies(
        get_transaction_statistics_use_case=lambda: None,
        list_counterparties_use_case=lambda: None,
        add_transaction_use_case=lambda: None,
    )

    handlers.setup_handlers(app, dependencies=deps)

    assert configured["deps"] is deps
    assert len(app.handlers) == 8

    assert isinstance(app.handlers[0], CommandHandler)
    assert app.handlers[0].callback is handlers.start
    assert "start" in app.handlers[0].commands

    assert isinstance(app.handlers[1], CommandHandler)
    assert app.handlers[1].callback is handlers.help_command
    assert "help" in app.handlers[1].commands

    assert isinstance(app.handlers[2], CommandHandler)
    assert app.handlers[2].callback is handlers.stats_command
    assert "stats" in app.handlers[2].commands

    assert isinstance(app.handlers[3], CommandHandler)
    assert app.handlers[3].callback is handlers.stats_command
    assert "stat" in app.handlers[3].commands

    assert isinstance(app.handlers[4], CommandHandler)
    assert app.handlers[4].callback is handlers.counterparties_command
    assert "counterparties" in app.handlers[4].commands

    assert isinstance(app.handlers[5], MessageHandler)
    assert app.handlers[5].callback is handlers.stats_command

    conv = app.handlers[6]
    assert isinstance(conv, ConversationHandler)
    assert set(conv.states.keys()) == {
        handlers.DATE,
        handlers.INCOME,
        handlers.EXPENSE,
        handlers.TAX,
        handlers.COUNTERPARTY,
        handlers.NOTE,
        handlers.CONFIRM,
    }

    entry_callbacks = [entry.callback for entry in conv.entry_points]
    assert handlers.add_command in entry_callbacks
    assert len(conv.entry_points) == 2
    assert conv.fallbacks[0].callback is handlers.add_cancel
    assert "cancel" in conv.fallbacks[0].commands

    assert isinstance(app.handlers[7], MessageHandler)
    assert app.handlers[7].callback is handlers.unknown_command


def test_setup_handlers_without_dependencies_does_not_reconfigure(monkeypatch):
    called = {"value": 0}
    monkeypatch.setattr(
        handlers,
        "configure_dependencies",
        lambda deps: called.__setitem__("value", called["value"] + 1),
    )
    app = _FakeApplication()

    handlers.setup_handlers(app, dependencies=None)

    assert called["value"] == 0
    assert len(app.handlers) == 8

