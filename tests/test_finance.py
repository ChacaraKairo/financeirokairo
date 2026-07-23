from datetime import date

from sqlalchemy.orm import Session

from financeiro_kairo.application.schemas import AccountCreate, TransactionCreate, TransferCreate
from financeiro_kairo.application.services.finance import FinanceService


def test_account_balance_with_income_expense_and_transfer(session: Session) -> None:
    service = FinanceService(session)
    source = service.create_account(
        AccountCreate(name="Conta principal", account_type="checking", initial_balance_cents=100_000)
    )
    destination = service.create_account(
        AccountCreate(name="Reserva", account_type="savings", initial_balance_cents=0)
    )
    service.create_transaction(
        TransactionCreate(
            transaction_type="income",
            description="Salário",
            amount_cents=50_000,
            occurred_on=date(2026, 7, 1),
            account_id=source.id,
        )
    )
    service.create_transaction(
        TransactionCreate(
            transaction_type="expense",
            description="Mercado",
            amount_cents=20_000,
            occurred_on=date(2026, 7, 2),
            account_id=source.id,
        )
    )
    service.create_transfer(
        TransferCreate(
            description="Reserva mensal",
            amount_cents=10_000,
            occurred_on=date(2026, 7, 3),
            source_account_id=source.id,
            destination_account_id=destination.id,
        )
    )

    assert service.account_balance_cents(source.id) == 120_000
    assert service.account_balance_cents(destination.id) == 10_000
