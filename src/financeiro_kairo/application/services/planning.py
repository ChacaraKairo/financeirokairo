from __future__ import annotations

from calendar import monthrange
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from financeiro_kairo.domain.models import Transaction, TransactionType
from financeiro_kairo.domain.planning_models import (
    Budget,
    Goal,
    GoalContribution,
    Installment,
    InstallmentPlan,
    RecurrenceRule,
)


class PlanningService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_budget(
        self,
        *,
        name: str,
        period_start: date,
        period_end: date,
        limit_cents: int,
        category_id: int | None = None,
        rollover: bool = False,
    ) -> Budget:
        budget = Budget(
            name=name,
            category_id=category_id,
            period_start=period_start,
            period_end=period_end,
            limit_cents=limit_cents,
            rollover=rollover,
        )
        self.session.add(budget)
        self.session.flush()
        return budget

    def budget_usage_cents(self, budget_id: int) -> int:
        budget = self._require(Budget, budget_id)
        filters = [
            Transaction.transaction_type == TransactionType.EXPENSE.value,
            Transaction.occurred_on >= budget.period_start,
            Transaction.occurred_on <= budget.period_end,
        ]
        if budget.category_id is not None:
            filters.append(Transaction.category_id == budget.category_id)
        value = self.session.scalar(
            select(func.coalesce(func.sum(Transaction.amount_cents), 0)).where(*filters)
        )
        return int(value or 0)

    def create_goal(
        self,
        *,
        name: str,
        target_cents: int,
        target_date: date | None = None,
        account_id: int | None = None,
        notes: str | None = None,
    ) -> Goal:
        goal = Goal(
            name=name,
            target_cents=target_cents,
            target_date=target_date,
            account_id=account_id,
            notes=notes,
        )
        self.session.add(goal)
        self.session.flush()
        return goal

    def contribute_to_goal(
        self,
        goal_id: int,
        amount_cents: int,
        contributed_on: date,
        notes: str | None = None,
    ) -> GoalContribution:
        goal = self._require(Goal, goal_id)
        contribution = GoalContribution(
            goal_id=goal.id,
            amount_cents=amount_cents,
            contributed_on=contributed_on,
            notes=notes,
        )
        goal.current_cents += amount_cents
        self.session.add(contribution)
        self.session.flush()
        return contribution

    def create_recurrence(
        self,
        *,
        description: str,
        transaction_type: str,
        amount_cents: int,
        account_id: int,
        next_date: date,
        frequency: str = "monthly",
        interval: int = 1,
        category_id: int | None = None,
        end_date: date | None = None,
    ) -> RecurrenceRule:
        rule = RecurrenceRule(
            description=description,
            transaction_type=transaction_type,
            amount_cents=amount_cents,
            account_id=account_id,
            category_id=category_id,
            frequency=frequency,
            interval=interval,
            next_date=next_date,
            end_date=end_date,
        )
        self.session.add(rule)
        self.session.flush()
        return rule

    def generate_due_recurrences(self, through_date: date) -> list[Transaction]:
        rules = self.session.scalars(
            select(RecurrenceRule).where(
                RecurrenceRule.active.is_(True), RecurrenceRule.next_date <= through_date
            )
        ).all()
        generated: list[Transaction] = []
        for rule in rules:
            while rule.next_date <= through_date and rule.active:
                transaction = Transaction(
                    transaction_type=rule.transaction_type,
                    description=rule.description,
                    amount_cents=rule.amount_cents,
                    occurred_on=rule.next_date,
                    account_id=rule.account_id,
                    category_id=rule.category_id,
                    notes=f"Gerado pela recorrência #{rule.id}",
                )
                self.session.add(transaction)
                generated.append(transaction)
                rule.next_date = self._advance(rule.next_date, rule.frequency, rule.interval)
                if rule.end_date is not None and rule.next_date > rule.end_date:
                    rule.active = False
        self.session.flush()
        return generated

    def create_installment_plan(
        self,
        *,
        description: str,
        total_cents: int,
        installment_count: int,
        account_id: int,
        first_due_date: date,
        category_id: int | None = None,
    ) -> InstallmentPlan:
        plan = InstallmentPlan(
            description=description,
            total_cents=total_cents,
            installment_count=installment_count,
            account_id=account_id,
            category_id=category_id,
            first_due_date=first_due_date,
        )
        self.session.add(plan)
        self.session.flush()

        base, remainder = divmod(total_cents, installment_count)
        due = first_due_date
        for number in range(1, installment_count + 1):
            amount = base + (1 if number <= remainder else 0)
            self.session.add(
                Installment(
                    plan_id=plan.id,
                    number=number,
                    due_date=due,
                    amount_cents=amount,
                )
            )
            due = self._add_months(due, 1)
        self.session.flush()
        return plan

    def pay_installment(self, installment_id: int, paid_on: date) -> Transaction:
        installment = self._require(Installment, installment_id)
        if installment.paid:
            raise ValueError("installment is already paid")
        plan = self._require(InstallmentPlan, installment.plan_id)
        transaction = Transaction(
            transaction_type=TransactionType.EXPENSE.value,
            description=f"{plan.description} ({installment.number}/{plan.installment_count})",
            amount_cents=installment.amount_cents,
            occurred_on=paid_on,
            account_id=plan.account_id,
            category_id=plan.category_id,
        )
        self.session.add(transaction)
        self.session.flush()
        installment.paid = True
        installment.transaction_id = transaction.id
        self.session.flush()
        return transaction

    def _require(self, model: type, object_id: int):
        obj = self.session.get(model, object_id)
        if obj is None:
            raise LookupError(f"{model.__name__} {object_id} was not found")
        return obj

    @classmethod
    def _advance(cls, value: date, frequency: str, interval: int) -> date:
        if frequency == "daily":
            return date.fromordinal(value.toordinal() + interval)
        if frequency == "weekly":
            return date.fromordinal(value.toordinal() + 7 * interval)
        if frequency == "monthly":
            return cls._add_months(value, interval)
        if frequency == "yearly":
            return cls._add_months(value, 12 * interval)
        raise ValueError(f"unsupported frequency: {frequency}")

    @staticmethod
    def _add_months(value: date, months: int) -> date:
        index = value.year * 12 + value.month - 1 + months
        year, month_index = divmod(index, 12)
        month = month_index + 1
        day = min(value.day, monthrange(year, month)[1])
        return date(year, month, day)
