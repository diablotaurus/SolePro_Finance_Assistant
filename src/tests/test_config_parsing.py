"""
Tests for infrastructure config parsing.
"""
from __future__ import annotations

from pathlib import Path

from solepro.infrastructure import config as config_module


def test_get_database_config_normalizes_relative_sqlite_path(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/test_finances.db")
    monkeypatch.setattr(config_module, "project_root", tmp_path)

    cfg = config_module.get_database_config()

    expected_absolute = (tmp_path / "data" / "test_finances.db").resolve().as_posix()
    assert cfg.url == f"sqlite:///{expected_absolute}"


def test_telegram_config_parses_allowlist_and_admin_id(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "1001, abc, 1002, , -5, 42x, 1003")
    monkeypatch.setenv("TELEGRAM_ADMIN_CHAT_ID", "9999")

    cfg = config_module.get_telegram_config()

    assert cfg.bot_token == "token"
    assert cfg.allowed_users == [1001, 1002, 1003]
    assert cfg.admin_chat_id == 9999


def test_telegram_config_invalid_admin_id_becomes_none(monkeypatch):
    monkeypatch.setenv("TELEGRAM_ADMIN_CHAT_ID", "not-a-number")

    cfg = config_module.get_telegram_config()

    assert cfg.admin_chat_id is None


def test_app_config_boolean_and_integer_fields_from_env(monkeypatch):
    monkeypatch.setenv("APP_DEBUG", "False")
    monkeypatch.setenv("ENABLE_AUTO_BACKUP", "false")
    monkeypatch.setenv("ENABLE_DATA_ENCRYPTION", "TRUE")
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "14")
    monkeypatch.setenv("EXPORT_MAX_ROWS", "5000")

    cfg = config_module.get_app_config()

    assert cfg.debug is False
    assert cfg.enable_auto_backup is False
    assert cfg.enable_data_encryption is True
    assert cfg.backup_retention_days == 14
    assert cfg.export_max_rows == 5000

