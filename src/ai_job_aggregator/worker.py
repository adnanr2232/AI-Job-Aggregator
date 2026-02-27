from __future__ import annotations

import logging
from typing import Any

from rq import Worker

from ai_job_aggregator.rq import redis_connection

logger = logging.getLogger(__name__)


def run_worker() -> None:
    conn: Any = redis_connection()
    with conn:
        worker = Worker(["scoring"])
        logger.info("rq_worker_starting", extra={"queues": ["scoring"]})
        worker.work(with_scheduler=False)
