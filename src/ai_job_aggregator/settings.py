from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AJA_",
        env_file=(".env", ".env.local"),
        extra="ignore",
    )

    # Root storage directory (set via AJA_STORAGE_DIR)
    storage_dir: Path = Path.home() / "Desktop" / "job-aggregator"

    # SQLite database path inside storage_dir by default
    db_path: Path | None = None

    # RemoteOK API endpoint
    remoteok_url: str = "https://remoteok.com/api"

    def resolved_db_path(self) -> Path:
        return self.db_path or (self.storage_dir / "data" / "jobs.sqlite3")

    def sqlalchemy_database_url(self) -> str:
        p = self.resolved_db_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+pysqlite:///{p}"
