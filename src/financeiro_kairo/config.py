from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FINANCEIRO_KAIRO_",
        env_file=".env",
        extra="ignore",
    )

    data_dir: Path = Field(default_factory=lambda: Path.home() / ".local/share/financeiro-kairo")
    database_name: str = "financeiro-kairo.sqlite3"
    backup_dir: Path | None = None
    sqlite_echo: bool = False

    @property
    def database_path(self) -> Path:
        return self.data_dir / self.database_name

    @property
    def database_url(self) -> str:
        return f"sqlite+pysqlite:///{self.database_path}"

    @property
    def resolved_backup_dir(self) -> Path:
        return self.backup_dir or self.data_dir / "backups"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.resolved_backup_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
