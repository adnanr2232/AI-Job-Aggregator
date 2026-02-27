from __future__ import annotations

import logging

from rq import Queue

from ai_job_aggregator.rq import redis_available, redis_connection
from ai_job_aggregator.scoring.tasks import score_run_task

logger = logging.getLogger(__name__)


def enqueue_scoring_run(*, run_id: int) -> bool:
    if not redis_available():
        logger.warning("redis_unavailable_scoring_skipped", extra={"run_id": run_id})
        return False

    q = Queue("scoring", connection=redis_connection())
    q.enqueue(score_run_task, run_id=run_id)
    logger.info("scoring_enqueued", extra={"run_id": run_id})
    return True
