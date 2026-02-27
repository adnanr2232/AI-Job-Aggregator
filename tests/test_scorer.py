from __future__ import annotations

import pytest
from sqlalchemy import select

from ai_job_aggregator.models import CandidateProfile, JobPosting
from ai_job_aggregator.models.scoring import ScoreItem, ScoreItemStatus
from ai_job_aggregator.scoring.heuristic import score_job
from ai_job_aggregator.scoring.service import create_scoring_run, score_run


def test_heuristic_score_job_basic_matching():
    res = score_job(
        profile_skills=["Python", "SQL"],
        job_title="Python Engineer",
        company="Acme",
        url="https://example.com",
        raw={"desc": "We use python and postgres"},
    )
    assert res.reasons["counts"]["skills_total"] == 2
    assert "python" in res.skills_matched
    assert "sql" not in res.skills_matched
    assert 0.0 <= res.score <= 100.0


def test_heuristic_score_job_empty_skills_is_zero():
    res = score_job(
        profile_skills=[],
        job_title="Anything",
        company=None,
        url=None,
        raw={},
    )
    assert res.score == 0.0
    assert res.skills_matched == []
    assert res.skills_missing == []


def test_score_run_profile_not_found_raises(session):
    run = create_scoring_run(session=session, profile_id=9999, ingestion_run_id=None)
    session.commit()

    with pytest.raises(ValueError, match="candidate_profile not found"):
        score_run(session=session, run_id=run.id)


def test_score_run_job_not_found_raises(session):
    with pytest.raises(ValueError, match="scoring_run not found"):
        score_run(session=session, run_id=123456)


def test_score_run_creates_items_and_finishes(session):
    prof = CandidateProfile(
        label="me", name="Me", location="X", role="Dev", skills=["python", "sql"]
    )
    session.add(prof)
    session.flush()

    job = JobPosting(
        source="stub",
        source_item_id="1",
        title="Junior Python Dev",
        company="Acme",
        url="https://x",
        published_at=None,
        raw={"text": "python"},
    )
    session.add(job)
    session.commit()

    run = create_scoring_run(session=session, profile_id=prof.id, ingestion_run_id=None)
    session.commit()

    score_run(session=session, run_id=run.id)

    items = session.execute(select(ScoreItem)).scalars().all()
    assert len(items) == 1
    assert items[0].status == ScoreItemStatus.finished
    assert items[0].score is not None
    assert "python" in items[0].skills_matched
