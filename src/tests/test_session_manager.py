"""
Tests for database session manager.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from solepro.infrastructure.database import session_manager as session_manager_module


def _stub_db_config():
    return SimpleNamespace(
        url="sqlite:///:memory:",
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
        echo=False,
    )


class _FakeSession:
    def __init__(self):
        self.commit_called = False
        self.rollback_called = False
        self.close_called = False

    def commit(self):
        self.commit_called = True

    def rollback(self):
        self.rollback_called = True

    def close(self):
        self.close_called = True


class _FakeScopedSession:
    def __init__(self, session: _FakeSession):
        self._session = session
        self.remove_called = False

    def __call__(self):
        return self._session

    def remove(self):
        self.remove_called = True


def test_session_manager_creates_sqlite_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(session_manager_module, "get_database_config", _stub_db_config)

    db_file = tmp_path / "nested" / "data" / "app.db"
    database_url = f"sqlite:///{db_file.as_posix()}"
    manager = session_manager_module.DatabaseSessionManager(database_url=database_url)
    try:
        assert db_file.parent.exists()
        assert db_file.parent.is_dir()
    finally:
        manager.close()


def test_session_context_commits_and_removes(monkeypatch, tmp_path):
    monkeypatch.setattr(session_manager_module, "get_database_config", _stub_db_config)
    db_url = f"sqlite:///{(tmp_path / 'commit_test.db').as_posix()}"
    manager = session_manager_module.DatabaseSessionManager(database_url=db_url)
    try:
        fake_session = _FakeSession()
        fake_scoped = _FakeScopedSession(fake_session)
        manager.scoped_session = fake_scoped

        with manager.session() as current:
            assert current is fake_session

        assert fake_session.commit_called is True
        assert fake_session.rollback_called is False
        assert fake_session.close_called is True
        assert fake_scoped.remove_called is True
    finally:
        manager.close()


def test_session_context_rollbacks_on_exception(monkeypatch, tmp_path):
    monkeypatch.setattr(session_manager_module, "get_database_config", _stub_db_config)
    db_url = f"sqlite:///{(tmp_path / 'rollback_test.db').as_posix()}"
    manager = session_manager_module.DatabaseSessionManager(database_url=db_url)
    try:
        fake_session = _FakeSession()
        fake_scoped = _FakeScopedSession(fake_session)
        manager.scoped_session = fake_scoped

        with pytest.raises(RuntimeError):
            with manager.session():
                raise RuntimeError("boom")

        assert fake_session.commit_called is False
        assert fake_session.rollback_called is True
        assert fake_session.close_called is True
        assert fake_scoped.remove_called is True
    finally:
        manager.close()


def test_close_disposes_engine(monkeypatch, tmp_path):
    monkeypatch.setattr(session_manager_module, "get_database_config", _stub_db_config)
    db_url = f"sqlite:///{(tmp_path / 'dispose_test.db').as_posix()}"
    manager = session_manager_module.DatabaseSessionManager(database_url=db_url)
    disposed = {"value": False}

    class _FakeEngine:
        def dispose(self):
            disposed["value"] = True

    manager.engine = _FakeEngine()
    manager.close()

    assert disposed["value"] is True
