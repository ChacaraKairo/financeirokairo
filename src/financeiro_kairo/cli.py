from __future__ import annotations

import argparse

from financeiro_kairo.application.services.backup import BackupService
from financeiro_kairo.infrastructure.database.bootstrap import create_schema


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="financeiro-kairo")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-db", help="cria as tabelas do banco local")
    subparsers.add_parser("backup", help="cria e valida um backup SQLite")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "init-db":
        create_schema()
        print("Banco inicializado com sucesso.")
        return
    if args.command == "backup":
        path = BackupService().create_backup()
        print(f"Backup criado: {path}")
        return
    raise SystemExit(2)


if __name__ == "__main__":
    main()
