from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from financeiro_kairo.application.facade import ApplicationFacade


def money(cents: int | None) -> str:
    if cents is None:
        return "A informar"
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


class RecurringExpenseDialog(QDialog):
    def __init__(
        self,
        facade: ApplicationFacade,
        item: dict | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.facade = facade
        self.item = item
        self.setWindowTitle("Editar despesa recorrente" if item else "Nova despesa recorrente")
        form = QFormLayout(self)

        self.description = QLineEdit()
        self.amount_mode = QComboBox()
        self.amount_mode.addItem("Valor fixo", "fixed")
        self.amount_mode.addItem("Valor variável a cada mês", "variable")
        self.amount_mode.currentIndexChanged.connect(self._update_amount_state)
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0.01, 10_000_000)
        self.amount.setDecimals(2)
        self.amount.setPrefix("R$ ")
        self.due_day = QSpinBox()
        self.due_day.setRange(1, 31)
        self.reminder = QSpinBox()
        self.reminder.setRange(0, 60)
        self.reminder.setSuffix(" dias antes")
        self.reminder.setValue(3)
        self.account = QComboBox()
        for account in facade.accounts():
            if account["active"]:
                self.account.addItem(account["name"], account["id"])
        self.category = QComboBox()
        self.category.addItem("Sem categoria", None)
        for category in facade.categories():
            self.category.addItem(category["name"], category["id"])
        self.active = QCheckBox("Despesa ativa")
        self.active.setChecked(True)

        form.addRow("Descrição", self.description)
        form.addRow("Tipo de valor", self.amount_mode)
        form.addRow("Valor fixo", self.amount)
        form.addRow("Dia do vencimento", self.due_day)
        form.addRow("Lembrete", self.reminder)
        form.addRow("Conta de pagamento", self.account)
        form.addRow("Categoria", self.category)
        form.addRow("Situação", self.active)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Salvar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        if item:
            self.description.setText(item["description"])
            self.amount_mode.setCurrentIndex(0 if item["amount_mode"] == "fixed" else 1)
            if item["fixed_amount_cents"] is not None:
                self.amount.setValue(item["fixed_amount_cents"] / 100)
            self.due_day.setValue(item["due_day"])
            self.reminder.setValue(item["reminder_days_before"])
            self._select(self.account, item["account_id"])
            self._select(self.category, item["category_id"])
            self.active.setChecked(item["active"])
        self._update_amount_state()

    @staticmethod
    def _select(combo: QComboBox, value: object) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _update_amount_state(self) -> None:
        self.amount.setEnabled(self.amount_mode.currentData() == "fixed")

    def accept(self) -> None:
        if self.account.currentData() is None:
            QMessageBox.warning(self, "Conta obrigatória", "Cadastre ou selecione uma conta válida.")
            return
        mode = str(self.amount_mode.currentData())
        fixed_amount = round(self.amount.value() * 100) if mode == "fixed" else None
        payload = {
            "description": self.description.text().strip(),
            "amount_mode": mode,
            "fixed_amount_cents": fixed_amount,
            "due_day": self.due_day.value(),
            "reminder_days_before": self.reminder.value(),
            "account_id": int(self.account.currentData()),
            "category_id": self.category.currentData(),
        }
        try:
            if self.item:
                self.facade.update_recurring_expense(
                    self.item["id"], **payload, active=self.active.isChecked()
                )
            else:
                self.facade.create_recurring_expense(**payload)
        except (ValueError, LookupError) as error:
            QMessageBox.warning(self, "Dados inválidos", str(error))
            return
        super().accept()


