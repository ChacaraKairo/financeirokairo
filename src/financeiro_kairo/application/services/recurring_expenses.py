from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from financeiro_kairo.domain.models import Transaction, TransactionType
from financeiro_kairo.domain.recurring_expenses import (
    RecurringExpense,
    RecurringExpenseOccurrence,
)


class RecurringExpenseService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        description: str,
        amount_mode: str,
        fixed_amount_cents: int | None,
        due_day: int,
        reminder_days_before: int,
        account_id: int,
        category_id: int | None = None,
    ) -> RecurringExpense:
        self._validate(description, amount_mode, fixed_amount_cents, due_day, reminder_days_before)
        item = RecurringExpense(
            description=description.strip(),
            amount_mode=amount_mode,
            fixed_amount_cents=fixed_amount_cents,
            due_day=due_day,
            reminder_days_before=reminder_days_before,
            account_id=account_id,
            category_id=category_id,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def update(
        self,
        expense_id: int,
        *,
        description: str,
        amount_mode: str,
        fixed_amount_cents: int | None,
        due_day: int,
        reminder_days_before: int,
        account_id: int,
        category_id: int | None = None,
        active: bool = True,
    ) -> RecurringExpense:
        item = self._require_expense(expense_id)
        self._validate(description, amount_mode, fixed_amount_cents, due_day, reminder_days_before)
        item.description = description.strip()
        item.amount_mode = amount_mode
        item.fixed_amount_cents = fixed_amount_cents
        item.due_day = due_day
        item.reminder_days_before = reminder_days_before
        item.account_id = account_id
        item.category_id = category_id
        item.active = active
        self.session.flush()
        return item

    def list_expenses(self, *, include_inactive: bool = False) -> list[RecurringExpense]:
        query = select(RecurringExpense).order_by(RecurringExpense.description)
        if not include_inactive:
            query = query.where(RecurringExpense.active.is_(True))
        return list(self.session.scalars(query).all())

    def ensure_month(self, reference: date) -> list[RecurringExpenseOccurrence]:
        first_day = reference.replace(day=1)
        expenses = self.list_expenses()
        created: list[RecurringExpenseOccurrence] = []
        for expense in expenses:
            existing = self.session.scalar(
                select(RecurringExpenseOccurrence).where(
                    RecurringExpenseOccurrence.expense_id == expense.id,
                    RecurringExpenseOccurrence.reference_month == first_day,
                )
            )
            if existing is not None:
                continue
            due_day = min(expense.due_day, monthrange(first_day.year, first_day.month)[1])
            occurrence = RecurringExpenseOccurrence(
                expense_id=expense.id,
                reference_month=first_day,
                due_date=date(first_day.year, first_day.month, due_day),
                amount_cents=expense.fixed_amount_cents,
            )
            self.session.add(occurrence)
            created.append(occurrence)
        self.session.flush()
        return created

    def occurrences_for_month(self, reference: date) -> list[RecurringExpenseOccurrence]:
        self.ensure_month(reference)
        first_day = reference.replace(day=1)
        return list(
            self.session.scalars(
                select(RecurringExpenseOccurrence)
                .join(RecurringExpense)
                .where(RecurringExpenseOccurrence.reference_month == first_day)
                .order_by(RecurringExpenseOccurrence.due_date, RecurringExpense.description)
            ).all()
        )

    def set_variable_amount(self, occurrence_id: int, amount_cents: int) -> None:
        occurrence = self._require_occurrence(occurrence_id)
        if occurrence.expense.amount_mode != "variable":
            raise ValueError("Somente despesas variáveis permitem informar o valor mensal.")
        if occurrence.paid:
            raise ValueError("Não é possível alterar o valor de uma despesa já paga.")
        if amount_cents <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        occurrence.amount_cents = amount_cents
        self.session.flush()

    def mark_paid(self, occurrence_id: int, paid_on: date) -> Transaction:
        occurrence = self._require_occurrence(occurrence_id)
        if occurrence.paid:
            raise ValueError("A despesa já está marcada como paga.")
        if occurrence.amount_cents is None:
            raise ValueError("Informe o valor da despesa antes de confirmar o pagamento.")
        expense = occurrence.expense
        transaction = Transaction(
            transaction_type=TransactionType.EXPENSE.value,
            description=expense.description,
            amount_cents=occurrence.amount_cents,
            occurred_on=paid_on,
            account_id=expense.account_id,
            category_id=expense.category_id,
            notes=(
                f"Pagamento da despesa recorrente #{expense.id} "
                f"referente a {occurrence.reference_month:%m/%Y}"
            ),
        )
        self.session.add(transaction)
        self.session.flush()
        occurrence.paid = True
        occurrence.paid_on = paid_on
        occurrence.transaction_id = transaction.id
        self.session.flush()
        return transaction

    def mark_unpaid(self, occurrence_id: int) -> None:
        occurrence = self._require_occurrence(occurrence_id)
        if not occurrence.paid:
            return
        if occurrence.transaction_id is not None:
            transaction = self.session.get(Transaction, occurrence.transaction_id)
            if transaction is not None:
                self.session.delete(transaction)
        occurrence.paid = False
        occurrence.paid_on = None
        occurrence.transaction_id = None
        self.session.flush()

    def reminders(self, today: date) -> list[RecurringExpenseOccurrence]:
        self.ensure_month(today)
        rows = self.occurrences_for_month(today)
        return [
            item
            for item in rows
            if not item.paid
            and today >= item.due_date - timedelta(days=item.expense.reminder_days_before)
        ]

    @staticmethod
    def status(occurrence: RecurringExpenseOccurrence, today: date) -> str:
        if occurrence.paid:
            return "Paga"
        if occurrence.amount_cents is None:
            return "Aguardando valor"
        if occurrence.due_date < today:
            return "Atrasada"
        if occurrence.due_date == today:
            return "Vence hoje"
        return "Pendente"

    def _require_expense(self, expense_id: int) -> RecurringExpense:
        item = self.session.get(RecurringExpense, expense_id)
        if item is None:
            raise LookupError("Despesa recorrente não encontrada.")
        return item

    def _require_occurrence(self, occurrence_id: int) -> RecurringExpenseOccurrence:
        item = self.session.get(RecurringExpenseOccurrence, occurrence_id)
        if item is None:
            raise LookupError("Competência mensal não encontrada.")
        return item

    @staticmethod
    def _validate(
        description: str,
        amount_mode: str,
        fixed_amount_cents: int | None,
        due_day: int,
        reminder_days_before: int,
    ) -> None:
        if len(description.strip()) < 2:
            raise ValueError("Informe uma descrição válida.")
        if amount_mode not in {"fixed", "variable"}:
            raise ValueError("Tipo de valor inválido.")
        if amount_mode == "fixed" and (fixed_amount_cents is None or fixed_amount_cents <= 0):
            raise ValueError("Informe o valor fixo da despesa.")
        if amount_mode == "variable" and fixed_amount_cents is not None:
            raise ValueError("Despesas variáveis não podem possuir valor fixo.")
        if not 1 <= due_day <= 31:
            raise ValueError("O dia de vencimento deve estar entre 1 e 31.")
        if not 0 <= reminder_days_before <= 60:
            raise ValueError("O lembrete deve estar entre 0 e 60 dias antes do vencimento.")
