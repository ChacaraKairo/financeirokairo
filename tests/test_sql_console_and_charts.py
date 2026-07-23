from __future__ import annotations

from datetime import date

import pytest
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine

from financeiro_kairo.application.services import sql_console
from financeiro_kairo.application.services.sql_console import SqlConsoleService
from financeiro_kairo.presentation.app import ChartsPage, SqlConsolePage, translate


class FakeFacade:
    def dashboard(self, start: date, end: date):
        return {
            "balance_cents": 100_000,
            "income_cents": 50_000,
            "expense_cents": 30_000,
            "net_cents": 20_000,
            "categories": [("Alimentação", 20_000), ("Transporte", 10_000)],
        }


def test_sql_console_read_only_and_write_protection(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    monkeypatch.setattr(sql_console, "engine", engine)
    service = SqlConsoleService()

    result = service.execute("SELECT 1 AS numero")
    assert result.columns == ["numero"]
    assert result.rows == [[1]]

    with pytest.raises(PermissionError):
        service.execute("CREATE TABLE teste (id INTEGER)")

    service.execute("CREATE TABLE teste (id INTEGER)", allow_writes=True)
    service.execute("INSERT INTO teste (id) VALUES (7)", allow_writes=True)
    assert service.execute("SELECT id FROM teste").rows == [[7]]


def test_portuguese_translation_and_graph_types(qapp):
    assert translate("credit_card") == "Cartão de crédito"
    assert translate("expense") == "Despesa"

    page = ChartsPage(FakeFacade())
    for chart_type in ["Pizza", "Barras", "Linha"]:
        page.chart_type.setCurrentText(chart_type)
        page.refresh()
        assert page.chart_view.chart().series()

    sql_page = SqlConsolePage()
    assert sql_page.allow_writes.text() == "Permitir comandos que alteram dados"


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    return app
