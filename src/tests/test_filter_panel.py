"""
Tests for desktop FilterPanel behavior.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from PyQt6.QtCore import QDate

from solepro.core.domain.enums.transaction_type import TransactionType
from solepro.presentation.desktop.views.widgets.filter_panel import FilterPanel

pytestmark = pytest.mark.ui


def test_apply_filters_builds_filter_with_search_type_and_amounts(qtbot):
    panel = FilterPanel()
    qtbot.add_widget(panel)

    panel.search_input.setText("  alpha  ")
    panel.type_combo.setCurrentIndex(1)  # income
    panel.min_amount_spin.setValue(10)
    panel.max_amount_spin.setValue(500)
    panel.start_date_edit.setDate(QDate(2026, 2, 1))
    panel.end_date_edit.setDate(QDate(2026, 2, 20))

    captured = {"value": None}
    panel.filter_changed.connect(lambda dto: captured.__setitem__("value", dto))
    panel.apply_filters()

    dto = captured["value"]
    assert dto is not None
    assert dto.show_all is False
    assert dto.search_query == "alpha"
    assert dto.transaction_type == TransactionType.INCOME
    assert dto.min_amount == Decimal("10")
    assert dto.max_amount == Decimal("500")
    assert dto.start_date == QDate(2026, 2, 1).toPyDate()
    assert dto.end_date == QDate(2026, 2, 20).toPyDate()


def test_apply_filters_tax_and_no_tax_branches(qtbot):
    panel = FilterPanel()
    qtbot.add_widget(panel)

    panel.type_combo.setCurrentIndex(4)  # tax
    panel.apply_filters()
    dto_tax = panel.get_current_filter()
    assert dto_tax.has_tax is True
    assert dto_tax.no_tax is None
    assert dto_tax.transaction_type is None

    panel.type_combo.setCurrentIndex(3)  # no_tax
    panel.apply_filters()
    dto_no_tax = panel.get_current_filter()
    assert dto_no_tax.no_tax is True
    assert dto_no_tax.has_tax is None
    assert dto_no_tax.transaction_type is None


def test_show_all_records_clears_filters_and_sets_show_all(qtbot):
    panel = FilterPanel()
    qtbot.add_widget(panel)
    panel.search_input.setText("query")
    panel.type_combo.setCurrentIndex(2)  # expense
    panel.min_amount_spin.setValue(50)
    panel.max_amount_spin.setValue(500)

    captured = {"value": None}
    panel.filter_changed.connect(lambda dto: captured.__setitem__("value", dto))

    panel.show_all_records()

    dto = captured["value"]
    assert dto is not None
    assert dto.show_all is True
    assert dto.search_query is None
    assert dto.transaction_type is None
    assert dto.min_amount is None
    assert dto.max_amount is None
    assert panel.search_input.text() == ""
    assert panel.type_combo.currentIndex() == 0
    assert panel.min_amount_spin.value() == 0
    assert panel.max_amount_spin.value() == 1000000000


def test_clear_filters_emits_signals_and_resets_state(qtbot):
    panel = FilterPanel()
    qtbot.add_widget(panel)

    panel.search_input.setText("x")
    panel.type_combo.setCurrentIndex(1)
    panel.min_amount_spin.setValue(20)
    panel.max_amount_spin.setValue(200)
    panel.page_size_combo.setCurrentIndex(0)
    panel.show_all = True

    events = {"cleared": 0, "changed": 0}
    panel.filter_cleared.connect(lambda: events.__setitem__("cleared", events["cleared"] + 1))
    panel.filter_changed.connect(lambda _dto: events.__setitem__("changed", events["changed"] + 1))

    panel.clear_filters()

    dto = panel.get_current_filter()
    assert events["cleared"] == 1
    assert events["changed"] == 0
    assert panel.show_all is False
    assert dto.show_all is False
    assert dto.search_query is None
    assert panel.page_size_combo.currentData() == 100


def test_pagination_emits_adjacent_pages_and_updates_buttons(qtbot):
    panel = FilterPanel()
    qtbot.add_widget(panel)
    captured = []
    panel.filter_changed.connect(captured.append)

    panel.set_page_info(page=1, total_pages=3, total_count=250)
    panel.next_page()

    assert captured[-1].page == 2
    panel.set_page_info(page=2, total_pages=3, total_count=250)
    panel.previous_page()
    assert captured[-1].page == 1
    assert panel.page_label.text() == "Страница 2 из 3"
