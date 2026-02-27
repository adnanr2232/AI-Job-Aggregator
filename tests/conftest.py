from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from alembic.config import Config


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.sqlite3"


@pytest.fixture()
def engine(db_path: Path):
    # Ensure app settings pick up this database when alembic env.py constructs Settings().
    os.environ["AJA_DB_PATH"] = str(db_path)
    # storage_dir not used when db_path is set, but set it anyway
    os.environ["AJA_STORAGE_DIR"] = str(db_path.parent)

    eng = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture()
def alembic_config() -> Config:
    root = Path(__file__).resolve().parents[1]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))
    return cfg


@pytest.fixture()
def migrated_db(engine, alembic_config: Config, db_path: Path):
    # Point alembic to the temp DB.
    alembic_config.set_main_option("sqlalchemy.url", f"sqlite+pysqlite:///{db_path}")
    command.upgrade(alembic_config, "head")
    return engine


@pytest.fixture()
def session(migrated_db) -> Session:
    SessionLocal = sessionmaker(bind=migrated_db, autoflush=False, autocommit=False, future=True)
    with SessionLocal() as s:
        yield s
