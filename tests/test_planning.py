from datetime import date

from financeiro_kairo.application.schemas import AccountCreate, TransactionCreate
from financeiro_kairo.application.services.finance import FinanceService
from financeiro_kairo.application.services.planning import PlanningService
from financeiro_kairo.domain.models import AccountType, TransactionType


def test_budget_goal_recurrence_and_installments(session):
    finance = FinanceService(session)
    account = finance.create_account(
        AccountCreate(name="Conta principal", account_type=AccountType.CHECKING.value)
    )
    finance.create_transaction(
        TransactionCreate(
            transaction_type=TransactionType.EXPENSE.value,
            description="Mercado",
            amount_cents=15_000,
            occurred_on=date(2026, 7, 5),
            account_id=account.id,
        )
    )

    planning = PlanningService(session)
    budget = planning.create_budget(
        name="Orçamento mensal",
        period_start=date(2026, 7, 1),
        period_end=date(2026, 7, 31),
        limit_cents=50_000,
    )
    assert planning.budget_usage_cents(budget.id) == 15_000

    goal = planning.create_goal(name="Reserva", target_cents=100_000)
    planning.contribute_to_goal(goal.id, 20_000, date(2026, 7, 10))
    assert goal.current_cents == 20_000

    planning.create_recurrence(
        description="Internet",
        transaction_type=TransactionType.EXPENSE.value,
        amount_cents=10_000,
        account_id=account.id,
        next_date=date(2026, 7, 15),
    )
    generated = planning.generate_due_recurrences(date(2026, 8, 15))
    assert len(generated) == 2

    plan = planning.create_installment_plan(
        description="Notebook",
        total_cents=100_001,
        installment_count=3,
        account_id=account.id,
        first_due_date=date(2026, 8, 1),
    )
    assert sum(item.amount_cents for item in plan.installments) == 100_001
    payment = planning.pay_installment(plan.installments[0].id, date(2026, 8, 1))
    assert payment.amount_cents == plan.installments[0].amount_cents
    assert plan.installments[0].paid is True
