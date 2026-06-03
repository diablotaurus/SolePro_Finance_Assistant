"""
Unit of Work contracts for application use cases.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..domain.repositories.counterparty_repository import CounterpartyRepository
from ..domain.repositories.transaction_repository import TransactionRepository


class UnitOfWork(ABC):
    """Application contract for a transactional business operation."""

    transactions: Optional[TransactionRepository] = None
    counterparties: Optional[CounterpartyRepository] = None

    @abstractmethod
    def __enter__(self) -> "UnitOfWork":
        """Open the unit of work scope."""

    @abstractmethod
    def __exit__(self, exc_type, exc, tb) -> None:
        """Close the unit of work scope."""

    @abstractmethod
    def commit(self) -> None:
        """Persist pending changes."""

    @abstractmethod
    def rollback(self) -> None:
        """Rollback pending changes."""


class RepositoryUnitOfWork(UnitOfWork):
    """Adapter that wraps existing repositories into a Unit of Work contract."""

    def __init__(
        self,
        transaction_repository: Optional[TransactionRepository] = None,
        counterparty_repository: Optional[CounterpartyRepository] = None,
    ):
        self.transactions = transaction_repository
        self.counterparties = counterparty_repository

    def __enter__(self) -> "RepositoryUnitOfWork":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        self._for_each_repository(lambda repository: repository.commit())

    def rollback(self) -> None:
        def _rollback(repository) -> None:
            try:
                repository.rollback()
            except Exception:
                pass

        self._for_each_repository(_rollback)

    def _for_each_repository(self, action) -> None:
        unique_repositories = []
        seen = set()
        for repository in (self.transactions, self.counterparties):
            if repository is None:
                continue
            repo_id = id(repository)
            if repo_id in seen:
                continue
            seen.add(repo_id)
            unique_repositories.append(repository)

        for repository in unique_repositories:
            action(repository)
