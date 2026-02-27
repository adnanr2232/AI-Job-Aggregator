from __future__ import annotations

import logging
import traceback as tb_mod
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_job_aggregator.connectors.base import JobConnector
from ai_job_aggregator.models.ingestion import (
    IngestionError,
    IngestionItem,
    IngestionRun,
    ItemStatus,
    RunStatus,
)
from ai_job_aggregator.models.job import JobPosting

logger = logging.getLogger(__name__)


def run_ingestion(*, session: Session, connector: JobConnector) -> int:
    run = IngestionRun(
        source=connector.source,
        started_at=datetime.now(tz=UTC),
        status=RunStatus.started,
        meta={},
    )
    session.add(run)
    session.commit()

    logger.info("ingestion_run_started", extra={"run_id": run.id, "source": connector.source})

    ok_count = 0
    err_count = 0
    skipped_count = 0

    try:
        for job in connector.fetch():
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
            "ok": ok_count,
            "skipped": skipped_count,
            "error": err_count,
        }
        session.commit()
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
            "ok": ok_count,
            "skipped": skipped_count,
            "error": err_count,
            "fatal": {"error_type": type(e).__name__, "message": str(e)},
        }
        session.commit()
        logger.error(
            "ingestion_run_failed",
            extra={"run_id": run.id, "source": connector.source, "error_type": type(e).__name__},
            exc_info=True,
        )
        return 2
