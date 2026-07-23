from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from financeiro_kairo.application.facade import ApplicationFacade
from financeiro_kairo.infrastructure.database.bootstrap import create_schema
from financeiro_kairo.presentation.app import MainWindow
from financeiro_kairo.presentation.recurring_expenses_page import RecurringExpensesPage


class FinanceiroKairoWindow(MainWindow):
    def __init__(self, facade: ApplicationFacade | None = None) -> None:
        super().__init__(facade)
        self.menu.insertItem(6, "Despesas recorrentes")
        self.stack.insertWidget(6, RecurringExpensesPage(self.facade))


def main() -> None:
    create_schema()
    app = QApplication(sys.argv)
    app.setApplicationName("Financeiro Kairo")
    app.setOrganizationName("Kairo")
    window = FinanceiroKairoWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
