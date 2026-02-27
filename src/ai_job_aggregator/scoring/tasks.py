from __future__ import annotations

import logging

from ai_job_aggregator.db import create_engine_from_settings, create_session_factory
from ai_job_aggregator.scoring.service import score_run
from ai_job_aggregator.settings import Settings

logger = logging.getLogger(__name__)


def score_run_task(*, run_id: int) -> None:
    settings = Settings()
    engine = create_engine_from_settings(settings)
    SessionFactory = create_session_factory(engine)

    with SessionFactory() as session:
        score_run(session=session, run_id=run_id)

    logger.info("rq_score_run_completed", extra={"run_id": run_id})
