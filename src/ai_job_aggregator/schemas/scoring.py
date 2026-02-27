from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ScoringRunCreate(BaseModel):
    profile_id: int
    ingestion_run_id: int | None = None
    meta: dict = Field(default_factory=dict)


class ScoringRunRead(BaseModel):
    id: int
    profile_id: int
    ingestion_run_id: int | None
    status: str
    started_at: datetime
    finished_at: datetime | None
    meta: dict


class ScoreItemRead(BaseModel):
    id: int
    scoring_run_id: int
    job_id: int
    status: str
    score: float | None
    skills_matched: list[str]
    skills_missing: list[str]
    reasons: dict
    error_id: int | None


class ScoreResult(BaseModel):
    score: float
    skills_matched: list[str]
    skills_missing: list[str]
    reasons: dict