class RecurringExpensesPage(QWidget):
    def __init__(self, facade: ApplicationFacade) -> None:
        super().__init__()
        self.facade = facade
        self.expenses: list[dict] = []
        self.occurrences: list[dict] = []
        layout = QVBoxLayout(self)
        title = QLabel("Despesas recorrentes")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.reminder_banner = QLabel()
        self.reminder_banner.setWordWrap(True)
        self.reminder_banner.setObjectName("warning")
        layout.addWidget(self.reminder_banner)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._build_registry_tab()
        self._build_month_tab()

    def _build_registry_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        actions = QHBoxLayout()
        create = QPushButton("Nova despesa recorrente")
        create.clicked.connect(self.create_expense)
        edit = QPushButton("Editar selecionada")
        edit.clicked.connect(self.edit_expense)
        actions.addWidget(create)
        actions.addWidget(edit)
        actions.addStretch()
        layout.addLayout(actions)
        self.expense_grid = table(
            ["Descrição", "Tipo", "Valor", "Vencimento", "Lembrete", "Situação"]
        )
        layout.addWidget(self.expense_grid)
        self.tabs.addTab(page, "Cadastros")

    def _build_month_tab(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        actions = QHBoxLayout()
        actions.addWidget(QLabel("Mês de referência:"))
        self.reference = QDateEdit(QDate.currentDate())
        self.reference.setDisplayFormat("MM/yyyy")
        self.reference.setCalendarPopup(True)
        self.reference.dateChanged.connect(self.refresh_month)
        actions.addWidget(self.reference)
        value = QPushButton("Informar valor")
        value.clicked.connect(self.set_amount)
        pay = QPushButton("Marcar como paga")
        pay.clicked.connect(self.mark_paid)
        unpay = QPushButton("Marcar como não paga")
        unpay.clicked.connect(self.mark_unpaid)
        actions.addStretch()
        actions.addWidget(value)
        actions.addWidget(pay)
        actions.addWidget(unpay)
        layout.addLayout(actions)
        self.month_grid = table(
            ["Vencimento", "Descrição", "Tipo", "Valor", "Situação", "Pagamento"]
        )
        layout.addWidget(self.month_grid)
        self.tabs.addTab(page, "Contas do mês")

    def create_expense(self) -> None:
        if RecurringExpenseDialog(self.facade, parent=self).exec():
            self.refresh()

    def edit_expense(self) -> None:
        row = self.expense_grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Editar", "Selecione uma despesa recorrente.")
            return
        if RecurringExpenseDialog(self.facade, self.expenses[row], self).exec():
            self.refresh()

    def set_amount(self) -> None:
        item = self._selected_occurrence()
        if item is None:
            return
        if item["amount_mode"] != "variable":
            QMessageBox.information(self, "Valor fixo", "Esta despesa já possui um valor fixo.")
            return
        value, accepted = QInputDialog.getDouble(
            self,
            "Valor do mês",
            f"Informe o valor de {item['description']}:",
            (item["amount_cents"] or 0) / 100,
            0.01,
            10_000_000,
            2,
        )
        if accepted:
            self.facade.set_recurring_expense_amount(item["id"], round(value * 100))
            self.refresh_month()

    def mark_paid(self) -> None:
        item = self._selected_occurrence()
        if item is None:
            return
        try:
            self.facade.pay_recurring_expense(item["id"], date.today())
        except (ValueError, LookupError) as error:
            QMessageBox.warning(self, "Pagamento", str(error))
            return
        self.refresh()

    def mark_unpaid(self) -> None:
        item = self._selected_occurrence()
        if item is None:
            return
        if not item["paid"]:
            return
        answer = QMessageBox.question(
            self,
            "Desfazer pagamento",
            "A transação gerada por este pagamento será removida. Deseja continuar?",
        )
        if answer == QMessageBox.Yes:
            self.facade.unpay_recurring_expense(item["id"])
            self.refresh()

    def _selected_occurrence(self) -> dict | None:
        row = self.month_grid.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleção", "Selecione uma conta do mês.")
            return None
        return self.occurrences[row]

    def refresh(self) -> None:
        self.expenses = self.facade.recurring_expenses(include_inactive=True)
        self.expense_grid.setRowCount(len(self.expenses))
        for row, item in enumerate(self.expenses):
            values = [
                item["description"],
                "Fixa" if item["amount_mode"] == "fixed" else "Variável",
                money(item["fixed_amount_cents"]),
                f"Dia {item['due_day']}",
                f"{item['reminder_days_before']} dias antes",
                "Ativa" if item["active"] else "Inativa",
            ]
            for column, value in enumerate(values):
                self.expense_grid.setItem(row, column, QTableWidgetItem(value))
        self.refresh_month()
        reminders = self.facade.recurring_expense_reminders()
        if reminders:
            text = " • ".join(
                f"{item['description']} — {item['status']} em {item['due_date']:%d/%m}"
                for item in reminders
            )
            self.reminder_banner.setText(f"Lembretes de pagamento: {text}")
            self.reminder_banner.show()
        else:
            self.reminder_banner.hide()

    def refresh_month(self) -> None:
        reference = self.reference.date().toPython()
        self.occurrences = self.facade.recurring_expense_month(reference)
        self.month_grid.setRowCount(len(self.occurrences))
        for row, item in enumerate(self.occurrences):
            values = [
                item["due_date"].strftime("%d/%m/%Y"),
                item["description"],
                "Fixa" if item["amount_mode"] == "fixed" else "Variável",
                money(item["amount_cents"]),
                item["status"],
                item["paid_on"].strftime("%d/%m/%Y") if item["paid_on"] else "—",
            ]
            for column, value in enumerate(values):
                self.month_grid.setItem(row, column, QTableWidgetItem(value))
