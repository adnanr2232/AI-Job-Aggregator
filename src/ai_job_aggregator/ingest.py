from __future__ import annotations

import logging
import traceback as tb_mod
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_job_aggregator.connectors.base import JobConnector
from ai_job_aggregator.models.candidate_profile import CandidateProfile
from ai_job_aggregator.models.ingestion import (
    IngestionError,
    IngestionItem,
    IngestionRun,
    ItemStatus,
    RunStatus,
)
from ai_job_aggregator.models.job import JobPosting
from ai_job_aggregator.settings import Settings

logger = logging.getLogger(__name__)


HARD_CAP_MAX_FETCH_PER_CONNECTOR = 100


def _clamp_fetch_limit(*, settings_limit: int, cli_limit: int | None) -> int:
    # Prefer explicit CLI limit if provided.
    raw = cli_limit if cli_limit is not None else settings_limit
    if raw <= 0:
        return 0
    return min(raw, HARD_CAP_MAX_FETCH_PER_CONNECTOR)


def run_ingestion(
    *,
    session: Session,
    connector: JobConnector,
    limit: int | None = None,
    profile_selector: str | None = None,
) -> int:
    run = IngestionRun(
        source=connector.source,
        started_at=datetime.now(tz=UTC),
        status=RunStatus.started,
        meta={},
    )
    # Candidate profile selection (optional)
    if profile_selector:
        # selector can be numeric id or string label
        prof = None
        if profile_selector.isdigit():
            prof = session.get(CandidateProfile, int(profile_selector))
        if prof is None:
            prof = session.execute(
                select(CandidateProfile).where(CandidateProfile.label == profile_selector)
            ).scalar_one_or_none()

        if prof is not None:
            run.profile_id = prof.id
            run.meta = {
                **(run.meta or {}),
                "profile": {
                    "id": prof.id,
                    "label": prof.label,
                    "name": prof.name,
                    "location": prof.location,
                    "role": prof.role,
                    "skills": prof.skills,
                },
            }
        else:
            run.meta = {**(run.meta or {}), "profile": {"selector": profile_selector}}

    session.add(run)
    session.commit()

    logger.info(
        "ingestion_run_started",
        extra={"run_id": run.id, "source": connector.source, "profile": profile_selector},
    )

    ok_count = 0
    err_count = 0
    skipped_count = 0

    try:
        settings = Settings()
        fetch_limit = _clamp_fetch_limit(
            settings_limit=settings.max_fetch_per_connector,
            cli_limit=limit,
        )

        if fetch_limit == 0:
            logger.info(
                "ingestion_run_noop_limit",
                extra={"run_id": run.id, "source": connector.source, "limit": fetch_limit},
            )
            run.status = RunStatus.finished
            run.finished_at = datetime.now(tz=UTC)
            run.meta = {
                **(run.meta or {}),
                "ok": ok_count,
                "skipped": skipped_count,
                "error": err_count,
                "limit": fetch_limit,
            }
            session.commit()
            return 0

        for idx, job in enumerate(connector.fetch()):
            if idx >= fetch_limit:
                break
            source_item_id = job.source_item_id
            item = IngestionItem(
                run_id=run.id,
                source_item_id=source_item_id,
                status=ItemStatus.ok,
                raw=job.raw,
            )
            session.add(item)
            session.flush()  # to get item.id

            try:
                existing = session.execute(
                    select(JobPosting).where(
                        JobPosting.source == job.source,
                        JobPosting.source_item_id == job.source_item_id,
                    )
                ).scalar_one_or_none()

                if existing is not None:
                    item.status = ItemStatus.skipped
                    item.job_id = existing.id
                    skipped_count += 1
                else:
                    jp = JobPosting(
                        source=job.source,
                        source_item_id=job.source_item_id,
                        title=job.title,
                        company=job.company,
                        url=job.url,
                        published_at=job.published_at,
                        raw=job.raw,
                    )
                    session.add(jp)
                    session.flush()
                    item.job_id = jp.id
                    ok_count += 1
            except Exception as e:  # noqa: BLE001
                item.status = ItemStatus.error
                err = IngestionError(
                    item_id=item.id,
                    error_type=type(e).__name__,
                    message=str(e),
                    traceback=tb_mod.format_exc(),
                    data={"source": job.source, "source_item_id": job.source_item_id},
                )
                session.add(err)
                err_count += 1

            session.commit()

        run.status = RunStatus.finished
        run.finished_at = datetime.now(tz=UTC)
        run.meta = {
            **(run.meta or {}),
            "ok": ok_count,
            "skipped": skipped_count,
            "error": err_count,
            "limit": fetch_limit,
        }
        session.commit()

        # enqueue scoring asynchronously for profile-bound ingestion runs
        if run.profile_id is not None:
            try:
                from ai_job_aggregator.scoring.enqueue import enqueue_scoring_run
                from ai_job_aggregator.scoring.service import create_scoring_run

                scoring_run = create_scoring_run(
                    session=session,
                    profile_id=run.profile_id,
                    ingestion_run_id=run.id,
                    meta={"source": connector.source},
                )
                session.commit()
                enqueue_scoring_run(run_id=scoring_run.id)
            except Exception:  # noqa: BLE001
                logger.warning(
                    "scoring_enqueue_failed",
                    extra={"ingestion_run_id": run.id, "profile_id": run.profile_id},
                    exc_info=True,
                )

        logger.info(
            "ingestion_run_finished",
            extra={
                "run_id": run.id,
                "source": connector.source,
                "ok": ok_count,
                "skipped": skipped_count,
                "error": err_count,
            },
        )
        return 0

    except Exception as e:  # noqa: BLE001
        run.status = RunStatus.failed
        run.finished_at = datetime.now(tz=UTC)
        run.meta = {
            **(run.meta or {}),
            "ok": ok_count,
            "skipped": skipped_count,
            "error": err_count,
            "fatal": {"error_type": type(e).__name__, "message": str(e)},
            "limit": locals().get("fetch_limit", None),
        }
        session.commit()
        logger.error(
            "ingestion_run_failed",
            extra={"run_id": run.id, "source": connector.source, "error_type": type(e).__name__},
            exc_info=True,
        )
        return 2
