"""
Tests for Alembic migration helper module.
"""
from __future__ import annotations

import builtins
import sqlite3
import types
from contextlib import closing

import pytest

from solepro.infrastructure.database import migrations as migrations_module
from solepro.shared.exceptions import MigrationException


class _FakeAlembicConfig:
    def __init__(self, ini_path: str):
        self.ini_path = ini_path
        self.options: dict[str, str] = {}
        self.attributes: dict = {}

    def set_main_option(self, key: str, value: str) -> None:
        self.options[key] = value


class _CommandSpy:
    def __init__(self, *, upgrade_side_effect: Exception | None = None):
        self.upgrade_calls = []
        self.stamp_calls = []
        self.upgrade_side_effect = upgrade_side_effect

    def upgrade(self, config, revision):
        self.upgrade_calls.append((config, revision))
        if self.upgrade_side_effect is not None:
            raise self.upgrade_side_effect

    def stamp(self, config, revision):
        self.stamp_calls.append((config, revision))


def _install_fake_alembic(monkeypatch, command_spy: _CommandSpy):
    fake_alembic = types.ModuleType("alembic")
    fake_alembic.command = command_spy

    fake_alembic_config = types.ModuleType("alembic.config")
    fake_alembic_config.Config = _FakeAlembicConfig

    monkeypatch.setitem(__import__("sys").modules, "alembic", fake_alembic)
    monkeypatch.setitem(__import__("sys").modules, "alembic.config", fake_alembic_config)


def test_upgrade_database_to_head_returns_false_without_alembic(monkeypatch):
    original_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "alembic" or name.startswith("alembic."):
            raise ImportError("alembic is unavailable")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    assert migrations_module.upgrade_database_to_head("sqlite:///tmp.db") is False


def test_upgrade_database_to_head_success(monkeypatch):
    command_spy = _CommandSpy()
    _install_fake_alembic(monkeypatch, command_spy)
    monkeypatch.setattr(migrations_module, "_prepare_legacy_database", lambda *args: None)

    result = migrations_module.upgrade_database_to_head("sqlite:///tmp.db")

    assert result is True
    assert len(command_spy.upgrade_calls) == 1
    assert command_spy.upgrade_calls[0][1] == "head"
    assert command_spy.stamp_calls == []


def test_upgrade_database_to_head_legacy_tables_uses_initial_stamp(monkeypatch):
    command_spy = _CommandSpy()
    _install_fake_alembic(monkeypatch, command_spy)

    disposed = {"value": False}

    class _FakeEngine:
        def dispose(self):
            disposed["value"] = True

    class _Inspector:
        @staticmethod
        def get_table_names() -> list[str]:
            return ["counterparties", "transactions"]

    monkeypatch.setattr(migrations_module, "create_engine", lambda url: _FakeEngine())
    monkeypatch.setattr(migrations_module, "inspect", lambda engine: _Inspector())

    result = migrations_module.upgrade_database_to_head("sqlite:///tmp.db")

    assert result is True
    assert disposed["value"] is True
    assert len(command_spy.stamp_calls) == 1
    assert command_spy.stamp_calls[0][1] == "20260213_0001"
    assert len(command_spy.upgrade_calls) == 1


def test_upgrade_database_to_head_non_table_error_raises(monkeypatch):
    command_spy = _CommandSpy(upgrade_side_effect=RuntimeError("permission denied"))
    _install_fake_alembic(monkeypatch, command_spy)
    monkeypatch.setattr(migrations_module, "_prepare_legacy_database", lambda *args: None)

    with pytest.raises(MigrationException, match="permission denied"):
        migrations_module.upgrade_database_to_head("sqlite:///tmp.db")

    assert command_spy.stamp_calls == []


def test_upgrade_database_to_head_rejects_partial_legacy_schema(monkeypatch):
    command_spy = _CommandSpy()
    _install_fake_alembic(monkeypatch, command_spy)

    class _FakeEngine:
        def dispose(self):
            pass

    class _Inspector:
        @staticmethod
        def get_table_names() -> list[str]:
            return ["transactions"]

    monkeypatch.setattr(migrations_module, "create_engine", lambda url: _FakeEngine())
    monkeypatch.setattr(migrations_module, "inspect", lambda engine: _Inspector())

    with pytest.raises(MigrationException, match="counterparties"):
        migrations_module.upgrade_database_to_head("sqlite:///tmp.db")

    assert command_spy.upgrade_calls == []


def test_upgrade_database_to_head_applies_pending_revisions_to_legacy_db(tmp_path):
    database_path = tmp_path / "legacy.db"
    with closing(sqlite3.connect(database_path)) as connection:
        connection.executescript(
            """
            CREATE TABLE counterparties (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                contact_info TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            );
            CREATE TABLE transactions (
                id VARCHAR(36) PRIMARY KEY,
                date DATETIME NOT NULL,
                income FLOAT NOT NULL,
                expense FLOAT NOT NULL,
                tax FLOAT NOT NULL,
                note TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                counterparty_id VARCHAR(36)
            );
            INSERT INTO transactions VALUES (
                '00000000-0000-0000-0000-000000000001',
                '2026-01-01 00:00:00', 10, 0, 0, NULL,
                '2026-01-01 00:00:00', '2026-01-01 00:00:00',
                '00000000-0000-0000-0000-000000000099'
            );
            """
        )
        connection.commit()

    database_url = f"sqlite:///{database_path.as_posix()}"
    assert migrations_module.upgrade_database_to_head(database_url) is True

    with closing(sqlite3.connect(database_path)) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        columns = {
            row[1]: row[2] for row in connection.execute("PRAGMA table_info(transactions)")
        }
        counterparty_id = connection.execute(
            "SELECT counterparty_id FROM transactions"
        ).fetchone()

    assert revision == ("20260716_0003",)
    assert columns["income"] == "NUMERIC(14, 2)"
    assert counterparty_id == (None,)
