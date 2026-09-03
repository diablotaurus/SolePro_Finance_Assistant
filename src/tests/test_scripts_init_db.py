"""
Tests for scripts/init_db.py helpers and bootstrap flow.
"""
import importlib.machinery
import importlib.util
import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace


def _load_init_db_module():
    project_root = Path(__file__).resolve().parents[2]
    module_path = project_root / "scripts" / "init_db.py"
    loader = importlib.machinery.SourceFileLoader("init_db_script", str(module_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_get_initial_counterparties_default(monkeypatch):
    module = _load_init_db_module()
    monkeypatch.delenv("INITIAL_COUNTERPARTIES", raising=False)

    result = module._get_initial_counterparties()

    assert result == list(module.DEFAULT_COUNTERPARTIES)


def test_get_initial_counterparties_from_env(monkeypatch):
    module = _load_init_db_module()
    monkeypatch.setenv("INITIAL_COUNTERPARTIES", "  Alpha , , Beta ,  Gamma  ")

    result = module._get_initial_counterparties()

    assert result == ["Alpha", "Beta", "Gamma"]


def test_seed_initial_data_created_and_skipped(monkeypatch):
    module = _load_init_db_module()
    monkeypatch.setattr(module, "_get_initial_counterparties", lambda: ["A", "B"])

    state = {"closed": False, "committed": False, "rolled_back": False, "saved": []}

    class _FakeRepo:
        def __init__(self, session):
            self.session = session

        def exists_by_name(self, name: str) -> bool:
            return name == "A"

        def save(self, counterparty):
            state["saved"].append(counterparty.name)
            return counterparty

    fake_session = SimpleNamespace(
        commit=lambda: state.__setitem__("committed", True),
        rollback=lambda: state.__setitem__("rolled_back", True),
        close=lambda: state.__setitem__("closed", True),
    )
    fake_session_manager = SimpleNamespace(get_session=lambda: fake_session)

    monkeypatch.setattr(module, "SQLAlchemyCounterpartyRepository", _FakeRepo)
    monkeypatch.setattr(module.container, "session_manager", lambda: fake_session_manager)

    result = module.seed_initial_data()

    assert result == {"created": 1, "skipped": 1}
    assert state["saved"] == ["B"]
    assert state["committed"] is True
    assert state["rolled_back"] is False
    assert state["closed"] is True


def test_seed_initial_data_rolls_back_on_error(monkeypatch):
    module = _load_init_db_module()
    monkeypatch.setattr(module, "_get_initial_counterparties", lambda: ["A"])
    state = {"committed": False, "rolled_back": False, "closed": False}

    class _FailingRepo:
        def __init__(self, session):
            self.session = session

        def exists_by_name(self, name: str) -> bool:
            return False

        def save(self, counterparty):
            raise RuntimeError("save failed")

    fake_session = SimpleNamespace(
        commit=lambda: state.__setitem__("committed", True),
        rollback=lambda: state.__setitem__("rolled_back", True),
        close=lambda: state.__setitem__("closed", True),
    )
    monkeypatch.setattr(module, "SQLAlchemyCounterpartyRepository", _FailingRepo)
    monkeypatch.setattr(
        module.container,
        "session_manager",
        lambda: SimpleNamespace(get_session=lambda: fake_session),
    )

    import pytest

    with pytest.raises(RuntimeError, match="save failed"):
        module.seed_initial_data()

    assert state == {"committed": False, "rolled_back": True, "closed": True}


def test_seed_initial_data_persists_rows(tmp_path, monkeypatch):
    from solepro.infrastructure.database.session_manager import DatabaseSessionManager

    module = _load_init_db_module()
    database_path = tmp_path / "seed.db"
    manager = DatabaseSessionManager(f"sqlite:///{database_path.as_posix()}")
    manager.create_tables()
    monkeypatch.setattr(module, "_get_initial_counterparties", lambda: ["Persistent"])
    monkeypatch.setattr(module.container, "session_manager", lambda: manager)

    assert module.seed_initial_data() == {"created": 1, "skipped": 0}

    with closing(sqlite3.connect(database_path)) as connection:
        assert connection.execute("SELECT name FROM counterparties").fetchone() == (
            "Persistent",
        )
    manager.close()


def test_init_database_uses_migrations_without_create_tables(monkeypatch):
    module = _load_init_db_module()
    state = {"create_tables_called": False, "seed_called": False}

    fake_session_manager = SimpleNamespace(
        database_url="sqlite:///./data/finances.db",
        create_tables=lambda: state.__setitem__("create_tables_called", True),
    )

    monkeypatch.setattr(
        module,
        "get_database_config",
        lambda: SimpleNamespace(use_migrations=True),
    )
    monkeypatch.setattr(module.container, "session_manager", lambda: fake_session_manager)
    monkeypatch.setattr(module, "upgrade_database_to_head", lambda database_url=None: True)
    monkeypatch.setattr(
        module,
        "seed_initial_data",
        lambda: state.__setitem__("seed_called", True) or {"created": 0, "skipped": 0},
    )

    module.init_database()

    assert state["create_tables_called"] is False
    assert state["seed_called"] is True


def test_init_database_fallback_calls_create_tables(monkeypatch):
    module = _load_init_db_module()
    state = {"create_tables_called": False, "seed_called": False}

    fake_session_manager = SimpleNamespace(
        database_url="sqlite:///./data/finances.db",
        create_tables=lambda: state.__setitem__("create_tables_called", True),
    )

    monkeypatch.setattr(
        module,
        "get_database_config",
        lambda: SimpleNamespace(use_migrations=True),
    )
    monkeypatch.setattr(module.container, "session_manager", lambda: fake_session_manager)
    monkeypatch.setattr(module, "upgrade_database_to_head", lambda database_url=None: False)
    monkeypatch.setattr(
        module,
        "seed_initial_data",
        lambda: state.__setitem__("seed_called", True) or {"created": 0, "skipped": 0},
    )

    module.init_database()

    assert state["create_tables_called"] is True
    assert state["seed_called"] is True
