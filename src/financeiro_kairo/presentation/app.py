from __future__ import annotations

import sys
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import select

from financeiro_kairo.application.schemas import AccountCreate, TransactionCreate
from financeiro_kairo.application.services.finance import FinanceService
from financeiro_kairo.application.services.reports import ReportService
from financeiro_kairo.domain.models import Account, AccountType, Transaction, TransactionType
from financeiro_kairo.infrastructure.database.bootstrap import create_schema
from financeiro_kairo.infrastructure.database.session import session_scope


class DashboardPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.layout = QVBoxLayout(self)
        title = QLabel("Visão geral")
        title.setObjectName("pageTitle")
        self.layout.addWidget(title)
        self.summary = QLabel()
        self.summary.setObjectName("summary")
        self.layout.addWidget(self.summary)
        self.layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        today = date.today()
        start = today.replace(day=1)
        with session_scope() as session:
            summary = ReportService(session).summary(start, today)
        self.summary.setText(
            f"Receitas: R$ {summary.income_cents / 100:,.2f}\n"
            f"Despesas: R$ {summary.expense_cents / 100:,.2f}\n"
            f"Resultado: R$ {summary.net_cents / 100:,.2f}"
        )


class TransactionsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Transações")
        title.setObjectName("pageTitle")
        add_button = QPushButton("Nova transação")
        add_button.clicked.connect(self.open_create_dialog)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_button)
        layout.addLayout(header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Data", "Descrição", "Tipo", "Valor", "Conta"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        with session_scope() as session:
            rows = session.scalars(
                select(Transaction).order_by(Transaction.occurred_on.desc(), Transaction.id.desc())
            ).all()
        self.table.setRowCount(len(rows))
        for row_index, transaction in enumerate(rows):
            values = [
                transaction.occurred_on.strftime("%d/%m/%Y"),
                transaction.description,
                transaction.transaction_type,
                f"R$ {transaction.amount_cents / 100:,.2f}",
                str(transaction.account_id),
            ]
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(value))

    def open_create_dialog(self) -> None:
        dialog = TransactionForm(self)
        if dialog.exec():
            self.refresh()


class TransactionForm(QMessageBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nova transação")
        self.setText("Preencha os dados do lançamento")
        container = QWidget()
        form = QFormLayout(container)
        self.description = QLineEdit()
        self.amount = QSpinBox()
        self.amount.setMaximum(100_000_000)
        self.amount.setSuffix(" centavos")
        self.kind = QComboBox()
        self.kind.addItem("Despesa", TransactionType.EXPENSE.value)
        self.kind.addItem("Receita", TransactionType.INCOME.value)
        self.account = QComboBox()
        self.occurred_on = QDateEdit()
        self.occurred_on.setCalendarPopup(True)
        self.occurred_on.setDate(date.today())
        with session_scope() as session:
            accounts = session.scalars(select(Account).where(Account.active.is_(True))).all()
        for account in accounts:
            self.account.addItem(account.name, account.id)
        form.addRow("Descrição", self.description)
        form.addRow("Valor", self.amount)
        form.addRow("Tipo", self.kind)
        form.addRow("Conta", self.account)
        form.addRow("Data", self.occurred_on)
        self.layout().addWidget(container, 1, 0, 1, self.layout().columnCount())
        self.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)

    def accept(self) -> None:
        if not self.description.text().strip() or self.amount.value() <= 0:
            QMessageBox.warning(self, "Dados inválidos", "Informe descrição e valor maior que zero.")
            return
        if self.account.currentData() is None:
            QMessageBox.warning(self, "Conta necessária", "Cadastre uma conta antes de lançar.")
            return
        with session_scope() as session:
            FinanceService(session).create_transaction(
                TransactionCreate(
                    transaction_type=self.kind.currentData(),
                    description=self.description.text().strip(),
                    amount_cents=self.amount.value(),
                    occurred_on=self.occurred_on.date().toPython(),
                    account_id=int(self.account.currentData()),
                )
            )
        super().accept()


class AccountsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Contas")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        form = QFormLayout()
        self.name = QLineEdit()
        self.type = QComboBox()
        for value in AccountType:
            self.type.addItem(value.value.replace("_", " ").title(), value.value)
        self.balance = QSpinBox()
        self.balance.setRange(-100_000_000, 100_000_000)
        button = QPushButton("Cadastrar conta")
        button.clicked.connect(self.create_account)
        form.addRow("Nome", self.name)
        form.addRow("Tipo", self.type)
        form.addRow("Saldo inicial (centavos)", self.balance)
        form.addRow(button)
        layout.addLayout(form)
        self.listing = QListWidget()
        layout.addWidget(self.listing)
        self.refresh()

    def create_account(self) -> None:
        if not self.name.text().strip():
            return
        with session_scope() as session:
            FinanceService(session).create_account(
                AccountCreate(
                    name=self.name.text().strip(),
                    account_type=self.type.currentData(),
                    initial_balance_cents=self.balance.value(),
                )
            )
        self.name.clear()
        self.refresh()

    def refresh(self) -> None:
        self.listing.clear()
        with session_scope() as session:
            accounts = session.scalars(select(Account).order_by(Account.name)).all()
            service = FinanceService(session)
            for account in accounts:
                balance = service.account_balance_cents(account.id)
                self.listing.addItem(f"{account.name} — R$ {balance / 100:,.2f}")


class PlaceholderPage(QWidget):
    def __init__(self, title_text: str, description: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel(title_text)
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        text = QLabel(description)
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Financeiro Kairo")
        self.resize(1280, 800)
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)

        self.menu = QListWidget()
        self.menu.setFixedWidth(230)
        labels = ["Visão geral", "Transações", "Contas", "Compras", "Planejamento", "Relatórios"]
        self.menu.addItems(labels)
        self.stack = QStackedWidget()
        self.dashboard = DashboardPage()
        self.transactions = TransactionsPage()
        self.accounts = AccountsPage()
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.transactions)
        self.stack.addWidget(self.accounts)
        self.stack.addWidget(
            PlaceholderPage("Compras", "Importação JSON, catálogo e comparação de preços disponíveis na camada de serviços.")
        )
        self.stack.addWidget(
            PlaceholderPage("Planejamento", "Orçamentos, metas, recorrências e parcelamentos estão disponíveis no domínio.")
        )
        self.stack.addWidget(
            PlaceholderPage("Relatórios", "Relatórios financeiros podem ser exportados para PDF e Excel.")
        )
        self.menu.currentRowChanged.connect(self.change_page)
        self.menu.setCurrentRow(0)
        layout.addWidget(self.menu)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f7f8fa; color: #18212f; }
            QListWidget { background: #172033; color: white; border: 0; padding: 12px; }
            QListWidget::item { padding: 12px; border-radius: 7px; }
            QListWidget::item:selected { background: #2f6fed; }
            QLabel#pageTitle { font-size: 24px; font-weight: 700; margin: 8px; }
            QLabel#summary { font-size: 18px; background: white; padding: 24px; border-radius: 10px; }
            QPushButton { background: #2f6fed; color: white; padding: 9px 15px; border: 0; border-radius: 7px; }
            QLineEdit, QComboBox, QSpinBox, QDateEdit { background: white; padding: 7px; border: 1px solid #ced5df; border-radius: 6px; }
            QTableWidget { background: white; border: 1px solid #e0e4ea; }
            """
        )

    def change_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        page = self.stack.currentWidget()
        refresh = getattr(page, "refresh", None)
        if callable(refresh):
            refresh()


def main() -> None:
    create_schema()
    app = QApplication(sys.argv)
    app.setApplicationName("Financeiro Kairo")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
