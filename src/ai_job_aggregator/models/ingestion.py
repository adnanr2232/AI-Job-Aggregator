from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class RunStatus(enum.StrEnum):
    started = "started"
    finished = "finished"
    failed = "failed"


class ItemStatus(enum.StrEnum):
    ok = "ok"
    error = "error"
    skipped = "skipped"


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.started)

    # Optional candidate context (no scoring yet; just association + snapshot in meta)
    profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_profiles.id"), nullable=True, index=True
    )

    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    items: Mapped[list[IngestionItem]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class IngestionItem(Base):
    __tablename__ = "ingestion_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("ingestion_runs.id"), index=True)

    # item identifier within source (e.g., RemoteOK job id)
    source_item_id: Mapped[str] = mapped_column(String(128), index=True)

    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus), default=ItemStatus.ok)

    # optional linkage to canonical job posting
    job_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_postings.id"), nullable=True, index=True
    )

    raw: Mapped[dict] = mapped_column(JSON, default=dict)

    error: Mapped[IngestionError | None] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
    run: Mapped[IngestionRun] = relationship(back_populates="items")


class IngestionError(Base):
    __tablename__ = "ingestion_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("ingestion_items.id"), index=True, unique=True)

    error_type: Mapped[str] = mapped_column(String(128))
    message: Mapped[str] = mapped_column(Text)
    traceback: Mapped[str | None] = mapped_column(Text, nullable=True)

    data: Mapped[dict] = mapped_column(JSON, default=dict)

    item: Mapped[IngestionItem] = relationship(back_populates="error")
