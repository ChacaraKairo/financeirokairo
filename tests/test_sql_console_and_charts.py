from __future__ import annotations

from datetime import date

import pytest
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine

from financeiro_kairo.application.services import sql_console
from financeiro_kairo.application.services.sql_console import SqlConsoleService
from financeiro_kairo.presentation.app import (
    ChartsPage,
    DatabaseBrowserPage,
    SqlConsolePage,
    translate,
)


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


def test_database_browser_lists_and_reads_tables(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    monkeypatch.setattr(sql_console, "engine", engine)
    service = SqlConsoleService()
    service.execute("CREATE TABLE contas (id INTEGER, nome TEXT)", allow_writes=True)
    service.execute("INSERT INTO contas (id, nome) VALUES (1, 'Carteira')", allow_writes=True)

    tables = service.tables()
    assert tables == [
        sql_console.DatabaseTable(
            name="contas",
            row_count=1,
            description="Tabela do banco de dados local sem descrição cadastrada no aplicativo.",
        )
    ]
    assert "Lançamentos financeiros" in service.table_description("transactions")

    data = service.table_data("contas")
    assert data.columns == ["id", "nome"]
    assert data.rows == [[1, "Carteira"]]
    assert data.total_rows == 1

    schema = service.schema_sql()
    assert 'CREATE TABLE "contas" (' in schema
    assert '    "id" INTEGER' in schema
    assert '    "nome" TEXT' in schema
    assert "Carteira" not in schema


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

    database_page = DatabaseBrowserPage()
    assert database_page.limit.value() == 500


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    return app
