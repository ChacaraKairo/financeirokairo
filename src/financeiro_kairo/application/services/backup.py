from __future__ import annotations

import shutil
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

    def restore_backup(self, source: Path) -> Path:
        source = source.expanduser().resolve()
        if not self.validate_backup(source):
            raise ValueError("backup file is invalid or corrupted")
        self.config.ensure_directories()
        safety_copy = self.create_backup(self.config.resolved_backup_dir / "before-restore")
        temporary = self.config.database_path.with_suffix(".restore.tmp")
        shutil.copy2(source, temporary)
        if not self.validate_backup(temporary):
            temporary.unlink(missing_ok=True)
            raise RuntimeError("restored copy failed integrity validation")
        temporary.replace(self.config.database_path)
        return safety_copy

    def rotate(self, *, keep: int = 30) -> list[Path]:
        if keep < 1:
            raise ValueError("keep must be at least one")
        directory = self.config.resolved_backup_dir
        directory.mkdir(parents=True, exist_ok=True)
        files = sorted(directory.glob("financeiro-kairo-*.sqlite3"), key=lambda item: item.stat().st_mtime, reverse=True)
        removed: list[Path] = []
        for path in files[keep:]:
            path.unlink(missing_ok=True)
            removed.append(path)
        return removed

    @staticmethod
    def validate_backup(path: Path) -> bool:
        path = Path(path)
        if not path.is_file():
            return False
        try:
            with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
                result = connection.execute("PRAGMA integrity_check").fetchone()
                return result is not None and result[0] == "ok"
        except sqlite3.Error:
            return False
