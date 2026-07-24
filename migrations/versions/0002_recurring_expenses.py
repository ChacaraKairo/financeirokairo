"""Adiciona despesas recorrentes e competências mensais.

Revision ID: 0002_recurring_expenses
Revises: 0001_initial_schema
Create Date: 2026-07-23
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_recurring_expenses"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "recurring_expenses" not in tables:
        op.create_table(
            "recurring_expenses",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("description", sa.String(length=240), nullable=False),
            sa.Column("amount_mode", sa.String(length=20), nullable=False),
            sa.Column("fixed_amount_cents", sa.Integer(), nullable=True),
            sa.Column("due_day", sa.Integer(), nullable=False),
            sa.Column("reminder_days_before", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("account_id", sa.Integer(), nullable=False),
            sa.Column("category_id", sa.Integer(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint("amount_mode IN ('fixed', 'variable')", name="recurring_amount_mode"),
            sa.CheckConstraint("due_day BETWEEN 1 AND 31", name="recurring_due_day"),
            sa.CheckConstraint(
                "reminder_days_before BETWEEN 0 AND 60", name="recurring_reminder_days"
            ),
            sa.CheckConstraint(
                "(amount_mode = 'fixed' AND fixed_amount_cents > 0) OR "
                "(amount_mode = 'variable' AND fixed_amount_cents IS NULL)",
                name="recurring_amount_consistency",
            ),
            sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        )
    if not _index_exists(inspector, "recurring_expenses", "ix_recurring_expenses_active_due"):
        op.create_index(
            "ix_recurring_expenses_active_due", "recurring_expenses", ["active", "due_day"]
        )

    if "recurring_expense_occurrences" not in tables:
        op.create_table(
            "recurring_expense_occurrences",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("expense_id", sa.Integer(), nullable=False),
            sa.Column("reference_month", sa.Date(), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=False),
            sa.Column("amount_cents", sa.Integer(), nullable=True),
            sa.Column("paid", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("paid_on", sa.Date(), nullable=True),
            sa.Column("transaction_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint(
                "amount_cents IS NULL OR amount_cents > 0", name="occurrence_amount"
            ),
            sa.CheckConstraint(
                "(paid = 0 AND paid_on IS NULL) OR (paid = 1 AND paid_on IS NOT NULL)",
                name="occurrence_payment_consistency",
            ),
            sa.ForeignKeyConstraint(
                ["expense_id"], ["recurring_expenses.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("expense_id", "reference_month", name="uq_recurring_month"),
        )
    if not _index_exists(
        inspector,
        "recurring_expense_occurrences",
        "ix_recurring_occurrences_due_paid",
    ):
        op.create_index(
            "ix_recurring_occurrences_due_paid",
            "recurring_expense_occurrences",
            ["due_date", "paid"],
        )


def downgrade() -> None:
    op.drop_index(
        "ix_recurring_occurrences_due_paid", table_name="recurring_expense_occurrences"
    )
    op.drop_table("recurring_expense_occurrences")
    op.drop_index("ix_recurring_expenses_active_due", table_name="recurring_expenses")
    op.drop_table("recurring_expenses")


def _index_exists(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if table_name not in inspector.get_table_names():
        return False
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))
