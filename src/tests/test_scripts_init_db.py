"""
Tests for scripts/init_db.py helpers and bootstrap flow.
"""
import importlib.machinery
import importlib.util
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

    state = {"closed": False, "saved": []}

    class _FakeRepo:
        def __init__(self, session):
            self.session = session

        def exists_by_name(self, name: str) -> bool:
            return name == "A"

        def save(self, counterparty):
            state["saved"].append(counterparty.name)
            return counterparty

    fake_session = SimpleNamespace(close=lambda: state.__setitem__("closed", True))
    fake_session_manager = SimpleNamespace(get_session=lambda: fake_session)

    monkeypatch.setattr(module, "SQLAlchemyCounterpartyRepository", _FakeRepo)
    monkeypatch.setattr(module.container, "session_manager", lambda: fake_session_manager)

    result = module.seed_initial_data()

    assert result == {"created": 1, "skipped": 1}
    assert state["saved"] == ["B"]
    assert state["closed"] is True


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
