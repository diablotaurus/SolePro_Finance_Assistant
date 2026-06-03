"""
Tests for Alembic migration helper module.
"""
from __future__ import annotations

import builtins
import types

from solepro.infrastructure.database import migrations as migrations_module


class _FakeAlembicConfig:
    def __init__(self, ini_path: str):
        self.ini_path = ini_path
        self.options: dict[str, str] = {}

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

    result = migrations_module.upgrade_database_to_head("sqlite:///tmp.db")

    assert result is True
    assert len(command_spy.upgrade_calls) == 1
    assert command_spy.upgrade_calls[0][1] == "head"
    assert command_spy.stamp_calls == []


def test_upgrade_database_to_head_legacy_tables_uses_stamp(monkeypatch):
    command_spy = _CommandSpy(upgrade_side_effect=RuntimeError("table already exists"))
    _install_fake_alembic(monkeypatch, command_spy)

    disposed = {"value": False}

    class _FakeEngine:
        def dispose(self):
            disposed["value"] = True

    class _Inspector:
        @staticmethod
        def has_table(name: str) -> bool:
            return name in {"counterparties", "transactions"}

    monkeypatch.setattr(migrations_module, "create_engine", lambda url: _FakeEngine())
    monkeypatch.setattr(migrations_module, "inspect", lambda engine: _Inspector())

    result = migrations_module.upgrade_database_to_head("sqlite:///tmp.db")

    assert result is True
    assert disposed["value"] is True
    assert len(command_spy.stamp_calls) == 1
    assert command_spy.stamp_calls[0][1] == "head"


def test_upgrade_database_to_head_non_table_error_returns_false(monkeypatch):
    command_spy = _CommandSpy(upgrade_side_effect=RuntimeError("permission denied"))
    _install_fake_alembic(monkeypatch, command_spy)

    result = migrations_module.upgrade_database_to_head("sqlite:///tmp.db")

    assert result is False
    assert command_spy.stamp_calls == []

