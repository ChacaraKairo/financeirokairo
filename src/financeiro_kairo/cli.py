from __future__ import annotations

import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config

from financeiro_kairo.application.services.backup import BackupService
from financeiro_kairo.infrastructure.database.bootstrap import create_schema


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="financeiro-kairo")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-db", help="cria as tabelas do banco local")
    subparsers.add_parser("migrate", help="aplica todas as migrações pendentes")
    subparsers.add_parser("backup", help="cria e valida um backup SQLite")
    validate = subparsers.add_parser("validate-backup", help="valida um arquivo de backup")
    validate.add_argument("path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "init-db":
        create_schema()
        print("Banco inicializado com sucesso.")
        return
    if args.command == "migrate":
        command.upgrade(Config("alembic.ini"), "head")
        print("Migrações aplicadas com sucesso.")
        return
    if args.command == "backup":
        path = BackupService().create_backup()
        print(f"Backup criado: {path}")
        return
    if args.command == "validate-backup":
        valid = BackupService.validate_backup(Path(args.path))
        print("Backup válido." if valid else "Backup inválido.")
        raise SystemExit(0 if valid else 1)
    raise SystemExit(2)


if __name__ == "__main__":
    main()
