from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QApplication,
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
    QMainWindow,
    QMessageBox,
    QProgressBar,
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
from financeiro_kairo.domain.models import AccountType, CategoryKind, TransactionType
from financeiro_kairo.infrastructure.database.bootstrap import create_schema


def money(cents: int) -> str:
    value = cents / 100
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def table(rows: int, headers: list[str]) -> QTableWidget:
    widget = QTableWidget(rows, len(headers))
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
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def finish(self) -> None:
        self.form.addRow(self.buttons)


class TransactionDialog(FormDialog):
    def __init__(self, facade: ApplicationFacade, parent: QWidget | None = None) -> None:
        super().__init__("Nova transação", parent)
        self.facade = facade
        self.description = QLineEdit()
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0.01, 10_000_000)
        self.amount.setDecimals(2)
        self.amount.setPrefix("R$ ")
        self.kind = QComboBox()
        self.kind.addItem("Despesa", TransactionType.EXPENSE.value)
        self.kind.addItem("Receita", TransactionType.INCOME.value)
        self.account = QComboBox()
        for item in facade.accounts():
            if item["active"]:
                self.account.addItem(item["name"], item["id"])
        self.category = QComboBox()
        self.category.addItem("Sem categoria", None)
        for item in facade.categories():
            self.category.addItem(item["name"], item["id"])
        self.occurred_on = QDateEdit(QDate.currentDate())
        self.occurred_on.setCalendarPopup(True)
        self.form.addRow("Descrição", self.description)
        self.form.addRow("Valor", self.amount)
        self.form.addRow("Tipo", self.kind)
        self.form.addRow("Conta", self.account)
        self.form.addRow("Categoria", self.category)
        self.form.addRow("Data", self.occurred_on)
        self.finish()

    def accept(self) -> None:
        if len(self.description.text().strip()) < 2 or self.account.currentData() is None:
            QMessageBox.warning(self, "Dados inválidos", "Informe descrição e uma conta válida.")
            return
        self.facade.create_transaction(
            transaction_type=str(self.kind.currentData()),
            description=self.description.text().strip(),
            amount_cents=round(self.amount.value() * 100),
            occurred_on=self.occurred_on.date().toPython(),
            account_id=int(self.account.currentData()),
            category_id=self.category.currentData(),
        )
        super().accept()


class AccountDialog(FormDialog):
    def __init__(self, facade: ApplicationFacade, parent: QWidget | None = None) -> None:
        super().__init__("Nova conta", parent)
        self.facade = facade
        self.name = QLineEdit()
        self.kind = QComboBox()
        for item in AccountType:
            self.kind.addItem(item.value.replace("_", " ").title(), item.value)
        self.balance = QDoubleSpinBox()
        self.balance.setRange(-10_000_000, 10_000_000)
        self.balance.setPrefix("R$ ")
        self.form.addRow("Nome", self.name)
        self.form.addRow("Tipo", self.kind)
        self.form.addRow("Saldo inicial", self.balance)
        self.finish()

    def accept(self) -> None:
        if len(self.name.text().strip()) < 2:
            QMessageBox.warning(self, "Nome inválido", "Informe um nome para a conta.")
            return
        self.facade.create_account(
            name=self.name.text().strip(),
            account_type=str(self.kind.currentData()),
            initial_balance_cents=round(self.balance.value() * 100),
        )
        super().accept()


class CategoryDialog(FormDialog):
    def __init__(self, facade: ApplicationFacade, parent: QWidget | None = None) -> None:
        super().__init__("Nova categoria", parent)
        self.facade = facade
        self.name = QLineEdit()
        self.kind = QComboBox()
        for item in CategoryKind:
            self.kind.addItem(item.value.title(), item.value)
        self.parent = QComboBox()
        self.parent.addItem("Nenhuma", None)
        for item in facade.categories():
            self.parent.addItem(item["name"], item["id"])
        self.form.addRow("Nome", self.name)
        self.form.addRow("Tipo", self.kind)
        self.form.addRow("Categoria pai", self.parent)
        self.finish()

    def accept(self) -> None:
        try:
            self.facade.create_category(
                name=self.name.text(),
                kind=str(self.kind.currentData()),
                parent_id=self.parent.currentData(),
            )
        except (ValueError, LookupError) as error:
            QMessageBox.warning(self, "Categoria inválida", str(error))
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
        self.categories = table(0, ["Categoria", "Despesas"])
        layout.addWidget(self.categories)

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


class TransactionsPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Transações")
        title.setObjectName("pageTitle")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar descrição")
        self.search.returnPressed.connect(self.refresh)
        add = QPushButton("Nova transação")
        add.clicked.connect(self.create)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search)
        header.addWidget(add)
        layout.addLayout(header)
        self.grid = table(0, ["Data", "Descrição", "Tipo", "Valor", "Conta", "Status"])
        layout.addWidget(self.grid)

    def create(self) -> None:
        if TransactionDialog(self.facade, self).exec():
            self.refresh()

    def refresh(self) -> None:
        rows, _ = self.facade.transactions(search_text=self.search.text().strip() or None)
        self.grid.setRowCount(len(rows))
        for index, item in enumerate(rows):
            values = [
                item["date"].strftime("%d/%m/%Y"),
                item["description"],
                item["type"],
                money(item["amount_cents"]),
                str(item["account_id"]),
                item["status"],
            ]
            for column, value in enumerate(values):
                self.grid.setItem(index, column, QTableWidgetItem(value))


class AccountsPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Contas")
        title.setObjectName("pageTitle")
        add = QPushButton("Nova conta")
        add.clicked.connect(self.create)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add)
        layout.addLayout(header)
        self.grid = table(0, ["Conta", "Tipo", "Saldo", "Estado"])
        layout.addWidget(self.grid)

    def create(self) -> None:
        if AccountDialog(self.facade, self).exec():
            self.refresh()

    def refresh(self) -> None:
        rows = self.facade.accounts()
        self.grid.setRowCount(len(rows))
        for index, item in enumerate(rows):
            values = [item["name"], item["type"], money(item["balance_cents"]), "Ativa" if item["active"] else "Arquivada"]
            for column, value in enumerate(values):
                self.grid.setItem(index, column, QTableWidgetItem(value))


class CategoriesPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Categorias")
        title.setObjectName("pageTitle")
        add = QPushButton("Nova categoria")
        add.clicked.connect(self.create)
        archive = QPushButton("Arquivar selecionada")
        archive.clicked.connect(self.archive)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add)
        header.addWidget(archive)
        layout.addLayout(header)
        self.grid = table(0, ["Nome", "Tipo", "Categoria pai", "Estado"])
        layout.addWidget(self.grid)
        self.ids: list[int] = []

    def create(self) -> None:
        if CategoryDialog(self.facade, self).exec():
            self.refresh()

    def archive(self) -> None:
        row = self.grid.currentRow()
        if row < 0:
            return
        self.facade.archive_category(self.ids[row])
        self.refresh()

    def refresh(self) -> None:
        rows = self.facade.categories(include_inactive=True)
        names = {item["id"]: item["name"] for item in rows}
        self.ids = [item["id"] for item in rows]
        self.grid.setRowCount(len(rows))
        for index, item in enumerate(rows):
            values = [item["name"], item["kind"], names.get(item["parent_id"], "—"), "Ativa" if item["active"] else "Arquivada"]
            for column, value in enumerate(values):
                self.grid.setItem(index, column, QTableWidgetItem(value))


class PurchasesPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel("Compras e importações")
        title.setObjectName("pageTitle")
        import_button = QPushButton("Importar JSON")
        import_button.clicked.connect(self.import_json)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(import_button)
        layout.addLayout(header)
        hint = QLabel("O arquivo é validado antes da persistência e importações duplicadas são bloqueadas.")
        layout.addWidget(hint)
        self.grid = table(0, ["Data", "Estabelecimento", "Itens", "Total", "Origem"])
        layout.addWidget(self.grid)

    def import_json(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Selecionar compra", "", "JSON (*.json)")
        if not filename:
            return
        try:
            purchase_id = self.facade.import_purchase(Path(filename))
        except Exception as error:
            QMessageBox.critical(self, "Falha na importação", str(error))
            return
        QMessageBox.information(self, "Importação concluída", f"Compra #{purchase_id} importada com sucesso.")
        self.refresh()

    def refresh(self) -> None:
        rows = self.facade.purchases()
        self.grid.setRowCount(len(rows))
        for index, item in enumerate(rows):
            values = [item["date"].strftime("%d/%m/%Y"), item["merchant"], str(item["items"]), money(item["total_cents"]), item["source"]]
            for column, value in enumerate(values):
                self.grid.setItem(index, column, QTableWidgetItem(value))


class PlanningPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        layout = QVBoxLayout(self)
        title = QLabel("Planejamento")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.budget_tab = QWidget()
        self.goal_tab = QWidget()
        self.installment_tab = QWidget()
        self.tabs.addTab(self.budget_tab, "Orçamentos")
        self.tabs.addTab(self.goal_tab, "Metas")
        self.tabs.addTab(self.installment_tab, "Parcelas")
        self._build_budgets()
        self._build_goals()
        self._build_installments()

    def _build_budgets(self) -> None:
        layout = QVBoxLayout(self.budget_tab)
        form = QHBoxLayout()
        self.budget_name = QLineEdit()
        self.budget_name.setPlaceholderText("Nome")
        self.budget_limit = QDoubleSpinBox()
        self.budget_limit.setRange(0.01, 10_000_000)
        self.budget_limit.setPrefix("R$ ")
        add = QPushButton("Criar orçamento mensal")
        add.clicked.connect(self.create_budget)
        form.addWidget(self.budget_name)
        form.addWidget(self.budget_limit)
        form.addWidget(add)
        layout.addLayout(form)
        self.budget_grid = table(0, ["Orçamento", "Período", "Limite", "Realizado", "Uso"])
        layout.addWidget(self.budget_grid)

    def _build_goals(self) -> None:
        layout = QVBoxLayout(self.goal_tab)
        form = QHBoxLayout()
        self.goal_name = QLineEdit()
        self.goal_name.setPlaceholderText("Meta")
        self.goal_target = QDoubleSpinBox()
        self.goal_target.setRange(0.01, 100_000_000)
        self.goal_target.setPrefix("R$ ")
        add = QPushButton("Criar meta")
        add.clicked.connect(self.create_goal)
        contribute = QPushButton("Contribuir R$ 100")
        contribute.clicked.connect(self.contribute_goal)
        form.addWidget(self.goal_name)
        form.addWidget(self.goal_target)
        form.addWidget(add)
        form.addWidget(contribute)
        layout.addLayout(form)
        self.goal_grid = table(0, ["Meta", "Atual", "Alvo", "Progresso"])
        layout.addWidget(self.goal_grid)
        self.goal_ids: list[int] = []

    def _build_installments(self) -> None:
        layout = QVBoxLayout(self.installment_tab)
        form = QHBoxLayout()
        self.plan_description = QLineEdit()
        self.plan_description.setPlaceholderText("Descrição")
        self.plan_total = QDoubleSpinBox()
        self.plan_total.setRange(0.01, 10_000_000)
        self.plan_total.setPrefix("R$ ")
        self.plan_count = QSpinBox()
        self.plan_count.setRange(1, 120)
        self.plan_account = QComboBox()
        add = QPushButton("Criar parcelamento")
        add.clicked.connect(self.create_installment)
        pay = QPushButton("Pagar selecionada")
        pay.clicked.connect(self.pay_installment)
        for item in self.facade.accounts():
            if item["active"]:
                self.plan_account.addItem(item["name"], item["id"])
        form.addWidget(self.plan_description)
        form.addWidget(self.plan_total)
        form.addWidget(self.plan_count)
        form.addWidget(self.plan_account)
        form.addWidget(add)
        form.addWidget(pay)
        layout.addLayout(form)
        self.installment_grid = table(0, ["Descrição", "Parcela", "Vencimento", "Valor", "Estado"])
        layout.addWidget(self.installment_grid)
        self.installment_ids: list[int] = []

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

    def create_goal(self) -> None:
        if len(self.goal_name.text().strip()) < 2:
            return
        self.facade.create_goal(name=self.goal_name.text().strip(), target_cents=round(self.goal_target.value() * 100))
        self.goal_name.clear()
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

    def pay_installment(self) -> None:
        row = self.installment_grid.currentRow()
        if row >= 0:
            try:
                self.facade.pay_installment(self.installment_ids[row], date.today())
            except ValueError as error:
                QMessageBox.warning(self, "Parcela", str(error))
            self.refresh()

    def refresh(self) -> None:
        budgets = self.facade.budgets()
        self.budget_grid.setRowCount(len(budgets))
        for index, item in enumerate(budgets):
            percentage = 0 if item["limit_cents"] == 0 else min(999, round(item["used_cents"] * 100 / item["limit_cents"]))
            values = [item["name"], f"{item['start']:%d/%m/%Y}–{item['end']:%d/%m/%Y}", money(item["limit_cents"]), money(item["used_cents"]), f"{percentage}%"]
            for column, value in enumerate(values):
                self.budget_grid.setItem(index, column, QTableWidgetItem(value))
        goals = self.facade.goals()
        self.goal_ids = [item["id"] for item in goals]
        self.goal_grid.setRowCount(len(goals))
        for index, item in enumerate(goals):
            percentage = min(100, round(item["current_cents"] * 100 / item["target_cents"]))
            values = [item["name"], money(item["current_cents"]), money(item["target_cents"]), f"{percentage}%"]
            for column, value in enumerate(values):
                self.goal_grid.setItem(index, column, QTableWidgetItem(value))
        installments = self.facade.installments()
        self.installment_ids = [item["id"] for item in installments]
        self.installment_grid.setRowCount(len(installments))
        for index, item in enumerate(installments):
            values = [item["description"], f"{item['number']}/{item['count']}", item["due_date"].strftime("%d/%m/%Y"), money(item["amount_cents"]), "Paga" if item["paid"] else "Pendente"]
            for column, value in enumerate(values):
                self.installment_grid.setItem(index, column, QTableWidgetItem(value))


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
            ("Exportar Excel", self.export_excel),
            ("Exportar PDF", self.export_pdf),
            ("Criar backup", self.backup),
            ("Restaurar backup", self.restore),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.summary = QLabel()
        self.summary.setObjectName("summary")
        layout.addWidget(self.summary)
        self.category_grid = table(0, ["Categoria", "Total"])
        layout.addWidget(self.category_grid)

    def range(self) -> tuple[date, date]:
        today = date.today()
        return today.replace(day=1), today

    def export_excel(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar relatório", "transacoes.xlsx", "Excel (*.xlsx)")
        if filename:
            start, end = self.range()
            self.facade.export_excel(Path(filename), start, end)
            QMessageBox.information(self, "Relatório", "Arquivo Excel criado.")

    def export_pdf(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar relatório", "relatorio.pdf", "PDF (*.pdf)")
        if filename:
            start, end = self.range()
            self.facade.export_pdf(Path(filename), start, end)
            QMessageBox.information(self, "Relatório", "Arquivo PDF criado.")

    def backup(self) -> None:
        try:
            path = self.facade.create_backup()
        except Exception as error:
            QMessageBox.critical(self, "Backup", str(error))
            return
        QMessageBox.information(self, "Backup", f"Backup criado em:\n{path}")

    def restore(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Restaurar backup", "", "SQLite (*.sqlite3 *.db)")
        if not filename:
            return
        answer = QMessageBox.question(self, "Confirmar restauração", "A base atual será preservada antes da restauração. Continuar?")
        if answer != QMessageBox.Yes:
            return
        try:
            safety = self.facade.restore_backup(Path(filename))
        except Exception as error:
            QMessageBox.critical(self, "Restauração", str(error))
            return
        QMessageBox.information(self, "Restauração concluída", f"Cópia anterior preservada em:\n{safety}\nReinicie o aplicativo.")

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


class MainWindow(QMainWindow):
    def __init__(self, facade: ApplicationFacade | None = None) -> None:
        super().__init__()
        self.facade = facade or ApplicationFacade()
        self.setWindowTitle("Financeiro Kairo")
        self.resize(1360, 860)
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        self.menu = QListWidget()
        self.menu.setFixedWidth(240)
        labels = ["Visão geral", "Transações", "Contas", "Categorias", "Compras", "Planejamento", "Relatórios e backup"]
        self.menu.addItems(labels)
        self.stack = QStackedWidget()
        for page in [
            DashboardPage(self.facade),
            TransactionsPage(self.facade),
            AccountsPage(self.facade),
            CategoriesPage(self.facade),
            PurchasesPage(self.facade),
            PlanningPage(self.facade),
            ReportsPage(self.facade),
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
            QLabel#summary { font-size: 17px; background: white; padding: 20px; border-radius: 10px; }
            QPushButton { background: #2f6fed; color: white; padding: 9px 15px; border: 0; border-radius: 7px; }
            QPushButton:hover { background: #245ccc; }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit { background: white; padding: 7px; border: 1px solid #ced5df; border-radius: 6px; }
            QTableWidget { background: white; border: 1px solid #e0e4ea; gridline-color: #edf0f4; }
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
