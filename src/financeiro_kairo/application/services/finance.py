from __future__ import annotations

from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from financeiro_kairo.application.schemas import AccountCreate, TransactionCreate, TransferCreate
from financeiro_kairo.domain.models import Account, Transaction, TransactionType


class AccountNotFoundError(LookupError):
    pass


class FinanceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_account(self, data: AccountCreate) -> Account:
        account = Account(**data.model_dump())
        self.session.add(account)
        self.session.flush()
        return account

    def create_transaction(self, data: TransactionCreate) -> Transaction:
        self._require_account(data.account_id)
        transaction = Transaction(**data.model_dump())
        self.session.add(transaction)
        self.session.flush()
        return transaction

    def create_transfer(self, data: TransferCreate) -> tuple[Transaction, Transaction]:
        self._require_account(data.source_account_id)
        self._require_account(data.destination_account_id)
        group = str(uuid4())

        outgoing = Transaction(
            transaction_type=TransactionType.TRANSFER.value,
            description=data.description,
            amount_cents=data.amount_cents,
            occurred_on=data.occurred_on,
            account_id=data.source_account_id,
            transfer_group=group,
            notes=data.notes,
        )
        incoming = Transaction(
            transaction_type=TransactionType.TRANSFER.value,
            description=data.description,
            amount_cents=data.amount_cents,
            occurred_on=data.occurred_on,
            account_id=data.destination_account_id,
            transfer_group=group,
            notes=data.notes,
        )
        self.session.add_all([outgoing, incoming])
        self.session.flush()
        return outgoing, incoming

    def account_balance_cents(self, account_id: int) -> int:
        account = self._require_account(account_id)
        income = self.session.scalar(
            select(func.coalesce(func.sum(Transaction.amount_cents), 0)).where(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.INCOME.value,
            )
        )
        expense = self.session.scalar(
            select(func.coalesce(func.sum(Transaction.amount_cents), 0)).where(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.EXPENSE.value,
            )
        )
        transfer_rows = self.session.scalars(
            select(Transaction).where(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.TRANSFER.value,
            )
        ).all()
        transfer_delta = 0
        for row in transfer_rows:
            if row.transfer_group is None:
                continue
            pair = self.session.scalars(
                select(Transaction)
                .where(Transaction.transfer_group == row.transfer_group)
                .order_by(Transaction.id)
            ).all()
            if len(pair) == 2:
                # O serviço sempre persiste a saída antes da entrada.
                transfer_delta += -row.amount_cents if pair[0].id == row.id else row.amount_cents

        return account.initial_balance_cents + int(income or 0) - int(expense or 0) + transfer_delta

    def _require_account(self, account_id: int) -> Account:
        account = self.session.get(Account, account_id)
        if account is None or not account.active:
            raise AccountNotFoundError(f"account {account_id} was not found or is inactive")
        return account
