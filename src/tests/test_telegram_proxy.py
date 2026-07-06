"""
Тесты «мягкого» прокси для Telegram-бота.

Проверяют функцию is_proxy_reachable без обращения к сети наружу:
используется реальный локальный слушающий сокет (доступен) и заведомо
закрытый порт (недоступен).
"""
import socket

import pytest

from solepro.presentation.telegram.bot import is_proxy_reachable
from solepro.infrastructure.config import TelegramConfig


@pytest.fixture
def listening_port():
    """Поднять локальный TCP-сервер и вернуть его порт; закрыть после теста."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    try:
        yield port
    finally:
        srv.close()


class TestIsProxyReachable:
    """Тесты is_proxy_reachable."""

    def test_reachable_when_port_is_listening(self, listening_port):
        url = f"socks5://127.0.0.1:{listening_port}"
        assert is_proxy_reachable(url, timeout=1.0) is True

    def test_not_reachable_when_port_closed(self):
        # Порт, который заведомо никто не слушает.
        url = "socks5://127.0.0.1:1"
        assert is_proxy_reachable(url, timeout=1.0) is False

    def test_empty_url_returns_false(self):
        assert is_proxy_reachable("", timeout=1.0) is False

    def test_none_url_returns_false(self):
        assert is_proxy_reachable(None, timeout=1.0) is False  # type: ignore[arg-type]

    def test_malformed_url_returns_false(self):
        assert is_proxy_reachable("not a url", timeout=1.0) is False

    def test_default_port_used_when_absent(self, listening_port, monkeypatch):
        # Порт в URL не указан → берётся дефолт для схемы. Подменяем дефолт
        # на реально слушающий порт и проверяем, что он подхватился.
        import solepro.presentation.telegram.bot as bot_module

        monkeypatch.setitem(
            bot_module._DEFAULT_PROXY_PORTS, "socks5", listening_port
        )
        assert is_proxy_reachable("socks5://127.0.0.1", timeout=1.0) is True


class TestTelegramConfigProxy:
    """Тесты чтения TELEGRAM_PROXY в конфиг."""

    def test_proxy_none_when_env_absent(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_PROXY", raising=False)
        assert TelegramConfig().proxy_url is None

    def test_proxy_none_when_env_blank(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_PROXY", "   ")
        assert TelegramConfig().proxy_url is None

    def test_proxy_value_read_and_stripped(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_PROXY", "  socks5://192.168.0.8:10808  ")
        assert TelegramConfig().proxy_url == "socks5://192.168.0.8:10808"
