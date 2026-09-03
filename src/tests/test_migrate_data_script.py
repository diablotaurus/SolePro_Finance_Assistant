"""Tests for the legacy database migration script."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from solepro.infrastructure.database.session_manager import DatabaseSessionManager


def _load_module():
    project_root = Path(__file__).resolve().parents[2]
    module_path = project_root / "scripts" / "migrate_data.py"
    loader = importlib.machinery.SourceFileLoader("migrate_data_script", str(module_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _create_legacy_database(path: Path, *, future_date: bool = False) -> None:
    transaction_date = "2999-01-01T00:00:00" if future_date else "2026-01-10T12:00:00"
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE counterparties (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                contact_info TEXT,
                created_at TEXT
            );
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                income TEXT,
                expense TEXT,
                tax TEXT,
                note TEXT,
                created_at TEXT,
                counterparty_id INTEGER
            );
            INSERT INTO counterparties VALUES
                (7, 'Legacy', 'Description', 'Contact', '2026-01-01T00:00:00');
            """
        )
        connection.execute(
            "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (11, transaction_date, "1.005", "0", "0", "Note", "2026-01-01T00:00:00", 7),
        )
        connection.commit()


def test_legacy_migration_is_atomic_and_uses_decimal(tmp_path, monkeypatch):
    module = _load_module()
    old_database = tmp_path / "old.db"
    target_database = tmp_path / "target.db"
    _create_legacy_database(old_database)
    manager = DatabaseSessionManager(f"sqlite:///{target_database.as_posix()}")
    manager.create_tables()
    monkeypatch.setattr(module, "get_session_manager", lambda: manager)
    monkeypatch.setattr(module, "upgrade_database_to_head", lambda _url: True)

    assert module.migrate_from_old_database(old_database) == (1, 1)

    with closing(sqlite3.connect(target_database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM counterparties").fetchone() == (1,)
        assert connection.execute("SELECT income FROM transactions").fetchone()[0] == 1.01
    manager.close()


def test_legacy_migration_rolls_back_all_rows_on_error(tmp_path, monkeypatch):
    module = _load_module()
    old_database = tmp_path / "old.db"
    target_database = tmp_path / "target.db"
    _create_legacy_database(old_database, future_date=True)
    manager = DatabaseSessionManager(f"sqlite:///{target_database.as_posix()}")
    manager.create_tables()
    monkeypatch.setattr(module, "get_session_manager", lambda: manager)
    monkeypatch.setattr(module, "upgrade_database_to_head", lambda _url: True)

    with pytest.raises(ValueError, match="будущем"):
        module.migrate_from_old_database(old_database)

    with closing(sqlite3.connect(target_database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM counterparties").fetchone() == (0,)
        assert connection.execute("SELECT COUNT(*) FROM transactions").fetchone() == (0,)
    manager.close()
