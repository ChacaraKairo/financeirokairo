from datetime import date

from sqlalchemy import select

from financeiro_kairo.application.schemas import AccountCreate
from financeiro_kairo.application.services.finance import FinanceService
from financeiro_kairo.application.services.recurring_expenses import RecurringExpenseService
from financeiro_kairo.domain.models import Transaction


def create_account(session) -> int:
    account = FinanceService(session).create_account(
        AccountCreate(name="Conta principal", account_type="checking", initial_balance_cents=0)
    )
    return account.id


def test_fixed_expense_creates_monthly_occurrence_and_clamps_due_day(session):
    account_id = create_account(session)
    service = RecurringExpenseService(session)
    expense = service.create(
        description="Aluguel",
        amount_mode="fixed",
        fixed_amount_cents=150_000,
        due_day=31,
        reminder_days_before=5,
        account_id=account_id,
    )

    rows = service.occurrences_for_month(date(2027, 2, 10))

    assert len(rows) == 1
    assert rows[0].expense_id == expense.id
    assert rows[0].due_date == date(2027, 2, 28)
    assert rows[0].amount_cents == 150_000
    assert service.status(rows[0], date(2027, 2, 20)) == "Pendente"


def test_variable_expense_requires_monthly_amount_before_payment(session):
    account_id = create_account(session)
    service = RecurringExpenseService(session)
    service.create(
        description="Energia elétrica",
        amount_mode="variable",
        fixed_amount_cents=None,
        due_day=15,
        reminder_days_before=3,
        account_id=account_id,
    )
    occurrence = service.occurrences_for_month(date(2027, 3, 1))[0]

    assert occurrence.amount_cents is None
    assert service.status(occurrence, date(2027, 3, 1)) == "Aguardando valor"

    try:
        service.mark_paid(occurrence.id, date(2027, 3, 10))
    except ValueError as error:
        assert "Informe o valor" in str(error)
    else:
        raise AssertionError("Pagamento sem valor deveria ser recusado")

    service.set_variable_amount(occurrence.id, 23_450)
    transaction = service.mark_paid(occurrence.id, date(2027, 3, 12))

    assert occurrence.paid is True
    assert occurrence.paid_on == date(2027, 3, 12)
    assert transaction.amount_cents == 23_450
    assert transaction.description == "Energia elétrica"

    service.mark_unpaid(occurrence.id)
    assert occurrence.paid is False
    assert occurrence.transaction_id is None
    assert session.scalar(select(Transaction).where(Transaction.id == transaction.id)) is None


def test_reminders_include_due_and_overdue_unpaid_expenses(session):
    account_id = create_account(session)
    service = RecurringExpenseService(session)
    service.create(
        description="Internet",
        amount_mode="fixed",
        fixed_amount_cents=9_990,
        due_day=10,
        reminder_days_before=3,
        account_id=account_id,
    )

    assert service.reminders(date(2027, 4, 6)) == []
    reminders = service.reminders(date(2027, 4, 7))
    assert len(reminders) == 1
    assert reminders[0].expense.description == "Internet"
    assert service.status(reminders[0], date(2027, 4, 11)) == "Atrasada"


def test_edit_recurring_expense_changes_future_configuration(session):
    account_id = create_account(session)
    service = RecurringExpenseService(session)
    item = service.create(
        description="Condomínio",
        amount_mode="fixed",
        fixed_amount_cents=30_000,
        due_day=5,
        reminder_days_before=2,
        account_id=account_id,
    )

    service.update(
        item.id,
        description="Condomínio atualizado",
        amount_mode="variable",
        fixed_amount_cents=None,
        due_day=8,
        reminder_days_before=4,
        account_id=account_id,
        active=True,
    )

    assert item.description == "Condomínio atualizado"
    assert item.amount_mode == "variable"
    assert item.fixed_amount_cents is None
    assert item.due_day == 8
    assert item.reminder_days_before == 4
