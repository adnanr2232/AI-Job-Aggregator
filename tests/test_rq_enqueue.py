from __future__ import annotations

import ai_job_aggregator.scoring.enqueue as enq


def test_enqueue_scoring_run_redis_unavailable_does_not_crash(monkeypatch):
    monkeypatch.setattr(enq, "redis_available", lambda: False)

    ok = enq.enqueue_scoring_run(run_id=1)

    assert ok is False
