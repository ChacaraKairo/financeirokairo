from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from financeiro_kairo.config import Settings, settings


class BackupService:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config

    def create_backup(self, destination: Path | None = None) -> Path:
        self.config.ensure_directories()
        target_dir = destination or self.config.resolved_backup_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = target_dir / f"financeiro-kairo-{timestamp}.sqlite3"

        with sqlite3.connect(self.config.database_path) as source:
            with sqlite3.connect(target) as backup:
                source.backup(backup)
                result = backup.execute("PRAGMA integrity_check").fetchone()
                if result is None or result[0] != "ok":
                    raise RuntimeError("backup integrity check failed")
        return target

    @staticmethod
    def validate_backup(path: Path) -> bool:
        if not path.is_file():
            return False
        try:
            with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
                result = connection.execute("PRAGMA integrity_check").fetchone()
                return result is not None and result[0] == "ok"
        except sqlite3.Error:
            return False
