from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from financeiro_kairo.presentation.main import FinanceiroKairoWindow


class FakeFacade:
    def accounts(self):
        return []

    def categories(self, *, include_inactive=False):
        return []

    def dashboard(self, start, end):
        return {
            "balance_cents": 0,
            "income_cents": 0,
            "expense_cents": 0,
            "net_cents": 0,
            "categories": [],
        }


def test_main_window_contains_recurring_expenses_module():
    app = QApplication.instance() or QApplication([])
    window = FinanceiroKairoWindow(FakeFacade())

    assert window.stack.count() == 10
    assert window.menu.item(6).text() == "Despesas recorrentes"

    window.close()
    app.processEvents()
