from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from financeiro_kairo.domain.models import (
    Account,
    AccountType,
    Category,
    Transaction,
    TransactionType,
)


@dataclass(frozen=True, slots=True)
class FinancialSummary:
    income_cents: int
    expense_cents: int
    net_cents: int


@dataclass(frozen=True, slots=True)
class CategoryTotal:
    category_id: int | None
    category_name: str
    amount_cents: int


@dataclass(frozen=True, slots=True)
class CreditCardInvoiceTotal:
    account_id: int
    account_name: str
    amount_cents: int


@dataclass(frozen=True, slots=True)
class CreditCardInvoiceTransaction:
    account_id: int
    account_name: str
    occurred_on: date
    description: str
    amount_cents: int


class ReportService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def summary(self, start: date, end: date) -> FinancialSummary:
        rows = self.session.execute(
            select(Transaction.transaction_type, func.sum(Transaction.amount_cents))
            .where(Transaction.occurred_on.between(start, end))
            .group_by(Transaction.transaction_type)
        ).all()
        totals = {kind: int(value or 0) for kind, value in rows}
        income = totals.get(TransactionType.INCOME.value, 0)
        expense = totals.get(TransactionType.EXPENSE.value, 0)
        return FinancialSummary(income, expense, income - expense)

    def expenses_by_category(self, start: date, end: date) -> list[CategoryTotal]:
        rows = self.session.execute(
            select(
                Transaction.category_id,
                func.coalesce(Category.name, "Sem categoria"),
                func.sum(Transaction.amount_cents),
            )
            .outerjoin(Category, Category.id == Transaction.category_id)
            .where(
                Transaction.transaction_type == TransactionType.EXPENSE.value,
                Transaction.occurred_on.between(start, end),
            )
            .group_by(Transaction.category_id, Category.name)
            .order_by(func.sum(Transaction.amount_cents).desc())
        ).all()
        return [CategoryTotal(row[0], str(row[1]), int(row[2] or 0)) for row in rows]

    def credit_card_invoice(
        self, start: date, end: date, *, recent_limit: int = 10
    ) -> tuple[list[CreditCardInvoiceTotal], list[CreditCardInvoiceTransaction]]:
        totals_rows = self.session.execute(
            select(
                Account.id,
                Account.name,
                func.coalesce(func.sum(Transaction.amount_cents), 0),
            )
            .join(Transaction, Transaction.account_id == Account.id)
            .where(
                Account.account_type == AccountType.CREDIT_CARD.value,
                Account.active.is_(True),
                Transaction.transaction_type == TransactionType.EXPENSE.value,
                Transaction.occurred_on.between(start, end),
            )
            .group_by(Account.id, Account.name)
            .order_by(func.sum(Transaction.amount_cents).desc())
        ).all()
        transactions_rows = self.session.execute(
            select(
                Account.id,
                Account.name,
                Transaction.occurred_on,
                Transaction.description,
                Transaction.amount_cents,
            )
            .join(Transaction, Transaction.account_id == Account.id)
            .where(
                Account.account_type == AccountType.CREDIT_CARD.value,
                Account.active.is_(True),
                Transaction.transaction_type == TransactionType.EXPENSE.value,
                Transaction.occurred_on.between(start, end),
            )
            .order_by(Transaction.occurred_on.desc(), Transaction.id.desc())
            .limit(recent_limit)
        ).all()
        totals = [
            CreditCardInvoiceTotal(int(row[0]), str(row[1]), int(row[2] or 0))
            for row in totals_rows
        ]
        transactions = [
            CreditCardInvoiceTransaction(
                int(row[0]),
                str(row[1]),
                row[2],
                str(row[3]),
                int(row[4] or 0),
            )
            for row in transactions_rows
        ]
        return totals, transactions

    def transactions_page(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        start: date | None = None,
        end: date | None = None,
        account_id: int | None = None,
        category_id: int | None = None,
        search_text: str | None = None,
    ) -> tuple[list[Transaction], int]:
        filters = []
        if start is not None:
            filters.append(Transaction.occurred_on >= start)
        if end is not None:
            filters.append(Transaction.occurred_on <= end)
        if account_id is not None:
            filters.append(Transaction.account_id == account_id)
        if category_id is not None:
            filters.append(Transaction.category_id == category_id)
        if search_text:
            filters.append(Transaction.description.ilike(f"%{search_text.strip()}%"))

        total = int(
            self.session.scalar(select(func.count(Transaction.id)).where(*filters)) or 0
        )
        items = self.session.scalars(
            select(Transaction)
            .where(*filters)
            .order_by(Transaction.occurred_on.desc(), Transaction.id.desc())
            .offset((max(page, 1) - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total

    def export_transactions_excel(
        self, transactions: Sequence[Transaction], target: Path
    ) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame(
            [
                {
                    "Data": item.occurred_on.isoformat(),
                    "Descrição": item.description,
                    "Tipo": item.transaction_type,
                    "Valor (R$)": item.amount_cents / 100,
                    "Conta": item.account_id,
                    "Categoria": item.category_id,
                    "Status": item.status,
                }
                for item in transactions
            ]
        )
        frame.to_excel(target, index=False)
        return target

    def export_summary_pdf(
        self,
        *,
        start: date,
        end: date,
        target: Path,
    ) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        summary = self.summary(start, end)
        categories = self.expenses_by_category(start, end)
        canvas = Canvas(str(target), pagesize=A4)
        width, height = A4
        y = height - 60
        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawString(50, y, "Financeiro Kairo — Relatório financeiro")
        y -= 28
        canvas.setFont("Helvetica", 11)
        canvas.drawString(50, y, f"Período: {start.isoformat()} a {end.isoformat()}")
        y -= 28
        canvas.drawString(50, y, f"Receitas: R$ {summary.income_cents / 100:,.2f}")
        y -= 20
        canvas.drawString(50, y, f"Despesas: R$ {summary.expense_cents / 100:,.2f}")
        y -= 20
        canvas.drawString(50, y, f"Resultado: R$ {summary.net_cents / 100:,.2f}")
        y -= 35
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawString(50, y, "Despesas por categoria")
        canvas.setFont("Helvetica", 10)
        for category in categories:
            y -= 18
            if y < 60:
                canvas.showPage()
                y = height - 60
            canvas.drawString(60, y, category.category_name)
            canvas.drawRightString(width - 50, y, f"R$ {category.amount_cents / 100:,.2f}")
        canvas.save()
        return target
