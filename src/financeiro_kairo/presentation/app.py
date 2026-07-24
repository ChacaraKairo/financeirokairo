from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QDate, QPointF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from financeiro_kairo.application.facade import ApplicationFacade
from financeiro_kairo.application.services.sql_console import SqlConsoleService
from financeiro_kairo.domain.models import AccountType, CategoryKind, TransactionType
from financeiro_kairo.infrastructure.database.bootstrap import create_schema

_TRANSLATIONS = {
    "income": "Receita",
    "expense": "Despesa",
    "checking": "Conta corrente",
    "savings": "Poupança",
    "cash": "Dinheiro",
    "credit_card": "Cartão de crédito",
    "investment": "Investimento",
    "wallet": "Carteira",
    "active": "Ativa",
    "inactive": "Inativa",
    "pending": "Pendente",
    "paid": "Paga",
    "cancelled": "Cancelada",
    "completed": "Concluída",
    "review": "Revisão necessária",
    "manual": "Manual",
    "api": "API",
    "mercado-json": "JSON de mercado",
    "csv-convertido": "CSV convertido",
}


def translate(value: Any) -> str:
    text = str(value)
    return _TRANSLATIONS.get(text.casefold(), text.replace("_", " ").capitalize())


def money(cents: int) -> str:
    value = cents / 100
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def table(headers: list[str]) -> QTableWidget:
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.horizontalHeader().setStretchLastSection(True)
    widget.setAlternatingRowColors(True)
    widget.setSelectionBehavior(QTableWidget.SelectRows)
    widget.setEditTriggers(QTableWidget.NoEditTriggers)
    return widget


class FormDialog(QDialog):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.form = QFormLayout(self)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Save).setText("Salvar")
        self.buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def finish(self) -> None:
        self.form.addRow(self.buttons)


def select_combo_value(combo: QComboBox, value: object) -> None:
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)


