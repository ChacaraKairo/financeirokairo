from __future__ import annotations

from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from financeiro_kairo.infrastructure.database.base import Base, TimestampMixin


class RecurringExpense(TimestampMixin, Base):
    __tablename__ = "recurring_expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    amount_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    fixed_amount_cents: Mapped[int | None] = mapped_column(Integer)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)
    reminder_days_before: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"))
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    occurrences: Mapped[list[RecurringExpenseOccurrence]] = relationship(
        back_populates="expense", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("amount_mode IN ('fixed', 'variable')", name="recurring_amount_mode"),
        CheckConstraint("due_day BETWEEN 1 AND 31", name="recurring_due_day"),
        CheckConstraint(
            "reminder_days_before BETWEEN 0 AND 60", name="recurring_reminder_days"
        ),
        CheckConstraint(
            "(amount_mode = 'fixed' AND fixed_amount_cents > 0) OR "
            "(amount_mode = 'variable' AND fixed_amount_cents IS NULL)",
            name="recurring_amount_consistency",
        ),
        Index("ix_recurring_expenses_active_due", "active", "due_day"),
    )


class RecurringExpenseOccurrence(TimestampMixin, Base):
    __tablename__ = "recurring_expense_occurrences"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(
        ForeignKey("recurring_expenses.id", ondelete="CASCADE"), nullable=False
    )
    reference_month: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_cents: Mapped[int | None] = mapped_column(Integer)
    paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    paid_on: Mapped[date | None] = mapped_column(Date)
    transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="SET NULL")
    )

    expense: Mapped[RecurringExpense] = relationship(back_populates="occurrences")

    __table_args__ = (
        CheckConstraint("amount_cents IS NULL OR amount_cents > 0", name="occurrence_amount"),
        CheckConstraint(
            "(paid = 0 AND paid_on IS NULL) OR (paid = 1 AND paid_on IS NOT NULL)",
            name="occurrence_payment_consistency",
        ),
        UniqueConstraint("expense_id", "reference_month", name="uq_recurring_month"),
        Index("ix_recurring_occurrences_due_paid", "due_date", "paid"),
    )
