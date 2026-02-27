from __future__ import annotations

import logging
import traceback as tb
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_job_aggregator.models import CandidateProfile, JobPosting
from ai_job_aggregator.models.scoring import (
    ScoreItem,
    ScoreItemStatus,
    ScoringError,
    ScoringRun,
    ScoringRunStatus,
)
from ai_job_aggregator.scoring.heuristic import score_job

logger = logging.getLogger(__name__)


def create_scoring_run(
    *,
    session: Session,
    profile_id: int,
    ingestion_run_id: int | None,
    meta: dict | None = None,
) -> ScoringRun:
    run = ScoringRun(
        profile_id=profile_id,
        ingestion_run_id=ingestion_run_id,
        status=ScoringRunStatus.started,
        started_at=datetime.utcnow(),
        finished_at=None,
        meta=meta or {},
    )
    session.add(run)
    session.flush()
    return run


def score_run(*, session: Session, run_id: int) -> None:
    run = session.get(ScoringRun, run_id)
    if not run:
        raise ValueError(f"scoring_run not found: {run_id}")

    profile = session.get(CandidateProfile, run.profile_id)
    if not profile:
        raise ValueError(f"candidate_profile not found: {run.profile_id}")

    jobs = session.execute(select(JobPosting)).scalars().all()

    for job in jobs:
        item = ScoreItem(
            scoring_run_id=run.id,
            job_id=job.id,
            status=ScoreItemStatus.started,
            score=None,
            skills_matched=[],
            skills_missing=[],
            reasons={},
            error_id=None,
        )
        session.add(item)
        session.flush()

        try:
            res = score_job(
                profile_skills=profile.skills,
                job_title=job.title,
                company=job.company,
                url=job.url,
                raw=job.raw,
            )
            item.status = ScoreItemStatus.finished
            item.score = float(res.score)
            item.skills_matched = res.skills_matched
            item.skills_missing = res.skills_missing
            item.reasons = res.reasons
        except Exception as e:  # noqa: BLE001
            err = ScoringError(
                item_id=item.id,
                error_type=type(e).__name__,
                message=str(e),
                traceback="".join(tb.format_exc()),
                data={"job_id": job.id, "run_id": run.id},
            )
            session.add(err)
            session.flush()

            item.status = ScoreItemStatus.failed
            item.error_id = err.id

        session.commit()

    run.status = ScoringRunStatus.finished
    run.finished_at = datetime.utcnow()
    session.commit()

    logger.info("scoring_finished", extra={"run_id": run.id, "profile_id": run.profile_id})
