"""
Тесты для TelegramBot.
"""
from types import SimpleNamespace

import pytest

from solepro.presentation.telegram import bot as bot_module


class _FakeApp:
    def __init__(self):
        self.handlers = []
        self.error_handlers = []
        self.polling_kwargs = None
        self.stop_called = False
        self.bot = SimpleNamespace(send_message=self._send_message)
        self.sent = []

    async def _send_message(self, **kwargs):
        self.sent.append(kwargs)

    def add_handler(self, handler):
        self.handlers.append(handler)

    def add_error_handler(self, handler):
        self.error_handlers.append(handler)

    def run_polling(self, **kwargs):
        self.polling_kwargs = kwargs

    def stop(self):
        self.stop_called = True


class _Builder:
    def __init__(self, app):
        self._app = app
        self._token = None
        self._post_init = None

    def token(self, token):
        self._token = token
        return self

    def post_init(self, callback):
        self._post_init = callback
        return self

    def build(self):
        return self._app


@pytest.fixture
def fake_config():
    return SimpleNamespace(
        bot_token="token-123",
        allowed_users=[1001, 1002],
        log_level="INFO",
        admin_chat_id=9999,
    )


def test_init_requires_token(monkeypatch):
    monkeypatch.setattr(
        bot_module,
        "get_telegram_config",
        lambda: SimpleNamespace(
            bot_token="",
            allowed_users=[],
            log_level="INFO",
            admin_chat_id=None,
        ),
    )
    with pytest.raises(ValueError):
        bot_module.TelegramBot()


def test_setup_application_registers_handlers(monkeypatch, fake_config):
    fake_app = _FakeApp()
    builder = _Builder(fake_app)
    setup_called = {"value": False}

    class _FakeApplication:
        @staticmethod
        def builder():
            return builder

    monkeypatch.setattr(bot_module, "Application", _FakeApplication)
    monkeypatch.setattr(bot_module, "get_telegram_config", lambda: fake_config)
    monkeypatch.setattr(bot_module, "AccessMiddleware", lambda allowed_users: ("middleware", allowed_users))
    monkeypatch.setattr(
        bot_module,
        "setup_handlers",
        lambda app, dependencies=None: setup_called.__setitem__(
            "value", app is fake_app and dependencies is not None
        ),
    )

    bot = bot_module.TelegramBot()
    bot.setup_application()

    assert bot.application is fake_app
    assert ("middleware", fake_config.allowed_users) in fake_app.handlers
    assert len(fake_app.error_handlers) == 1
    assert setup_called["value"] is True


@pytest.mark.asyncio
async def test_post_init_sends_messages(monkeypatch, fake_config):
    monkeypatch.setattr(bot_module, "get_telegram_config", lambda: fake_config)
    bot = bot_module.TelegramBot()
    app = _FakeApp()

    await bot.post_init(app)

    recipients = {item["chat_id"] for item in app.sent}
    assert recipients == {9999, 1001, 1002}
    assert all("Бот запущен" in item["text"] for item in app.sent)


@pytest.mark.asyncio
async def test_error_handler_user_and_admin_message(monkeypatch, fake_config):
    monkeypatch.setattr(bot_module, "get_telegram_config", lambda: fake_config)
    bot = bot_module.TelegramBot()

    sent = []

    async def _send_message(**kwargs):
        sent.append(kwargs)

    update = SimpleNamespace(
        effective_chat=SimpleNamespace(id=1001),
        effective_user=SimpleNamespace(id=1001, username="user1"),
        effective_message=SimpleNamespace(text="/stats"),
    )
    context = SimpleNamespace(error=RuntimeError("boom"), bot=SimpleNamespace(send_message=_send_message))

    await bot.error_handler(update, context)

    assert len(sent) == 2
    assert sent[0]["chat_id"] == 1001
    assert "Произошла ошибка" in sent[0]["text"]
    assert sent[1]["chat_id"] == 9999
    assert "Ошибка в боте" in sent[1]["text"]


def test_run_and_stop(monkeypatch, fake_config):
    monkeypatch.setattr(bot_module, "get_telegram_config", lambda: fake_config)
    bot = bot_module.TelegramBot()
    app = _FakeApp()

    monkeypatch.setattr(bot, "setup_application", lambda: setattr(bot, "application", app))

    bot.run()
    assert app.polling_kwargs is not None
    assert app.polling_kwargs["drop_pending_updates"] is True
    assert app.polling_kwargs["timeout"] == 30

    bot.stop()
    assert app.stop_called is True
