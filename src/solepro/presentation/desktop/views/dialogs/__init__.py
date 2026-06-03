"""
Диалоги десктопного приложения.
"""

from .counterparty_dialog import CounterpartyDialog
from .counterparty_manager_dialog import CounterpartyManagerDialog
from .settings_dialog import SettingsDialog
from .statistics_dialog import StatisticsDialog
from .transaction_dialog import TransactionDialog

__all__ = [
    "CounterpartyDialog",
    "CounterpartyManagerDialog",
    "SettingsDialog",
    "StatisticsDialog",
    "TransactionDialog",
]
