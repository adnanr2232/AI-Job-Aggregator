from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from ai_job_aggregator.models.base import Base


class ScoringRunStatus(enum.StrEnum):
    started = "started"
    finished = "finished"
    failed = "failed"


class ScoreItemStatus(enum.StrEnum):
    started = "started"
    finished = "finished"
    failed = "failed"


class ScoringRun(Base):
    __tablename__ = "scoring_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    profile_id: Mapped[int] = mapped_column(ForeignKey("candidate_profiles.id"), index=True)
    ingestion_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("ingestion_runs.id"), index=True, nullable=True
    )

    status: Mapped[ScoringRunStatus] = mapped_column(index=True)
    started_at: Mapped[datetime] = mapped_column(index=True)
    finished_at: Mapped[datetime | None] = mapped_column(index=True, nullable=True)

    meta: Mapped[dict] = mapped_column(JSON, default=dict)


class ScoringError(Base):
    __tablename__ = "scoring_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("score_items.id"), index=True)

    error_type: Mapped[str] = mapped_column(index=True)
    message: Mapped[str]
    traceback: Mapped[str]
    data: Mapped[dict] = mapped_column(JSON, default=dict)


class ScoreItem(Base):
    __tablename__ = "score_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    scoring_run_id: Mapped[int] = mapped_column(ForeignKey("scoring_runs.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"), index=True)

    status: Mapped[ScoreItemStatus] = mapped_column(index=True)

    score: Mapped[float | None] = mapped_column(nullable=True)
    skills_matched: Mapped[list[str]] = mapped_column(JSON, default=list)
    skills_missing: Mapped[list[str]] = mapped_column(JSON, default=list)
    reasons: Mapped[dict] = mapped_column(JSON, default=dict)

    error_id: Mapped[int | None] = mapped_column(
        ForeignKey("scoring_errors.id"), index=True, nullable=True
    )
