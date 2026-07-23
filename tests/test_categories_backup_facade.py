from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pytest

from financeiro_kairo.application.facade import ApplicationFacade
from financeiro_kairo.application.services.backup import BackupService
from financeiro_kairo.application.services.categories import CategoryService
from financeiro_kairo.config import Settings
from financeiro_kairo.domain.models import CategoryKind


def test_category_hierarchy_archive_and_cycle_protection(session):
    service = CategoryService(session)
    parent = service.create(name="Alimentação", kind=CategoryKind.EXPENSE.value)
    child = service.create(
        name="Mercado",
        kind=CategoryKind.EXPENSE.value,
        parent_id=parent.id,
    )
    assert child.parent_id == parent.id

    with pytest.raises(ValueError, match="cycles"):
        service.update(parent.id, parent_id=child.id)

    service.archive(child.id)
    assert child.active is False
    service.restore(child.id)
    assert child.active is True


def test_backup_restore_preserves_current_database(tmp_path: Path):
    config = Settings(data_dir=tmp_path / "data", backup_dir=tmp_path / "backups")
    config.ensure_directories()
    with sqlite3.connect(config.database_path) as connection:
        connection.execute("CREATE TABLE sample (value TEXT NOT NULL)")
        connection.execute("INSERT INTO sample VALUES ('original')")

    service = BackupService(config)
    backup = service.create_backup()
    with sqlite3.connect(config.database_path) as connection:
        connection.execute("UPDATE sample SET value='changed'")

    safety = service.restore_backup(backup)
    assert safety.is_file()
    with sqlite3.connect(config.database_path) as connection:
        value = connection.execute("SELECT value FROM sample").fetchone()[0]
    assert value == "original"


def test_facade_end_to_end_with_isolated_session(monkeypatch, session):
    from contextlib import contextmanager

    @contextmanager
    def fake_scope():
        yield session

    monkeypatch.setattr("financeiro_kairo.application.facade.session_scope", fake_scope)
    facade = ApplicationFacade()
    account_id = facade.create_account(
        name="Carteira",
        account_type="cash",
        initial_balance_cents=10_000,
    )
    category_id = facade.create_category(name="Lazer", kind="expense")
    facade.create_transaction(
        transaction_type="expense",
        description="Cinema",
        amount_cents=2_500,
        occurred_on=date(2026, 7, 23),
        account_id=account_id,
        category_id=category_id,
    )
    accounts = facade.accounts()
    rows, total = facade.transactions(search_text="Cinema")
    assert accounts[0]["balance_cents"] == 7_500
    assert total == 1
    assert rows[0]["category_id"] == category_id
