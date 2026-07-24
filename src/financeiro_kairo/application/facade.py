from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import select

from financeiro_kairo.application.schemas import AccountCreate, TransactionCreate
from financeiro_kairo.application.services.backup import BackupService
from financeiro_kairo.application.services.catalog import normalize_text
from financeiro_kairo.application.services.categories import CategoryService
from financeiro_kairo.application.services.finance import FinanceService
from financeiro_kairo.application.services.imports import PurchaseImportService
from financeiro_kairo.application.services.planning import PlanningService
from financeiro_kairo.application.services.recurring_expenses import RecurringExpenseService
from financeiro_kairo.application.services.reports import ReportService
from financeiro_kairo.domain.models import Account, Category, Merchant, Purchase, Transaction
from financeiro_kairo.domain.planning_models import Budget, Goal, Installment, InstallmentPlan
from financeiro_kairo.domain.recurring_expenses import RecurringExpense
from financeiro_kairo.infrastructure.database.session import session_scope


class ApplicationFacade:
    def accounts(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            service = FinanceService(session)
            rows = session.scalars(select(Account).order_by(Account.name)).all()
            return [
                {
                    "id": item.id,
                    "name": item.name,
                    "type": item.account_type,
                    "active": item.active,
                    "initial_balance_cents": item.initial_balance_cents,
                    "balance_cents": service.account_balance_cents(item.id),
                }
                for item in rows
            ]

    def create_account(self, *, name: str, account_type: str, initial_balance_cents: int) -> int:
        with session_scope() as session:
            item = FinanceService(session).create_account(
                AccountCreate(
                    name=name,
                    account_type=account_type,
                    initial_balance_cents=initial_balance_cents,
                )
            )
            return item.id

    def update_account(
        self,
        account_id: int,
        *,
        name: str,
        account_type: str,
        initial_balance_cents: int,
        active: bool = True,
    ) -> None:
        with session_scope() as session:
            item = self._require(session, Account, account_id)
            clean_name = name.strip()
            if len(clean_name) < 2:
                raise ValueError("Informe um nome com pelo menos dois caracteres.")
            item.name = clean_name
            item.account_type = account_type
            item.initial_balance_cents = initial_balance_cents
            item.active = active

    def delete_account(self, account_id: int) -> None:
        with session_scope() as session:
            session.delete(self._require(session, Account, account_id))

    def transactions(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
        search_text: str | None = None,
        start: date | None = None,
        end: date | None = None,
        account_id: int | None = None,
        category_id: int | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        with session_scope() as session:
            rows, total = ReportService(session).transactions_page(
                page=page,
                page_size=page_size,
                search_text=search_text,
                start=start,
                end=end,
                account_id=account_id,
                category_id=category_id,
            )
            return (
                [
                    {
                        "id": row.id,
                        "date": row.occurred_on,
                        "description": row.description,
                        "type": row.transaction_type,
                        "amount_cents": row.amount_cents,
                        "account_id": row.account_id,
                        "category_id": row.category_id,
                        "status": row.status,
                    }
                    for row in rows
                ],
                total,
            )

    def create_transaction(
        self,
        *,
        transaction_type: str,
        description: str,
        amount_cents: int,
        occurred_on: date,
        account_id: int,
        category_id: int | None = None,
    ) -> int:
        with session_scope() as session:
            item = FinanceService(session).create_transaction(
                TransactionCreate(
                    transaction_type=transaction_type,
                    description=description,
                    amount_cents=amount_cents,
                    occurred_on=occurred_on,
                    account_id=account_id,
                    category_id=category_id,
                )
            )
            return item.id

    def update_transaction(
        self,
        transaction_id: int,
        *,
        transaction_type: str,
        description: str,
        amount_cents: int,
        occurred_on: date,
        account_id: int,
        category_id: int | None = None,
    ) -> None:
        data = TransactionCreate(
            transaction_type=transaction_type,
            description=description,
            amount_cents=amount_cents,
            occurred_on=occurred_on,
            account_id=account_id,
            category_id=category_id,
        )
        with session_scope() as session:
            FinanceService(session)._require_account(data.account_id)
            item = self._require(session, Transaction, transaction_id)
            item.transaction_type = data.transaction_type
            item.description = data.description
            item.amount_cents = data.amount_cents
            item.occurred_on = data.occurred_on
            item.account_id = data.account_id
            item.category_id = data.category_id

    def delete_transaction(self, transaction_id: int) -> None:
        with session_scope() as session:
            session.delete(self._require(session, Transaction, transaction_id))

    def categories(self, *, include_inactive: bool = False) -> list[dict[str, Any]]:
        with session_scope() as session:
            rows = CategoryService(session).list(include_inactive=include_inactive)
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "parent_id": row.parent_id,
                    "kind": row.kind,
                    "active": row.active,
                }
                for row in rows
            ]

    def create_category(self, *, name: str, kind: str, parent_id: int | None = None) -> int:
        with session_scope() as session:
            item = CategoryService(session).create(name=name, kind=kind, parent_id=parent_id)
            return item.id

    def update_category(
        self,
        category_id: int,
        *,
        name: str,
        kind: str,
        parent_id: int | None = None,
        active: bool = True,
    ) -> None:
        with session_scope() as session:
            service = CategoryService(session)
            item = service.update(category_id, name=name, kind=kind, parent_id=parent_id)
            item.active = active

    def archive_category(self, category_id: int) -> None:
        with session_scope() as session:
            CategoryService(session).archive(category_id)

    def delete_category(self, category_id: int) -> None:
        with session_scope() as session:
            session.delete(self._require(session, Category, category_id))

    def purchases(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            rows = session.scalars(
                select(Purchase).order_by(Purchase.purchased_on.desc(), Purchase.id.desc())
            ).all()
            return [
                {
                    "id": row.id,
                    "date": row.purchased_on,
                    "merchant": row.merchant.name,
                    "account_id": row.account_id,
                    "items": len(row.items),
                    "total_cents": row.net_total_cents,
                    "source": row.source_type,
                    "document_number": row.document_number,
                }
                for row in rows
            ]

    def import_purchase(self, path: Path) -> int:
        payload = json.loads(path.read_text(encoding="utf-8"))
        with session_scope() as session:
            purchase = PurchaseImportService(session).import_payload(payload, path.name)
            return purchase.id

    def update_purchase(
        self,
        purchase_id: int,
        *,
        purchased_on: date,
        merchant_name: str,
        account_id: int | None,
        total_cents: int,
        source_type: str,
        document_number: str | None = None,
    ) -> None:
        clean_merchant = merchant_name.strip()
        if len(clean_merchant) < 2:
            raise ValueError("Informe o estabelecimento.")
        if total_cents < 0:
            raise ValueError("O total não pode ser negativo.")
        with session_scope() as session:
            if account_id is not None:
                FinanceService(session)._require_account(account_id)
            purchase = self._require(session, Purchase, purchase_id)
            normalized = normalize_text(clean_merchant)
            merchant = session.scalar(select(Merchant).where(Merchant.normalized_name == normalized))
            if merchant is None:
                merchant = Merchant(name=clean_merchant, normalized_name=normalized)
                session.add(merchant)
                session.flush()
            purchase.purchased_on = purchased_on
            purchase.merchant_id = merchant.id
            purchase.account_id = account_id
            purchase.gross_total_cents = total_cents
            purchase.net_total_cents = total_cents
            purchase.discount_cents = 0
            purchase.source_type = source_type.strip() or "manual"
            purchase.document_number = document_number.strip() if document_number else None

    def delete_purchase(self, purchase_id: int) -> None:
        with session_scope() as session:
            session.delete(self._require(session, Purchase, purchase_id))

    def budgets(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            service = PlanningService(session)
            rows = session.scalars(
                select(Budget)
                .where(Budget.active.is_(True))
                .order_by(Budget.period_start.desc())
            ).all()
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "start": row.period_start,
                    "end": row.period_end,
                    "limit_cents": row.limit_cents,
                    "used_cents": service.budget_usage_cents(row.id),
                    "active": row.active,
                }
                for row in rows
            ]

    def create_budget(
        self,
        *,
        name: str,
        period_start: date,
        period_end: date,
        limit_cents: int,
        category_id: int | None = None,
    ) -> int:
        with session_scope() as session:
            item = PlanningService(session).create_budget(
                name=name,
                period_start=period_start,
                period_end=period_end,
                limit_cents=limit_cents,
                category_id=category_id,
            )
            return item.id

    def update_budget(
        self,
        budget_id: int,
        *,
        name: str,
        period_start: date,
        period_end: date,
        limit_cents: int,
        active: bool = True,
    ) -> None:
        if len(name.strip()) < 2:
            raise ValueError("Informe um nome para o orçamento.")
        if limit_cents < 0:
            raise ValueError("O limite não pode ser negativo.")
        if period_end < period_start:
            raise ValueError("A data final deve ser maior ou igual à inicial.")
        with session_scope() as session:
            item = self._require(session, Budget, budget_id)
            item.name = name.strip()
            item.period_start = period_start
            item.period_end = period_end
            item.limit_cents = limit_cents
            item.active = active

    def delete_budget(self, budget_id: int) -> None:
        with session_scope() as session:
            session.delete(self._require(session, Budget, budget_id))

    def goals(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            rows = session.scalars(
                select(Goal).where(Goal.active.is_(True)).order_by(Goal.id.desc())
            ).all()
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "target_cents": row.target_cents,
                    "current_cents": row.current_cents,
                    "target_date": row.target_date,
                    "active": row.active,
                }
                for row in rows
            ]

    def create_goal(self, *, name: str, target_cents: int, target_date: date | None = None) -> int:
        with session_scope() as session:
            item = PlanningService(session).create_goal(
                name=name,
                target_cents=target_cents,
                target_date=target_date,
            )
            return item.id

    def update_goal(
        self,
        goal_id: int,
        *,
        name: str,
        target_cents: int,
        current_cents: int,
        active: bool = True,
    ) -> None:
        if len(name.strip()) < 2:
            raise ValueError("Informe um nome para a meta.")
        if target_cents <= 0 or current_cents < 0:
            raise ValueError("Valores da meta inválidos.")
        with session_scope() as session:
            item = self._require(session, Goal, goal_id)
            item.name = name.strip()
            item.target_cents = target_cents
            item.current_cents = current_cents
            item.active = active

    def delete_goal(self, goal_id: int) -> None:
        with session_scope() as session:
            session.delete(self._require(session, Goal, goal_id))

    def contribute_goal(self, goal_id: int, amount_cents: int, contributed_on: date) -> None:
        with session_scope() as session:
            PlanningService(session).contribute_to_goal(goal_id, amount_cents, contributed_on)

    def installments(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            rows = session.execute(
                select(Installment, InstallmentPlan)
                .join(InstallmentPlan, InstallmentPlan.id == Installment.plan_id)
                .order_by(Installment.due_date, Installment.id)
            ).all()
            return [
                {
                    "id": installment.id,
                    "plan_id": plan.id,
                    "description": plan.description,
                    "number": installment.number,
                    "count": plan.installment_count,
                    "due_date": installment.due_date,
                    "amount_cents": installment.amount_cents,
                    "paid": installment.paid,
                }
                for installment, plan in rows
            ]

    def create_installment_plan(
        self,
        *,
        description: str,
        total_cents: int,
        installment_count: int,
        account_id: int,
        first_due_date: date,
        category_id: int | None = None,
    ) -> int:
        with session_scope() as session:
            item = PlanningService(session).create_installment_plan(
                description=description,
                total_cents=total_cents,
                installment_count=installment_count,
                account_id=account_id,
                first_due_date=first_due_date,
                category_id=category_id,
            )
            return item.id

    def update_installment(
        self,
        installment_id: int,
        *,
        due_date: date,
        amount_cents: int,
    ) -> None:
        if amount_cents <= 0:
            raise ValueError("O valor da parcela deve ser positivo.")
        with session_scope() as session:
            item = self._require(session, Installment, installment_id)
            if item.paid:
                raise ValueError("Não é possível editar uma parcela já paga.")
            item.due_date = due_date
            item.amount_cents = amount_cents

    def delete_installment_plan(self, plan_id: int) -> None:
        with session_scope() as session:
            plan = self._require(session, InstallmentPlan, plan_id)
            if any(installment.paid for installment in plan.installments):
                raise ValueError("Não é possível apagar um parcelamento com parcelas pagas.")
            session.delete(plan)

    def pay_installment(self, installment_id: int, paid_on: date) -> None:
        with session_scope() as session:
            PlanningService(session).pay_installment(installment_id, paid_on)

    def recurring_expenses(self, *, include_inactive: bool = False) -> list[dict[str, Any]]:
        with session_scope() as session:
            rows = RecurringExpenseService(session).list_expenses(
                include_inactive=include_inactive
            )
            return [
                {
                    "id": item.id,
                    "description": item.description,
                    "amount_mode": item.amount_mode,
                    "fixed_amount_cents": item.fixed_amount_cents,
                    "due_day": item.due_day,
                    "reminder_days_before": item.reminder_days_before,
                    "account_id": item.account_id,
                    "category_id": item.category_id,
                    "active": item.active,
                }
                for item in rows
            ]

    def create_recurring_expense(
        self,
        *,
        description: str,
        amount_mode: str,
        fixed_amount_cents: int | None,
        due_day: int,
        reminder_days_before: int,
        account_id: int,
        category_id: int | None = None,
    ) -> int:
        with session_scope() as session:
            item = RecurringExpenseService(session).create(
                description=description,
                amount_mode=amount_mode,
                fixed_amount_cents=fixed_amount_cents,
                due_day=due_day,
                reminder_days_before=reminder_days_before,
                account_id=account_id,
                category_id=category_id,
            )
            return item.id

    def update_recurring_expense(
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
    ) -> None:
        with session_scope() as session:
            RecurringExpenseService(session).update(
                expense_id,
                description=description,
                amount_mode=amount_mode,
                fixed_amount_cents=fixed_amount_cents,
                due_day=due_day,
                reminder_days_before=reminder_days_before,
                account_id=account_id,
                category_id=category_id,
                active=active,
            )

    def delete_recurring_expense(self, expense_id: int) -> None:
        with session_scope() as session:
            item = self._require(session, RecurringExpense, expense_id)
            paid_occurrences = [occurrence for occurrence in item.occurrences if occurrence.paid]
            if paid_occurrences:
                raise ValueError("Não é possível apagar uma despesa recorrente com ocorrências pagas.")
            session.delete(item)

    def recurring_expense_month(self, reference: date) -> list[dict[str, Any]]:
        with session_scope() as session:
            service = RecurringExpenseService(session)
            rows = service.occurrences_for_month(reference)
            today = date.today()
            return [
                {
                    "id": item.id,
                    "expense_id": item.expense_id,
                    "description": item.expense.description,
                    "amount_mode": item.expense.amount_mode,
                    "amount_cents": item.amount_cents,
                    "due_date": item.due_date,
                    "paid": item.paid,
                    "paid_on": item.paid_on,
                    "status": service.status(item, today),
                }
                for item in rows
            ]

    def set_recurring_expense_amount(self, occurrence_id: int, amount_cents: int) -> None:
        with session_scope() as session:
            RecurringExpenseService(session).set_variable_amount(occurrence_id, amount_cents)

    def pay_recurring_expense(self, occurrence_id: int, paid_on: date) -> None:
        with session_scope() as session:
            RecurringExpenseService(session).mark_paid(occurrence_id, paid_on)

    def unpay_recurring_expense(self, occurrence_id: int) -> None:
        with session_scope() as session:
            RecurringExpenseService(session).mark_unpaid(occurrence_id)

    def recurring_expense_reminders(self, today: date | None = None) -> list[dict[str, Any]]:
        reference = today or date.today()
        with session_scope() as session:
            service = RecurringExpenseService(session)
            return [
                {
                    "id": item.id,
                    "description": item.expense.description,
                    "due_date": item.due_date,
                    "amount_cents": item.amount_cents,
                    "status": service.status(item, reference),
                }
                for item in service.reminders(reference)
            ]

    def dashboard(self, start: date, end: date) -> dict[str, Any]:
        with session_scope() as session:
            reports = ReportService(session)
            summary = reports.summary(start, end)
            categories = reports.expenses_by_category(start, end)
            invoice_totals, invoice_transactions = reports.credit_card_invoice(start, end)
            balances = sum(item["balance_cents"] for item in self.accounts())
            return {
                "income_cents": summary.income_cents,
                "expense_cents": summary.expense_cents,
                "net_cents": summary.net_cents,
                "balance_cents": balances,
                "categories": [(item.category_name, item.amount_cents) for item in categories],
                "credit_card_invoice": {
                    "total_cents": sum(item.amount_cents for item in invoice_totals),
                    "cards": [
                        {
                            "account_id": item.account_id,
                            "account_name": item.account_name,
                            "amount_cents": item.amount_cents,
                        }
                        for item in invoice_totals
                    ],
                    "transactions": [
                        {
                            "account_id": item.account_id,
                            "account_name": item.account_name,
                            "date": item.occurred_on,
                            "description": item.description,
                            "amount_cents": item.amount_cents,
                        }
                        for item in invoice_transactions
                    ],
                },
            }

    def export_excel(self, target: Path, start: date, end: date) -> Path:
        with session_scope() as session:
            reports = ReportService(session)
            rows, _ = reports.transactions_page(
                page=1,
                page_size=1_000_000,
                start=start,
                end=end,
            )
            return reports.export_transactions_excel(rows, target)

    def export_pdf(self, target: Path, start: date, end: date) -> Path:
        with session_scope() as session:
            return ReportService(session).export_summary_pdf(start=start, end=end, target=target)

    def create_backup(self) -> Path:
        return BackupService().create_backup()

    def restore_backup(self, path: Path) -> Path:
        return BackupService().restore_backup(path)

    @staticmethod
    def _require(session: Any, model: type, object_id: int) -> Any:
        item = session.get(model, object_id)
        if item is None:
            raise LookupError(f"{model.__name__} {object_id} não encontrado.")
        return item
