"""
Тесты для TelegramBot.
"""
import logging
from types import SimpleNamespace

import pytest
from telegram.error import NetworkError, TimedOut

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
        self.proxy_url = None
        self.get_updates_proxy_url = None

    def token(self, token):
        self._token = token
        return self

    def post_init(self, callback):
        self._post_init = callback
        return self

    def proxy(self, url):
        self.proxy_url = url
        return self

    def get_updates_proxy(self, url):
        self.get_updates_proxy_url = url
        return self

    def build(self):
        return self._app


@pytest.fixture
def fake_config():
    return SimpleNamespace(
        bot_token="token-123",
        allowed_users=[1001, 1002],
        log_level="INFO",
        log_file="logs/test-bot.log",
        admin_chat_id=9999,
        proxy_url=None,
        allow_all_users=False,
    )


def test_init_requires_token(monkeypatch):
    monkeypatch.setattr(
        bot_module,
        "get_telegram_config",
        lambda: SimpleNamespace(
            bot_token="",
            allowed_users=[],
            log_level="INFO",
            log_file="logs/test-bot.log",
            admin_chat_id=None,
        ),
    )
    with pytest.raises(ValueError):
        bot_module.TelegramBot()


def test_setup_logging_suppresses_http_client_info(monkeypatch, fake_config):
    configured = {}
    dependency_levels = {}
    httpx_logger = logging.getLogger("httpx")
    httpcore_logger = logging.getLogger("httpcore")

    bot = bot_module.TelegramBot.__new__(bot_module.TelegramBot)
    bot.config = fake_config
    monkeypatch.setattr(
        bot_module,
        "configure_logging",
        lambda **kwargs: configured.update(kwargs),
    )
    monkeypatch.setattr(
        httpx_logger,
        "setLevel",
        lambda level: dependency_levels.__setitem__("httpx", level),
    )
    monkeypatch.setattr(
        httpcore_logger,
        "setLevel",
        lambda level: dependency_levels.__setitem__("httpcore", level),
    )

    bot.setup_logging()

    assert configured == {
        "level": fake_config.log_level,
        "log_file": fake_config.log_file,
    }
    assert dependency_levels == {
        "httpx": logging.WARNING,
        "httpcore": logging.WARNING,
    }


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
    monkeypatch.setattr(
        bot_module,
        "AccessMiddleware",
        lambda allowed_users, allow_all=False: ("middleware", allowed_users),
    )
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
    # Прокси не задан → билдер прокси не получал.
    assert builder.proxy_url is None
    assert builder.get_updates_proxy_url is None


def _prepare_bot(monkeypatch, config):
    """Собрать TelegramBot с фейковым Application и вернуть (bot, builder)."""
    fake_app = _FakeApp()
    builder = _Builder(fake_app)

    class _FakeApplication:
        @staticmethod
        def builder():
            return builder

    monkeypatch.setattr(bot_module, "Application", _FakeApplication)
    monkeypatch.setattr(bot_module, "get_telegram_config", lambda: config)
    monkeypatch.setattr(
        bot_module,
        "AccessMiddleware",
        lambda allowed_users, allow_all=False: ("middleware", allowed_users),
    )
    monkeypatch.setattr(bot_module, "setup_handlers", lambda app, dependencies=None: None)
    return bot_module.TelegramBot(), builder


def test_setup_application_uses_proxy_when_reachable(monkeypatch, fake_config):
    fake_config.proxy_url = "socks5://127.0.0.1:10808"
    monkeypatch.setattr(bot_module, "is_proxy_reachable", lambda url, timeout=2.0: True)

    bot, builder = _prepare_bot(monkeypatch, fake_config)
    bot.setup_application()

    assert builder.proxy_url == "socks5://127.0.0.1:10808"
    assert builder.get_updates_proxy_url == "socks5://127.0.0.1:10808"


def test_setup_application_skips_proxy_when_unreachable(monkeypatch, fake_config):
    fake_config.proxy_url = "socks5://127.0.0.1:10808"
    monkeypatch.setattr(bot_module, "is_proxy_reachable", lambda url, timeout=2.0: False)

    bot, builder = _prepare_bot(monkeypatch, fake_config)
    bot.setup_application()

    # Прокси недоступен → билдер прокси не получал (fallback напрямую).
    assert builder.proxy_url is None
    assert builder.get_updates_proxy_url is None


@pytest.mark.asyncio
async def test_post_init_sends_message_only_to_admin(monkeypatch, fake_config):
    monkeypatch.setattr(bot_module, "get_telegram_config", lambda: fake_config)
    bot = bot_module.TelegramBot()
    app = _FakeApp()

    await bot.post_init(app)

    assert len(app.sent) == 1
    assert app.sent[0]["chat_id"] == fake_config.admin_chat_id
    assert "Бот запущен" in app.sent[0]["text"]


@pytest.mark.asyncio
async def test_post_init_without_admin_sends_no_startup_message(
    monkeypatch,
    fake_config,
):
    fake_config.admin_chat_id = None
    monkeypatch.setattr(bot_module, "get_telegram_config", lambda: fake_config)
    bot = bot_module.TelegramBot()
    app = _FakeApp()

    await bot.post_init(app)

    assert app.sent == []


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


def test_proxy_log_target_hides_credentials():
    target = bot_module._proxy_log_target("socks5://secret-user:secret-pass@127.0.0.1:10808")

    assert target == "socks5://127.0.0.1:10808"
    assert "secret" not in target


@pytest.mark.parametrize(
    "network_error",
    [
        NetworkError("httpx.RemoteProtocolError: disconnected"),
        TimedOut(),
    ],
)
@pytest.mark.asyncio
async def test_error_handler_suppresses_background_network_alerts(
    monkeypatch,
    fake_config,
    caplog,
    network_error,
):
    monkeypatch.setattr(bot_module, "get_telegram_config", lambda: fake_config)
    bot = bot_module.TelegramBot()

    async def _unexpected_send_message(**kwargs):
        pytest.fail(f"Сетевая ошибка polling не должна отправлять сообщение: {kwargs}")

    context = SimpleNamespace(
        error=network_error,
        bot=SimpleNamespace(send_message=_unexpected_send_message),
    )

    with caplog.at_level(logging.WARNING, logger=bot_module.__name__):
        await bot.error_handler(None, context)

    assert "Временная сетевая ошибка Telegram polling" in caplog.text


def test_run_and_stop(monkeypatch, fake_config):
    monkeypatch.setattr(bot_module, "get_telegram_config", lambda: fake_config)
    bot = bot_module.TelegramBot()
    app = _FakeApp()

    monkeypatch.setattr(bot, "setup_application", lambda: setattr(bot, "application", app))

    bot.run()
    assert app.polling_kwargs is not None
    assert app.polling_kwargs["drop_pending_updates"] is True
    assert app.polling_kwargs["timeout"] == 30
    assert app.polling_kwargs["bootstrap_retries"] == -1

    bot.stop()
    assert app.stop_called is True
