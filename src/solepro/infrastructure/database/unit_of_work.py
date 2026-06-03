"""
SQLAlchemy Unit of Work implementation.
"""
from __future__ import annotations

from typing import Optional

from ...core.application.unit_of_work import UnitOfWork
from .repositories import SQLAlchemyCounterpartyRepository, SQLAlchemyTransactionRepository
from .session_manager import DatabaseSessionManager


class SQLAlchemyUnitOfWork(UnitOfWork):
    """Creates a shared SQLAlchemy session for all repositories in a use case."""

    def __init__(self, session_manager: DatabaseSessionManager):
        self._session_manager = session_manager
        self._session = None
        self.transactions = None
        self.counterparties = None

    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        self._session = self._session_manager.get_session()
        self.transactions = SQLAlchemyTransactionRepository(self._session)
        self.counterparties = SQLAlchemyCounterpartyRepository(self._session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is not None:
                self.rollback()
        finally:
            self._close_session()

    def commit(self) -> None:
        if self._session is not None:
            self._session.commit()

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()

    def _close_session(self) -> None:
        if self._session is None:
            return
        self._session.close()
        self._session_manager.scoped_session.remove()
        self._session = None
        self.transactions = None
        self.counterparties = None
