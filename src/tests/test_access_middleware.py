"""
Tests for Telegram access middleware.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from solepro.presentation.telegram.middlewares.access_middleware import AccessMiddleware


def _build_update(user_id=None):
    effective_user = (
        SimpleNamespace(id=user_id) if user_id is not None else None
    )
    return SimpleNamespace(
        effective_user=effective_user,
        message=None,
        callback_query=None,
        inline_query=None,
        effective_message=None,
    )


def test_check_update_returns_none_when_no_user_in_update():
    middleware = AccessMiddleware(allowed_users=[1, 2])
    update = _build_update(user_id=None)

    assert middleware.check_update(update) is None


def test_check_update_blocks_unauthorized_user():
    middleware = AccessMiddleware(allowed_users=[1, 2])
    update = _build_update(user_id=3)

    assert middleware.check_update(update) is True


def test_check_update_allows_authorized_user():
    middleware = AccessMiddleware(allowed_users=[1, 2])
    update = _build_update(user_id=2)

    assert middleware.check_update(update) is False


def test_check_update_blocks_everyone_when_allowlist_empty():
    """Fail-closed: пустой allowlist закрывает доступ, а не открывает."""
    middleware = AccessMiddleware(allowed_users=[])
    update = _build_update(user_id=999)

    assert middleware.check_update(update) is True


def test_check_update_allows_all_with_explicit_flag():
    """Открытый доступ для разработки включается только явным флагом."""
    middleware = AccessMiddleware(allowed_users=[], allow_all=True)
    update = _build_update(user_id=999)

    assert middleware.check_update(update) is False


def test_allow_all_flag_ignored_when_allowlist_present():
    """При заполненном allowlist флаг allow_all не расширяет доступ."""
    middleware = AccessMiddleware(allowed_users=[1], allow_all=True)
    update = _build_update(user_id=999)

    assert middleware.check_update(update) is True


@pytest.mark.asyncio
async def test_handle_sends_access_denied_message():
    sent = {"text": None}

    async def _reply_text(text):
        sent["text"] = text

    middleware = AccessMiddleware(allowed_users=[1])
    update = SimpleNamespace(
        effective_message=SimpleNamespace(reply_text=_reply_text),
        effective_user=SimpleNamespace(id=2),
    )
    context = SimpleNamespace()

    await middleware._handle(update, context)

    assert sent["text"] is not None
    assert "Доступ запрещен" in sent["text"]

