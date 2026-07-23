from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from financeiro_kairo.presentation.app import MainWindow


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


def test_main_window_starts_headless():
    app = QApplication.instance() or QApplication([])
    window = MainWindow(FakeFacade())
    assert window.windowTitle() == "Financeiro Kairo"
    assert window.stack.count() == 9
    assert window.menu.item(6).text() == "Gráficos"
    assert window.menu.item(8).text() == "Console SQL"
    window.close()
    app.processEvents()
