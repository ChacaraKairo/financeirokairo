from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import text

from financeiro_kairo.config import settings
from financeiro_kairo.infrastructure.database.session import engine

_READ_ONLY_PREFIXES = ("select", "with", "pragma", "explain")
_FORBIDDEN_IN_READ_ONLY = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|detach|vacuum|reindex)\b",
    re.IGNORECASE,
)
_TABLE_DESCRIPTIONS = {
    "accounts": "Contas financeiras cadastradas, incluindo carteira, banco, poupança, investimento e cartão de crédito.",
    "categories": "Categorias e subcategorias usadas para classificar receitas, despesas, compras e planejamentos.",
    "transactions": "Lançamentos financeiros de receitas, despesas e transferências vinculados a contas e categorias.",
    "brands": "Marcas de produtos identificadas no catálogo de compras.",
    "products": "Produtos normalizados usados para consolidar itens iguais comprados com descrições diferentes.",
    "product_variants": "Variações de produtos, como marca, embalagem, quantidade, unidade e código de barras.",
    "product_aliases": "Apelidos e descrições originais associadas a uma variação de produto para melhorar futuras importações.",
    "merchants": "Estabelecimentos comerciais encontrados nas compras importadas ou cadastradas.",
    "import_batches": "Lotes de importação processados, com hash, origem, situação e auditoria básica.",
    "purchases": "Compras registradas, com data, estabelecimento, conta, totais, origem e documento.",
    "purchase_items": "Itens individuais de cada compra, incluindo quantidade, preço, desconto e associação ao catálogo.",
    "price_observations": "Histórico de preços observados por produto, estabelecimento e data para comparação de valores.",
    "budgets": "Orçamentos por período, com limite planejado e categoria opcional.",
    "goals": "Metas financeiras com valor alvo, progresso atual, conta opcional e situação.",
    "goal_contributions": "Contribuições feitas para metas financeiras ao longo do tempo.",
    "recurrence_rules": "Regras antigas de recorrência usadas para gerar lançamentos financeiros recorrentes.",
    "installment_plans": "Planos de parcelamento com valor total, número de parcelas, conta e primeira data de vencimento.",
    "installments": "Parcelas geradas por cada plano, com vencimento, valor e situação de pagamento.",
    "recurring_expenses": "Cadastros de despesas recorrentes, fixas ou variáveis, com vencimento e lembrete.",
    "recurring_expense_occurrences": "Competências mensais das despesas recorrentes, com valor informado e pagamento.",
    "alembic_version": "Controle interno do Alembic com a versão atual das migrações aplicadas.",
    "sqlite_sequence": "Controle interno do SQLite para sequências de IDs autoincrementais.",
}


@dataclass(frozen=True, slots=True)
class SqlExecutionResult:
    columns: list[str]
    rows: list[list[Any]]
    affected_rows: int
    message: str


@dataclass(frozen=True, slots=True)
class DatabaseTable:
    name: str
    row_count: int
    description: str


@dataclass(frozen=True, slots=True)
class DatabaseTableData:
    name: str
    columns: list[str]
    rows: list[list[Any]]
    total_rows: int
    message: str


