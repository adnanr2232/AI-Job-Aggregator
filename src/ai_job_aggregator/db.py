from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from ai_job_aggregator.settings import Settings


def create_engine_from_settings(settings: Settings) -> Engine:
    return create_engine(
        settings.sqlalchemy_database_url(),
        future=True,
    )


def create_session_factory(engine: Engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
