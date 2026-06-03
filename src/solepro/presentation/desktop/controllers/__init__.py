"""
Контроллеры для десктопного приложения.
"""

from .main_controller import MainController
from .coordinators import (
    TransactionCoordinator,
    CounterpartyCoordinator,
    TransactionCoordinatorProtocol,
    CounterpartyCoordinatorProtocol,
)

__all__ = [
    "MainController",
    "TransactionCoordinator",
    "CounterpartyCoordinator",
    "TransactionCoordinatorProtocol",
    "CounterpartyCoordinatorProtocol",
]