def confirm_delete(parent: QWidget, title: str, message: str) -> bool:
    answer = QMessageBox.question(parent, title, message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    return answer == QMessageBox.Yes


class TransactionDialog(FormDialog):
    def __init__(
        self,
        facade: ApplicationFacade,
        item: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Editar transação" if item else "Nova transação", parent)
        self.facade = facade
        self.item = item
        self.description = QLineEdit()
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0.01, 10_000_000)
        self.amount.setDecimals(2)
        self.amount.setPrefix("R$ ")
        self.kind = QComboBox()
        self.kind.addItem("Despesa", TransactionType.EXPENSE.value)
        self.kind.addItem("Receita", TransactionType.INCOME.value)
        self.account = QComboBox()
        for account in facade.accounts():
            if account["active"]:
                self.account.addItem(account["name"], account["id"])
        self.category = QComboBox()
        self.category.addItem("Sem categoria", None)
        for category in facade.categories():
            self.category.addItem(category["name"], category["id"])
        self.occurred_on = QDateEdit(QDate.currentDate())
        self.occurred_on.setCalendarPopup(True)
        self.form.addRow("Descrição", self.description)
        self.form.addRow("Valor", self.amount)
        self.form.addRow("Tipo", self.kind)
        self.form.addRow("Conta", self.account)
        self.form.addRow("Categoria", self.category)
        self.form.addRow("Data", self.occurred_on)
        self.finish()
        if item:
            self.description.setText(item["description"])
            self.amount.setValue(item["amount_cents"] / 100)
            select_combo_value(self.kind, item["type"])
            select_combo_value(self.account, item["account_id"])
            select_combo_value(self.category, item["category_id"])
            self.occurred_on.setDate(QDate(item["date"].year, item["date"].month, item["date"].day))

    def accept(self) -> None:
        if len(self.description.text().strip()) < 2 or self.account.currentData() is None:
            QMessageBox.warning(self, "Dados inválidos", "Informe uma descrição e uma conta válida.")
            return
        payload = {
            "transaction_type": str(self.kind.currentData()),
            "description": self.description.text().strip(),
            "amount_cents": round(self.amount.value() * 100),
            "occurred_on": self.occurred_on.date().toPython(),
            "account_id": int(self.account.currentData()),
            "category_id": self.category.currentData(),
        }
        if self.item:
            self.facade.update_transaction(self.item["id"], **payload)
        else:
            self.facade.create_transaction(**payload)
        super().accept()


class AccountDialog(FormDialog):
    def __init__(
        self,
        facade: ApplicationFacade,
        item: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Editar conta" if item else "Nova conta", parent)
        self.facade = facade
        self.item = item
        self.name = QLineEdit()
        self.kind = QComboBox()
        for account_type in AccountType:
            self.kind.addItem(translate(account_type.value), account_type.value)
        self.balance = QDoubleSpinBox()
        self.balance.setRange(-10_000_000, 10_000_000)
        self.balance.setPrefix("R$ ")
        self.active = QCheckBox("Conta ativa")
        self.active.setChecked(True)
        self.form.addRow("Nome", self.name)
        self.form.addRow("Tipo", self.kind)
        self.form.addRow("Saldo inicial", self.balance)
        self.form.addRow("Situação", self.active)
        self.finish()
        if item:
            self.name.setText(item["name"])
            select_combo_value(self.kind, item["type"])
            self.balance.setValue(item["initial_balance_cents"] / 100)
            self.active.setChecked(item["active"])

    def accept(self) -> None:
        if len(self.name.text().strip()) < 2:
            QMessageBox.warning(self, "Nome inválido", "Informe um nome para a conta.")
            return
        payload = {
            "name": self.name.text().strip(),
            "account_type": str(self.kind.currentData()),
            "initial_balance_cents": round(self.balance.value() * 100),
        }
        if self.item:
            self.facade.update_account(self.item["id"], **payload, active=self.active.isChecked())
        else:
            self.facade.create_account(**payload)
        super().accept()


class CategoryDialog(FormDialog):
    def __init__(
        self,
        facade: ApplicationFacade,
        item: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Editar categoria" if item else "Nova categoria", parent)
        self.facade = facade
        self.item = item
        self.name = QLineEdit()
        self.kind = QComboBox()
        for category_kind in CategoryKind:
            self.kind.addItem(translate(category_kind.value), category_kind.value)
        self.parent_category = QComboBox()
        self.parent_category.addItem("Nenhuma", None)
        for category in facade.categories():
            if self.item is None or category["id"] != self.item["id"]:
                self.parent_category.addItem(category["name"], category["id"])
        self.active = QCheckBox("Categoria ativa")
        self.active.setChecked(True)
        self.form.addRow("Nome", self.name)
        self.form.addRow("Tipo", self.kind)
        self.form.addRow("Categoria superior", self.parent_category)
        self.form.addRow("Situação", self.active)
        self.finish()
        if item:
            self.name.setText(item["name"])
            select_combo_value(self.kind, item["kind"])
            select_combo_value(self.parent_category, item["parent_id"])
            self.active.setChecked(item["active"])

    def accept(self) -> None:
        try:
            payload = {
                "name": self.name.text(),
                "kind": str(self.kind.currentData()),
                "parent_id": self.parent_category.currentData(),
            }
            if self.item:
                self.facade.update_category(self.item["id"], **payload, active=self.active.isChecked())
            else:
                self.facade.create_category(**payload)
        except (ValueError, LookupError) as error:
            QMessageBox.warning(self, "Categoria inválida", str(error))
            return
        super().accept()


class PurchaseDialog(FormDialog):
    def __init__(
        self,
        facade: ApplicationFacade,
        item: dict[str, Any],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Editar compra", parent)
        self.facade = facade
        self.item = item
        self.purchased_on = QDateEdit(QDate(item["date"].year, item["date"].month, item["date"].day))
        self.purchased_on.setCalendarPopup(True)
        self.merchant = QLineEdit(item["merchant"])
        self.total = QDoubleSpinBox()
        self.total.setRange(0, 10_000_000)
        self.total.setDecimals(2)
        self.total.setPrefix("R$ ")
        self.total.setValue(item["total_cents"] / 100)
        self.source = QLineEdit(str(item["source"]))
        self.document = QLineEdit(item["document_number"] or "")
        self.account = QComboBox()
        self.account.addItem("Sem conta", None)
        for account in facade.accounts():
            if account["active"]:
                self.account.addItem(account["name"], account["id"])
        select_combo_value(self.account, item["account_id"])
        self.form.addRow("Data", self.purchased_on)
        self.form.addRow("Estabelecimento", self.merchant)
        self.form.addRow("Total", self.total)
        self.form.addRow("Origem", self.source)
        self.form.addRow("Documento", self.document)
        self.form.addRow("Conta", self.account)
        self.finish()

    def accept(self) -> None:
        try:
            self.facade.update_purchase(
                self.item["id"],
                purchased_on=self.purchased_on.date().toPython(),
                merchant_name=self.merchant.text(),
                account_id=self.account.currentData(),
                total_cents=round(self.total.value() * 100),
                source_type=self.source.text(),
                document_number=self.document.text(),
            )
        except (ValueError, LookupError) as error:
            QMessageBox.warning(self, "Compra inválida", str(error))
            return
        super().accept()


class DashboardPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        layout = QVBoxLayout(self)
        title = QLabel("Visão geral")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.summary = QLabel()
        self.summary.setObjectName("summary")
        layout.addWidget(self.summary)
        self.categories = table(["Categoria", "Despesas"])
        layout.addWidget(self.categories)
        invoice_title = QLabel("Fatura do cartão de crédito")
        invoice_title.setObjectName("sectionTitle")
        layout.addWidget(invoice_title)
        self.invoice_summary = QLabel()
        self.invoice_summary.setObjectName("summary")
        layout.addWidget(self.invoice_summary)
        self.invoice_cards = table(["Cartão", "Total no mês"])
        layout.addWidget(self.invoice_cards)
        self.invoice_transactions = table(["Data", "Cartão", "Descrição", "Valor"])
        layout.addWidget(self.invoice_transactions)

    def refresh(self) -> None:
        today = date.today()
        result = self.facade.dashboard(today.replace(day=1), today)
        self.summary.setText(
            f"Saldo consolidado: {money(result['balance_cents'])}\n"
            f"Receitas do mês: {money(result['income_cents'])}\n"
            f"Despesas do mês: {money(result['expense_cents'])}\n"
            f"Resultado: {money(result['net_cents'])}"
        )
        rows = result["categories"]
        self.categories.setRowCount(len(rows))
        for index, (name, amount) in enumerate(rows):
            self.categories.setItem(index, 0, QTableWidgetItem(name))
            self.categories.setItem(index, 1, QTableWidgetItem(money(amount)))
        invoice = result.get("credit_card_invoice", {"total_cents": 0, "cards": [], "transactions": []})
        self.invoice_summary.setText(f"Fatura atual do mês: {money(invoice['total_cents'])}")
        cards = invoice["cards"]
        self.invoice_cards.setRowCount(len(cards))
        for index, item in enumerate(cards):
            self.invoice_cards.setItem(index, 0, QTableWidgetItem(item["account_name"]))
            self.invoice_cards.setItem(index, 1, QTableWidgetItem(money(item["amount_cents"])))
        transactions = invoice["transactions"]
        self.invoice_transactions.setRowCount(len(transactions))
        for index, item in enumerate(transactions):
            values = [
                item["date"].strftime("%d/%m/%Y"),
                item["account_name"],
                item["description"],
                money(item["amount_cents"]),
            ]
            for column, value in enumerate(values):
                self.invoice_transactions.setItem(index, column, QTableWidgetItem(value))


class TransactionsPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        self.rows: list[dict[str, Any]] = []
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Transações")
        title.setObjectName("pageTitle")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar pela descrição")
        self.search.returnPressed.connect(self.refresh)
        add = QPushButton("Nova transação")
        add.clicked.connect(self.create)
        edit = QPushButton("Editar")
        edit.clicked.connect(self.edit)
        delete = QPushButton("Apagar")
        delete.clicked.connect(self.delete)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search)
        header.addWidget(add)
        header.addWidget(edit)
        header.addWidget(delete)
        layout.addLayout(header)
        self.grid = table(["Data", "Descrição", "Tipo", "Valor", "Conta", "Situação"])
        layout.addWidget(self.grid)

    def create(self) -> None:
        if TransactionDialog(self.facade, parent=self).exec():
            self.refresh()

    def edit(self) -> None:
        row = self.grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Editar", "Selecione uma transação.")
            return
        if TransactionDialog(self.facade, self.rows[row], self).exec():
            self.refresh()

    def delete(self) -> None:
        row = self.grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Apagar", "Selecione uma transação.")
            return
        if not confirm_delete(self, "Apagar transação", "Deseja apagar a transação selecionada?"):
            return
        try:
            self.facade.delete_transaction(self.rows[row]["id"])
        except Exception as error:
            QMessageBox.warning(self, "Não foi possível apagar", str(error))
            return
        self.refresh()

    def refresh(self) -> None:
        self.rows, _ = self.facade.transactions(search_text=self.search.text().strip() or None)
        self.grid.setRowCount(len(self.rows))
        for index, item in enumerate(self.rows):
            values = [
                item["date"].strftime("%d/%m/%Y"),
                item["description"],
                translate(item["type"]),
                money(item["amount_cents"]),
                str(item["account_id"]),
                translate(item["status"]),
            ]
            for column, value in enumerate(values):
                self.grid.setItem(index, column, QTableWidgetItem(value))


class AccountsPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        self.rows: list[dict[str, Any]] = []
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Contas")
        title.setObjectName("pageTitle")
        add = QPushButton("Nova conta")
        add.clicked.connect(self.create)
        edit = QPushButton("Editar")
        edit.clicked.connect(self.edit)
        delete = QPushButton("Apagar")
        delete.clicked.connect(self.delete)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add)
        header.addWidget(edit)
        header.addWidget(delete)
        layout.addLayout(header)
        self.grid = table(["Conta", "Tipo", "Saldo", "Situação"])
        layout.addWidget(self.grid)

    def create(self) -> None:
        if AccountDialog(self.facade, parent=self).exec():
            self.refresh()

    def edit(self) -> None:
        row = self.grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Editar", "Selecione uma conta.")
            return
        if AccountDialog(self.facade, self.rows[row], self).exec():
            self.refresh()

    def delete(self) -> None:
        row = self.grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Apagar", "Selecione uma conta.")
            return
        if not confirm_delete(self, "Apagar conta", "Deseja apagar a conta selecionada?"):
            return
        try:
            self.facade.delete_account(self.rows[row]["id"])
        except Exception as error:
            QMessageBox.warning(self, "Não foi possível apagar", str(error))
            return
        self.refresh()

    def refresh(self) -> None:
        self.rows = self.facade.accounts()
        self.grid.setRowCount(len(self.rows))
        for index, item in enumerate(self.rows):
            values = [
                item["name"],
                translate(item["type"]),
                money(item["balance_cents"]),
                "Ativa" if item["active"] else "Arquivada",
            ]
            for column, value in enumerate(values):
                self.grid.setItem(index, column, QTableWidgetItem(value))


class CategoriesPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        self.rows: list[dict[str, Any]] = []
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Categorias")
        title.setObjectName("pageTitle")
        add = QPushButton("Nova categoria")
        add.clicked.connect(self.create)
        edit = QPushButton("Editar")
        edit.clicked.connect(self.edit)
        archive = QPushButton("Arquivar selecionada")
        archive.clicked.connect(self.archive)
        delete = QPushButton("Apagar")
        delete.clicked.connect(self.delete)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add)
        header.addWidget(edit)
        header.addWidget(archive)
        header.addWidget(delete)
        layout.addLayout(header)
        self.grid = table(["Nome", "Tipo", "Categoria superior", "Situação"])
        layout.addWidget(self.grid)

    def create(self) -> None:
        if CategoryDialog(self.facade, parent=self).exec():
            self.refresh()

    def edit(self) -> None:
        row = self.grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Editar", "Selecione uma categoria.")
            return
        if CategoryDialog(self.facade, self.rows[row], self).exec():
            self.refresh()

    def archive(self) -> None:
        row = self.grid.currentRow()
        if row >= 0:
            self.facade.archive_category(self.rows[row]["id"])
            self.refresh()

    def delete(self) -> None:
        row = self.grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Apagar", "Selecione uma categoria.")
            return
        if not confirm_delete(self, "Apagar categoria", "Deseja apagar a categoria selecionada?"):
            return
        try:
            self.facade.delete_category(self.rows[row]["id"])
        except Exception as error:
            QMessageBox.warning(self, "Não foi possível apagar", str(error))
            return
        self.refresh()

    def refresh(self) -> None:
        self.rows = self.facade.categories(include_inactive=True)
        names = {item["id"]: item["name"] for item in self.rows}
        self.grid.setRowCount(len(self.rows))
        for index, item in enumerate(self.rows):
            values = [
                item["name"],
                translate(item["kind"]),
                names.get(item["parent_id"], "—"),
                "Ativa" if item["active"] else "Arquivada",
            ]
            for column, value in enumerate(values):
                self.grid.setItem(index, column, QTableWidgetItem(value))


class PurchasesPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        self.rows: list[dict[str, Any]] = []
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Compras e importações")
        title.setObjectName("pageTitle")
        button = QPushButton("Importar arquivo JSON")
        button.clicked.connect(self.import_json)
        edit = QPushButton("Editar")
        edit.clicked.connect(self.edit)
        delete = QPushButton("Apagar")
        delete.clicked.connect(self.delete)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(button)
        header.addWidget(edit)
        header.addWidget(delete)
        layout.addLayout(header)
        layout.addWidget(QLabel("O arquivo é validado e importações repetidas são bloqueadas."))
        self.grid = table(["Data", "Estabelecimento", "Itens", "Total", "Origem"])
        layout.addWidget(self.grid)

    def import_json(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Selecionar compra", "", "Arquivo JSON (*.json)")
        if not filename:
            return
        try:
            purchase_id = self.facade.import_purchase(Path(filename))
        except Exception as error:
            QMessageBox.critical(self, "Falha na importação", str(error))
            return
        QMessageBox.information(self, "Importação concluída", f"Compra nº {purchase_id} importada com sucesso.")
        self.refresh()

    def edit(self) -> None:
        row = self.grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Editar", "Selecione uma compra.")
            return
        if PurchaseDialog(self.facade, self.rows[row], self).exec():
            self.refresh()

    def delete(self) -> None:
        row = self.grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Apagar", "Selecione uma compra.")
            return
        if not confirm_delete(self, "Apagar compra", "Deseja apagar a compra selecionada?"):
            return
        try:
            self.facade.delete_purchase(self.rows[row]["id"])
        except Exception as error:
            QMessageBox.warning(self, "Não foi possível apagar", str(error))
            return
        self.refresh()

    def refresh(self) -> None:
        self.rows = self.facade.purchases()
        self.grid.setRowCount(len(self.rows))
        for index, item in enumerate(self.rows):
            values = [
                item["date"].strftime("%d/%m/%Y"),
                item["merchant"],
                str(item["items"]),
                money(item["total_cents"]),
                translate(item["source"]),
            ]
            for column, value in enumerate(values):
                self.grid.setItem(index, column, QTableWidgetItem(value))


class BudgetDialog(FormDialog):
    def __init__(self, item: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__("Editar orçamento", parent)
        self.name = QLineEdit(item["name"])
        self.start = QDateEdit(QDate(item["start"].year, item["start"].month, item["start"].day))
        self.start.setCalendarPopup(True)
        self.end = QDateEdit(QDate(item["end"].year, item["end"].month, item["end"].day))
        self.end.setCalendarPopup(True)
        self.limit = QDoubleSpinBox()
        self.limit.setRange(0, 10_000_000)
        self.limit.setDecimals(2)
        self.limit.setPrefix("R$ ")
        self.limit.setValue(item["limit_cents"] / 100)
        self.active = QCheckBox("Orçamento ativo")
        self.active.setChecked(item.get("active", True))
        self.form.addRow("Nome", self.name)
        self.form.addRow("Início", self.start)
        self.form.addRow("Fim", self.end)
        self.form.addRow("Limite", self.limit)
        self.form.addRow("Situação", self.active)
        self.finish()

    def payload(self) -> dict[str, Any]:
        return {
            "name": self.name.text(),
            "period_start": self.start.date().toPython(),
            "period_end": self.end.date().toPython(),
            "limit_cents": round(self.limit.value() * 100),
            "active": self.active.isChecked(),
        }


class GoalDialog(FormDialog):
    def __init__(self, item: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__("Editar meta", parent)
        self.name = QLineEdit(item["name"])
        self.current = QDoubleSpinBox()
        self.current.setRange(0, 100_000_000)
        self.current.setDecimals(2)
        self.current.setPrefix("R$ ")
        self.current.setValue(item["current_cents"] / 100)
        self.target = QDoubleSpinBox()
        self.target.setRange(0.01, 100_000_000)
        self.target.setDecimals(2)
        self.target.setPrefix("R$ ")
        self.target.setValue(item["target_cents"] / 100)
        self.active = QCheckBox("Meta ativa")
        self.active.setChecked(item.get("active", True))
        self.form.addRow("Nome", self.name)
        self.form.addRow("Atual", self.current)
        self.form.addRow("Alvo", self.target)
        self.form.addRow("Situação", self.active)
        self.finish()

    def payload(self) -> dict[str, Any]:
        return {
            "name": self.name.text(),
            "current_cents": round(self.current.value() * 100),
            "target_cents": round(self.target.value() * 100),
            "active": self.active.isChecked(),
        }


class InstallmentDialog(FormDialog):
    def __init__(self, item: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__("Editar parcela", parent)
        self.due_date = QDateEdit(QDate(item["due_date"].year, item["due_date"].month, item["due_date"].day))
        self.due_date.setCalendarPopup(True)
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0.01, 10_000_000)
        self.amount.setDecimals(2)
        self.amount.setPrefix("R$ ")
        self.amount.setValue(item["amount_cents"] / 100)
        self.form.addRow("Vencimento", self.due_date)
        self.form.addRow("Valor", self.amount)
        self.finish()

    def payload(self) -> dict[str, Any]:
        return {
            "due_date": self.due_date.date().toPython(),
            "amount_cents": round(self.amount.value() * 100),
        }


class PlanningPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        self.goal_ids: list[int] = []
        self.installment_ids: list[int] = []
        layout = QVBoxLayout(self)
        title = QLabel("Planejamento")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._build_budgets()
        self._build_goals()
        self._build_installments()

    def _build_budgets(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QHBoxLayout()
        self.budget_name = QLineEdit()
        self.budget_name.setPlaceholderText("Nome do orçamento")
        self.budget_limit = QDoubleSpinBox()
        self.budget_limit.setRange(0.01, 10_000_000)
        self.budget_limit.setPrefix("R$ ")
        add = QPushButton("Criar orçamento mensal")
        add.clicked.connect(self.create_budget)
        edit = QPushButton("Editar")
        edit.clicked.connect(self.edit_budget)
        delete = QPushButton("Apagar")
        delete.clicked.connect(self.delete_budget)
        form.addWidget(self.budget_name)
        form.addWidget(self.budget_limit)
        form.addWidget(add)
        form.addWidget(edit)
        form.addWidget(delete)
        layout.addLayout(form)
        self.budget_grid = table(["Orçamento", "Período", "Limite", "Realizado", "Uso"])
        layout.addWidget(self.budget_grid)
        self.tabs.addTab(page, "Orçamentos")

    def _build_goals(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QHBoxLayout()
        self.goal_name = QLineEdit()
        self.goal_name.setPlaceholderText("Nome da meta")
        self.goal_target = QDoubleSpinBox()
        self.goal_target.setRange(0.01, 100_000_000)
        self.goal_target.setPrefix("R$ ")
        add = QPushButton("Criar meta")
        add.clicked.connect(self.create_goal)
        edit = QPushButton("Editar")
        edit.clicked.connect(self.edit_goal)
        delete = QPushButton("Apagar")
        delete.clicked.connect(self.delete_goal)
        contribute = QPushButton("Adicionar R$ 100 à selecionada")
        contribute.clicked.connect(self.contribute_goal)
        form.addWidget(self.goal_name)
        form.addWidget(self.goal_target)
        form.addWidget(add)
        form.addWidget(edit)
        form.addWidget(delete)
        form.addWidget(contribute)
        layout.addLayout(form)
        self.goal_grid = table(["Meta", "Atual", "Alvo", "Progresso"])
        layout.addWidget(self.goal_grid)
        self.tabs.addTab(page, "Metas")

    def _build_installments(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        form = QHBoxLayout()
        self.plan_description = QLineEdit()
        self.plan_description.setPlaceholderText("Descrição")
        self.plan_total = QDoubleSpinBox()
        self.plan_total.setRange(0.01, 10_000_000)
        self.plan_total.setPrefix("R$ ")
        self.plan_count = QSpinBox()
        self.plan_count.setRange(1, 120)
        self.plan_account = QComboBox()
        for item in self.facade.accounts():
            if item["active"]:
                self.plan_account.addItem(item["name"], item["id"])
        add = QPushButton("Criar parcelamento")
        add.clicked.connect(self.create_installment)
        edit = QPushButton("Editar parcela")
        edit.clicked.connect(self.edit_installment)
        delete = QPushButton("Apagar parcelamento")
        delete.clicked.connect(self.delete_installment_plan)
        pay = QPushButton("Pagar parcela selecionada")
        pay.clicked.connect(self.pay_installment)
        for widget in [
            self.plan_description,
            self.plan_total,
            self.plan_count,
            self.plan_account,
            add,
            edit,
            delete,
            pay,
        ]:
            form.addWidget(widget)
        layout.addLayout(form)
        self.installment_grid = table(["Descrição", "Parcela", "Vencimento", "Valor", "Situação"])
        layout.addWidget(self.installment_grid)
        self.tabs.addTab(page, "Parcelas")

    def create_budget(self) -> None:
        today = date.today()
        if len(self.budget_name.text().strip()) < 2:
            return
        end = date(today.year, today.month, QDate(today.year, today.month, 1).daysInMonth())
        self.facade.create_budget(
            name=self.budget_name.text().strip(),
            period_start=today.replace(day=1),
            period_end=end,
            limit_cents=round(self.budget_limit.value() * 100),
        )
        self.budget_name.clear()
        self.refresh()

    def edit_budget(self) -> None:
        row = self.budget_grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Editar", "Selecione um orçamento.")
            return
        item = self.budgets()[row]
        dialog = BudgetDialog(item, self)
        if not dialog.exec():
            return
        try:
            self.facade.update_budget(item["id"], **dialog.payload())
        except (ValueError, LookupError) as error:
            QMessageBox.warning(self, "Orçamento inválido", str(error))
            return
        self.refresh()

    def delete_budget(self) -> None:
        row = self.budget_grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Apagar", "Selecione um orçamento.")
            return
        item = self.budgets()[row]
        if not confirm_delete(self, "Apagar orçamento", "Deseja apagar o orçamento selecionado?"):
            return
        try:
            self.facade.delete_budget(item["id"])
        except Exception as error:
            QMessageBox.warning(self, "Não foi possível apagar", str(error))
            return
        self.refresh()

    def create_goal(self) -> None:
        if len(self.goal_name.text().strip()) < 2:
            return
        self.facade.create_goal(name=self.goal_name.text().strip(), target_cents=round(self.goal_target.value() * 100))
        self.goal_name.clear()
        self.refresh()

    def edit_goal(self) -> None:
        row = self.goal_grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Editar", "Selecione uma meta.")
            return
        item = self.goals()[row]
        dialog = GoalDialog(item, self)
        if not dialog.exec():
            return
        try:
            self.facade.update_goal(item["id"], **dialog.payload())
        except (ValueError, LookupError) as error:
            QMessageBox.warning(self, "Meta inválida", str(error))
            return
        self.refresh()

    def delete_goal(self) -> None:
        row = self.goal_grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Apagar", "Selecione uma meta.")
            return
        item = self.goals()[row]
        if not confirm_delete(self, "Apagar meta", "Deseja apagar a meta selecionada?"):
            return
        try:
            self.facade.delete_goal(item["id"])
        except Exception as error:
            QMessageBox.warning(self, "Não foi possível apagar", str(error))
            return
        self.refresh()

    def contribute_goal(self) -> None:
        row = self.goal_grid.currentRow()
        if row >= 0:
            self.facade.contribute_goal(self.goal_ids[row], 10_000, date.today())
            self.refresh()

    def create_installment(self) -> None:
        if self.plan_account.currentData() is None or len(self.plan_description.text().strip()) < 2:
            return
        self.facade.create_installment_plan(
            description=self.plan_description.text().strip(),
            total_cents=round(self.plan_total.value() * 100),
            installment_count=self.plan_count.value(),
            account_id=int(self.plan_account.currentData()),
            first_due_date=date.today(),
        )
        self.plan_description.clear()
        self.refresh()

    def edit_installment(self) -> None:
        row = self.installment_grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Editar", "Selecione uma parcela.")
            return
        item = self.installments()[row]
        dialog = InstallmentDialog(item, self)
        if not dialog.exec():
            return
        try:
            self.facade.update_installment(item["id"], **dialog.payload())
        except (ValueError, LookupError) as error:
            QMessageBox.warning(self, "Parcela inválida", str(error))
            return
        self.refresh()

    def delete_installment_plan(self) -> None:
        row = self.installment_grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Apagar", "Selecione uma parcela do parcelamento.")
            return
        item = self.installments()[row]
        if not confirm_delete(
            self,
            "Apagar parcelamento",
            "Deseja apagar todo o parcelamento da parcela selecionada?",
        ):
            return
        try:
            self.facade.delete_installment_plan(item["plan_id"])
        except Exception as error:
            QMessageBox.warning(self, "Não foi possível apagar", str(error))
            return
        self.refresh()

    def pay_installment(self) -> None:
        row = self.installment_grid.currentRow()
        if row >= 0:
            try:
                self.facade.pay_installment(self.installment_ids[row], date.today())
            except ValueError as error:
                QMessageBox.warning(self, "Parcela", str(error))
            self.refresh()

    def budgets(self) -> list[dict[str, Any]]:
        return self.facade.budgets()

    def goals(self) -> list[dict[str, Any]]:
        return self.facade.goals()

    def installments(self) -> list[dict[str, Any]]:
        return self.facade.installments()

    def refresh(self) -> None:
        budgets = self.budgets()
        self.budget_grid.setRowCount(len(budgets))
        for index, item in enumerate(budgets):
            percentage = 0 if item["limit_cents"] == 0 else min(999, round(item["used_cents"] * 100 / item["limit_cents"]))
            values = [item["name"], f"{item['start']:%d/%m/%Y} a {item['end']:%d/%m/%Y}", money(item["limit_cents"]), money(item["used_cents"]), f"{percentage}%"]
            for column, value in enumerate(values):
                self.budget_grid.setItem(index, column, QTableWidgetItem(value))
        goals = self.goals()
        self.goal_ids = [item["id"] for item in goals]
        self.goal_grid.setRowCount(len(goals))
        for index, item in enumerate(goals):
            percentage = min(100, round(item["current_cents"] * 100 / item["target_cents"]))
            values = [item["name"], money(item["current_cents"]), money(item["target_cents"]), f"{percentage}%"]
            for column, value in enumerate(values):
                self.goal_grid.setItem(index, column, QTableWidgetItem(value))
        installments = self.installments()
        self.installment_ids = [item["id"] for item in installments]
        self.installment_grid.setRowCount(len(installments))
        for index, item in enumerate(installments):
            values = [item["description"], f"{item['number']}/{item['count']}", item["due_date"].strftime("%d/%m/%Y"), money(item["amount_cents"]), "Paga" if item["paid"] else "Pendente"]
            for column, value in enumerate(values):
                self.installment_grid.setItem(index, column, QTableWidgetItem(value))


class ChartsPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        layout = QVBoxLayout(self)
        title = QLabel("Gráficos")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Tipo do gráfico:"))
        self.chart_type = QComboBox()
        self.chart_type.addItems(["Pizza", "Barras", "Linha"])
        self.chart_type.currentTextChanged.connect(self.refresh)
        controls.addWidget(self.chart_type)
        controls.addStretch()
        layout.addLayout(controls)
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.chart_view, 1)
        self.note = QLabel("Os valores representam as despesas do mês agrupadas por categoria.")
        layout.addWidget(self.note)

    def refresh(self) -> None:
        today = date.today()
        data = self.facade.dashboard(today.replace(day=1), today)["categories"]
        chart = QChart()
        chart.setTitle(f"Despesas por categoria — {today:%m/%Y}")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        kind = self.chart_type.currentText()
        if not data:
            chart.setTitle("Não há despesas no período selecionado")
        elif kind == "Pizza":
            series = QPieSeries()
            for name, amount in data:
                series.append(name, amount / 100)
            series.setLabelsVisible(True)
            chart.addSeries(series)
        elif kind == "Barras":
            values = QBarSet("Despesas em reais")
            values.append([amount / 100 for _, amount in data])
            series = QBarSeries()
            series.append(values)
            chart.addSeries(series)
            axis_x = QBarCategoryAxis()
            axis_x.append([name for name, _ in data])
            axis_y = QValueAxis()
            axis_y.setTitleText("Valor em reais")
            axis_y.setLabelFormat("%.2f")
            chart.addAxis(axis_x, Qt.AlignBottom)
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
        else:
            series = QLineSeries()
            series.setName("Despesas em reais")
            for index, (_, amount) in enumerate(data):
                series.append(QPointF(index, amount / 100))
            chart.addSeries(series)
            axis_x = QBarCategoryAxis()
            axis_x.append([name for name, _ in data])
            axis_y = QValueAxis()
            axis_y.setTitleText("Valor em reais")
            axis_y.setLabelFormat("%.2f")
            chart.addAxis(axis_x, Qt.AlignBottom)
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
        self.chart_view.setChart(chart)


class ReportsPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        layout = QVBoxLayout(self)
        title = QLabel("Relatórios e segurança")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.period = QLabel()
        layout.addWidget(self.period)
        actions = QHBoxLayout()
        for label, handler in [
            ("Exportar para Excel", self.export_excel),
            ("Exportar para PDF", self.export_pdf),
            ("Criar cópia de segurança", self.backup),
            ("Restaurar cópia de segurança", self.restore),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.summary = QLabel()
        self.summary.setObjectName("summary")
        layout.addWidget(self.summary)
        self.category_grid = table(["Categoria", "Total"])
        layout.addWidget(self.category_grid)

    def range(self) -> tuple[date, date]:
        today = date.today()
        return today.replace(day=1), today

    def export_excel(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar relatório", "transacoes.xlsx", "Planilha Excel (*.xlsx)")
        if filename:
            start, end = self.range()
            self.facade.export_excel(Path(filename), start, end)
            QMessageBox.information(self, "Relatório", "Planilha criada com sucesso.")

    def export_pdf(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar relatório", "relatorio.pdf", "Documento PDF (*.pdf)")
        if filename:
            start, end = self.range()
            self.facade.export_pdf(Path(filename), start, end)
            QMessageBox.information(self, "Relatório", "Documento PDF criado com sucesso.")

    def backup(self) -> None:
        try:
            path = self.facade.create_backup()
        except Exception as error:
            QMessageBox.critical(self, "Cópia de segurança", str(error))
            return
        QMessageBox.information(self, "Cópia de segurança", f"Arquivo criado em:\n{path}")

    def restore(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Restaurar cópia", "", "Banco SQLite (*.sqlite3 *.db)")
        if not filename:
            return
        answer = QMessageBox.question(self, "Confirmar restauração", "A base atual será preservada. Deseja continuar?")
        if answer != QMessageBox.Yes:
            return
        try:
            safety = self.facade.restore_backup(Path(filename))
        except Exception as error:
            QMessageBox.critical(self, "Restauração", str(error))
            return
        QMessageBox.information(self, "Restauração concluída", f"Base anterior preservada em:\n{safety}\nReinicie o aplicativo.")

    def refresh(self) -> None:
        start, end = self.range()
        result = self.facade.dashboard(start, end)
        self.period.setText(f"Período atual: {start:%d/%m/%Y} a {end:%d/%m/%Y}")
        self.summary.setText(f"Receitas: {money(result['income_cents'])} | Despesas: {money(result['expense_cents'])} | Resultado: {money(result['net_cents'])}")
        rows = result["categories"]
        self.category_grid.setRowCount(len(rows))
        for index, (name, amount) in enumerate(rows):
            self.category_grid.setItem(index, 0, QTableWidgetItem(name))
            self.category_grid.setItem(index, 1, QTableWidgetItem(money(amount)))


class SqlConsolePage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = SqlConsoleService()
        self.history: list[str] = []
        layout = QVBoxLayout(self)
        title = QLabel("Console SQL")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        warning = QLabel(
            "Use esta ferramenta com cuidado. Consultas são protegidas por padrão; comandos de alteração podem modificar ou apagar dados."
        )
        warning.setWordWrap(True)
        warning.setObjectName("warning")
        layout.addWidget(warning)
        self.editor = QPlainTextEdit("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name;")
        self.editor.setPlaceholderText("Digite uma instrução SQL")
        layout.addWidget(self.editor)
        controls = QHBoxLayout()
        self.allow_writes = QCheckBox("Permitir comandos que alteram dados")
        self.limit = QSpinBox()
        self.limit.setRange(1, 10_000)
        self.limit.setValue(1_000)
        execute = QPushButton("Executar SQL")
        execute.clicked.connect(self.execute)
        clear = QPushButton("Limpar")
        clear.clicked.connect(self.clear)
        controls.addWidget(self.allow_writes)
        controls.addWidget(QLabel("Limite de linhas:"))
        controls.addWidget(self.limit)
        controls.addStretch()
        controls.addWidget(clear)
        controls.addWidget(execute)
        layout.addLayout(controls)
        self.status = QLabel("Pronto para executar.")
        layout.addWidget(self.status)
        self.result = table([])
        layout.addWidget(self.result, 1)
        layout.addWidget(QLabel("Histórico desta sessão"))
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(lambda item: self.editor.setPlainText(item.text()))
        self.history_list.setMaximumHeight(120)
        layout.addWidget(self.history_list)

    def execute(self) -> None:
        sql = self.editor.toPlainText().strip()
        if self.allow_writes.isChecked():
            answer = QMessageBox.warning(
                self,
                "Confirmar alteração no banco",
                "O comando pode alterar ou excluir dados. Confirma a execução?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
        try:
            output = self.service.execute(sql, allow_writes=self.allow_writes.isChecked(), limit=self.limit.value())
        except Exception as error:
            self.status.setText(f"Erro: {error}")
            QMessageBox.critical(self, "Erro ao executar SQL", str(error))
            return
        self.status.setText(output.message)
        self.result.clear()
        self.result.setColumnCount(len(output.columns))
        self.result.setHorizontalHeaderLabels(output.columns)
        self.result.setRowCount(len(output.rows))
        for row_index, row in enumerate(output.rows):
            for column, value in enumerate(row):
                self.result.setItem(row_index, column, QTableWidgetItem("" if value is None else str(value)))
        if sql and (not self.history or self.history[-1] != sql):
            self.history.append(sql)
            self.history_list.addItem(sql)

    def clear(self) -> None:
        self.editor.clear()
        self.result.clear()
        self.result.setRowCount(0)
        self.result.setColumnCount(0)
        self.status.setText("Área limpa.")


class DatabaseBrowserPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.service = SqlConsoleService()
        layout = QVBoxLayout(self)
        title = QLabel("Banco de dados")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        hint = QLabel("Visualização somente leitura das tabelas SQLite da aplicação.")
        hint.setObjectName("summary")
        layout.addWidget(hint)

        controls = QHBoxLayout()
        self.include_internal = QCheckBox("Mostrar tabelas internas do SQLite")
        self.include_internal.stateChanged.connect(self.refresh)
        self.limit = QSpinBox()
        self.limit.setRange(1, 10_000)
        self.limit.setValue(500)
        self.limit.valueChanged.connect(self.load_selected_table)
        reload_button = QPushButton("Atualizar")
        reload_button.clicked.connect(self.refresh)
        copy_schema = QPushButton("Copiar estrutura SQL")
        copy_schema.clicked.connect(self.copy_schema_sql)
        download_database = QPushButton("Baixar arquivo SQLite")
        download_database.clicked.connect(self.download_database_file)
        controls.addWidget(self.include_internal)
        controls.addWidget(QLabel("Limite de linhas:"))
        controls.addWidget(self.limit)
        controls.addStretch()
        controls.addWidget(copy_schema)
        controls.addWidget(download_database)
        controls.addWidget(reload_button)
        layout.addLayout(controls)

        content = QHBoxLayout()
        self.tables = QListWidget()
        self.tables.setFixedWidth(280)
        self.tables.currentRowChanged.connect(self.load_selected_table)
        content.addWidget(self.tables)
        right = QVBoxLayout()
        self.status = QLabel("Selecione uma tabela para visualizar.")
        right.addWidget(self.status)
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setObjectName("summary")
        right.addWidget(self.description)
        self.grid = table([])
        right.addWidget(self.grid, 1)
        content.addLayout(right, 1)
        layout.addLayout(content, 1)

    def refresh(self) -> None:
        current = self.tables.currentItem().data(Qt.UserRole) if self.tables.currentItem() else None
        self.tables.blockSignals(True)
        self.tables.clear()
        rows = self.service.tables(include_internal=self.include_internal.isChecked())
        for item in rows:
            label = f"{item.name} ({item.row_count})"
            table_item = QListWidgetItem(label)
            table_item.setData(Qt.UserRole, item.name)
            table_item.setData(Qt.UserRole + 1, item.description)
            self.tables.addItem(table_item)
        self.tables.blockSignals(False)
        if not rows:
            self.grid.clear()
            self.grid.setRowCount(0)
            self.grid.setColumnCount(0)
            self.status.setText("Nenhuma tabela encontrada.")
            self.description.clear()
            return
        selected_index = next((index for index, item in enumerate(rows) if item.name == current), 0)
        self.tables.setCurrentRow(selected_index)
        self.load_selected_table()

    def load_selected_table(self) -> None:
        current = self.tables.currentItem()
        if current is None:
            return
        table_name = current.data(Qt.UserRole)
        self.description.setText(str(current.data(Qt.UserRole + 1)))
        try:
            output = self.service.table_data(str(table_name), limit=self.limit.value())
        except Exception as error:
            self.status.setText(f"Erro: {error}")
            QMessageBox.critical(self, "Erro ao visualizar tabela", str(error))
            return
        self.status.setText(output.message)
        self.grid.clear()
        self.grid.setColumnCount(len(output.columns))
        self.grid.setHorizontalHeaderLabels(output.columns)
        self.grid.setRowCount(len(output.rows))
        for row_index, row in enumerate(output.rows):
            for column, value in enumerate(row):
                self.grid.setItem(row_index, column, QTableWidgetItem("" if value is None else str(value)))

    def copy_schema_sql(self) -> None:
        try:
            sql = self.service.schema_sql(include_internal=self.include_internal.isChecked())
        except Exception as error:
            QMessageBox.critical(self, "Erro ao copiar estrutura", str(error))
            return
        QApplication.clipboard().setText(sql)
        self.status.setText("Estrutura SQL copiada para a área de transferência.")
        QMessageBox.information(self, "Estrutura SQL", "Estrutura do banco copiada.")

    def download_database_file(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar banco SQLite",
            "financeiro-kairo.sqlite3",
            "Banco SQLite (*.sqlite3 *.db)",
        )
        if not filename:
            return
        try:
            path = self.service.copy_database_file(Path(filename))
        except Exception as error:
            QMessageBox.critical(self, "Erro ao salvar banco", str(error))
            return
        self.status.setText(f"Arquivo SQLite salvo em: {path}")
        QMessageBox.information(self, "Banco SQLite", f"Arquivo salvo em:\n{path}")


class MainWindow(QMainWindow):
    def __init__(self, facade: ApplicationFacade | None = None) -> None:
        super().__init__()
        self.facade = facade or ApplicationFacade()
        self.setWindowTitle("Financeiro Kairo")
        self.resize(1440, 900)
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        self.menu = QListWidget()
        self.menu.setFixedWidth(250)
        labels = [
            "Visão geral",
            "Transações",
            "Contas",
            "Categorias",
            "Compras",
            "Planejamento",
            "Gráficos",
            "Relatórios e cópias",
            "Banco de dados",
            "Console SQL",
        ]
        self.menu.addItems(labels)
        self.stack = QStackedWidget()
        for page in [
            DashboardPage(self.facade),
            TransactionsPage(self.facade),
            AccountsPage(self.facade),
            CategoriesPage(self.facade),
            PurchasesPage(self.facade),
            PlanningPage(self.facade),
            ChartsPage(self.facade),
            ReportsPage(self.facade),
            DatabaseBrowserPage(),
            SqlConsolePage(),
        ]:
            self.stack.addWidget(page)
        self.menu.currentRowChanged.connect(self.change_page)
        self.menu.setCurrentRow(0)
        layout.addWidget(self.menu)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f6f8fb; color: #18212f; font-size: 14px; }
            QListWidget { background: #172033; color: white; border: 0; padding: 12px; }
            QListWidget::item { padding: 13px; border-radius: 7px; }
            QListWidget::item:selected { background: #2f6fed; }
            QLabel#pageTitle { font-size: 25px; font-weight: 700; margin: 8px; }
            QLabel#sectionTitle { font-size: 18px; font-weight: 700; margin: 8px; }
            QLabel#summary { font-size: 17px; background: white; padding: 20px; border-radius: 10px; }
            QLabel#warning { background: #fff4d6; color: #6a4a00; padding: 12px; border: 1px solid #f0c65d; border-radius: 7px; }
            QPushButton { background: #2f6fed; color: white; padding: 9px 15px; border: 0; border-radius: 7px; }
            QPushButton:hover { background: #245ccc; }
            QLineEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit { background: white; padding: 7px; border: 1px solid #ced5df; border-radius: 6px; }
            QTableWidget, QChartView { background: white; border: 1px solid #e0e4ea; gridline-color: #edf0f4; }
            QHeaderView::section { background: #eef2f7; padding: 8px; border: 0; font-weight: 600; }
            QTabWidget::pane { border: 1px solid #dfe4ec; background: white; }
            """
        )

    def change_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        page = self.stack.currentWidget()
        refresh = getattr(page, "refresh", None)
        if callable(refresh):
            try:
                refresh()
            except Exception as error:
                QMessageBox.critical(self, "Erro", str(error))


def main() -> None:
    create_schema()
    app = QApplication(sys.argv)
    app.setApplicationName("Financeiro Kairo")
    app.setOrganizationName("Kairo")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
