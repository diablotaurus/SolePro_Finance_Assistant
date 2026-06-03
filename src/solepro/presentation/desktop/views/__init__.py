"""
Представления (виджеты) для десктопного приложения.
"""

from .widgets.transaction_table import TransactionTableView
from .widgets.filter_panel import FilterPanel
from .dialogs.transaction_dialog import TransactionDialog
from .dialogs.counterparty_dialog import CounterpartyDialog
from .dialogs.counterparty_manager_dialog import CounterpartyManagerDialog
from .dialogs.statistics_dialog import StatisticsDialog
from .dialogs.settings_dialog import SettingsDialog

__all__ = [
    "TransactionTableView",
    "FilterPanel",
    "TransactionDialog",
    "CounterpartyDialog",
    "CounterpartyManagerDialog",
    "StatisticsDialog",
    "SettingsDialog",
]
