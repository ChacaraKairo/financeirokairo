"""Cria o schema inicial completo.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-23
"""
from __future__ import annotations

from alembic import op

from financeiro_kairo.domain import models, planning_models  # noqa: F401
from financeiro_kairo.infrastructure.database.base import Base

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
