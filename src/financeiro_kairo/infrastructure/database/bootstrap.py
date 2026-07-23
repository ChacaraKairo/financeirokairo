from sqlalchemy import Engine

from financeiro_kairo.domain import models, planning_models, recurring_expenses  # noqa: F401
from financeiro_kairo.infrastructure.database.base import Base
from financeiro_kairo.infrastructure.database.session import engine


def create_schema(target_engine: Engine = engine) -> None:
    Base.metadata.create_all(target_engine)
