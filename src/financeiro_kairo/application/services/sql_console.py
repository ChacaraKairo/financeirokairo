from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from financeiro_kairo.infrastructure.database.session import engine

_READ_ONLY_PREFIXES = ("select", "with", "pragma", "explain")
_FORBIDDEN_IN_READ_ONLY = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|detach|vacuum|reindex)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class SqlExecutionResult:
    columns: list[str]
    rows: list[list[Any]]
    affected_rows: int
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