class SqlConsoleService:
    """Executa uma instrução SQL por vez, em modo leitura por padrão."""

    def execute(self, statement: str, *, allow_writes: bool = False, limit: int = 1_000) -> SqlExecutionResult:
        sql = statement.strip()
        if not sql:
            raise ValueError("Informe uma instrução SQL.")
        if limit < 1 or limit > 10_000:
            raise ValueError("O limite deve estar entre 1 e 10.000 linhas.")
        if not allow_writes:
            self._ensure_read_only(sql)

        with engine.begin() as connection:
            result = connection.execute(text(sql))
            if result.returns_rows:
                columns = list(result.keys())
                rows = [list(row) for row in result.fetchmany(limit)]
                message = f"Consulta concluída: {len(rows)} linha(s) exibida(s)."
                if len(rows) == limit:
                    message += " O limite configurado foi atingido."
                return SqlExecutionResult(columns, rows, len(rows), message)

            affected = max(result.rowcount or 0, 0)
            return SqlExecutionResult([], [], affected, f"Comando concluído: {affected} linha(s) afetada(s).")

    @staticmethod
    def _ensure_read_only(sql: str) -> None:
        normalized = re.sub(r"--.*?$|/\*.*?\*/", " ", sql, flags=re.MULTILINE | re.DOTALL).strip().lower()
        if not normalized.startswith(_READ_ONLY_PREFIXES) or _FORBIDDEN_IN_READ_ONLY.search(normalized):
            raise PermissionError(
                "O modo protegido aceita apenas SELECT, WITH, PRAGMA e EXPLAIN. "
                "Ative explicitamente a alteração de dados para outros comandos."
            )

    def tables(self, *, include_internal: bool = False) -> list[DatabaseTable]:
        where = "type = 'table'"
        if not include_internal:
            where += " AND name NOT LIKE 'sqlite_%'"
        with engine.connect() as connection:
            names = [
                str(row[0])
                for row in connection.execute(
                    text(f"SELECT name FROM sqlite_master WHERE {where} ORDER BY name")
                )
            ]
            return [
                DatabaseTable(
                    name=name,
                    row_count=self._table_row_count(connection, name),
                    description=self.table_description(name),
                )
                for name in names
            ]

    def table_data(self, table_name: str, *, limit: int = 500) -> DatabaseTableData:
        if limit < 1 or limit > 10_000:
            raise ValueError("O limite deve estar entre 1 e 10.000 linhas.")
        with engine.connect() as connection:
            self._ensure_existing_table(connection, table_name)
            identifier = self._quote_identifier(table_name)
            total_rows = self._table_row_count(connection, table_name)
            result = connection.execute(text(f"SELECT * FROM {identifier} LIMIT :limit"), {"limit": limit})
            columns = list(result.keys())
            rows = [list(row) for row in result.fetchmany(limit)]
        message = f"Tabela {table_name}: {len(rows)} de {total_rows} linha(s) exibida(s)."
        if len(rows) == limit and total_rows > limit:
            message += " O limite configurado foi atingido."
        return DatabaseTableData(table_name, columns, rows, total_rows, message)

    def schema_sql(self, *, include_internal: bool = False) -> str:
        lines: list[str] = []
        for table_info in self.tables(include_internal=include_internal):
            lines.append(f"CREATE TABLE {self._quote_identifier(table_info.name)} (")
            column_lines = [
                f"    {self._quote_identifier(column['name'])} {column['type'] or 'TEXT'}"
                for column in self.table_columns(table_info.name)
            ]
            lines.append(",\n".join(column_lines))
            lines.append(");\n")
        return "\n".join(lines).strip() + "\n"

    def table_columns(self, table_name: str) -> list[dict[str, Any]]:
        with engine.connect() as connection:
            self._ensure_existing_table(connection, table_name)
            rows = connection.execute(text(f"PRAGMA table_info({self._quote_identifier(table_name)})")).mappings().all()
            return [
                {
                    "name": str(row["name"]),
                    "type": str(row["type"] or ""),
                }
                for row in rows
            ]

    def copy_database_file(self, target: Path) -> Path:
        source = settings.database_path
        if not source.exists():
            raise FileNotFoundError(f"Banco SQLite não encontrado: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(source) as source_connection:
            with sqlite3.connect(target) as target_connection:
                source_connection.backup(target_connection)
        return target

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        if not identifier or "\x00" in identifier:
            raise ValueError("Nome de tabela inválido.")
        return '"' + identifier.replace('"', '""') + '"'

    def _ensure_existing_table(self, connection: Any, table_name: str) -> None:
        row = connection.execute(
            text("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = :name"),
            {"name": table_name},
        ).first()
        if row is None:
            raise LookupError(f"Tabela não encontrada: {table_name}")

    def _table_row_count(self, connection: Any, table_name: str) -> int:
        identifier = self._quote_identifier(table_name)
        return int(connection.execute(text(f"SELECT COUNT(*) FROM {identifier}")).scalar_one())

    @staticmethod
    def table_description(table_name: str) -> str:
        return _TABLE_DESCRIPTIONS.get(
            table_name,
            "Tabela do banco de dados local sem descrição cadastrada no aplicativo.",
        )
