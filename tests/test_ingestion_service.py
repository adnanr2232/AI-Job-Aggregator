from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from ai_job_aggregator.ingest import run_ingestion
from ai_job_aggregator.models.ingestion import (
    IngestionItem,
    IngestionRun,
    ItemStatus,
    RunStatus,
)
from ai_job_aggregator.models.job import JobPosting
from ai_job_aggregator.schemas.job import JobPostingIn


class _StubConnector:
    source = "stub"

    def __init__(self, items):
        self._items = items

    def fetch(self):
        yield from self._items


def test_run_ingestion_dedups_and_tracks_statuses(session):
    now = datetime(2025, 1, 1, tzinfo=UTC)

    items = [
        JobPostingIn(
            source="stub",
            source_item_id="1",
            title="A",
            company="C",
            url="https://x/1",
            published_at=now,
            raw={"id": 1},
        ),
        JobPostingIn(
            source="stub",
            source_item_id="1",
            title="A2",
            company="C",
            url="https://x/1b",
            published_at=now,
            raw={"id": 1, "dup": True},
        ),
    ]

    rc = run_ingestion(session=session, connector=_StubConnector(items), limit=10)
    assert rc == 0

    run = session.execute(select(IngestionRun)).scalar_one()
    assert run.status == RunStatus.finished
    assert run.meta["ok"] == 1
    assert run.meta["skipped"] == 1
    assert run.meta["error"] == 0

    jobs = session.execute(select(JobPosting)).scalars().all()
    assert len(jobs) == 1

    ing_items = session.execute(select(IngestionItem).order_by(IngestionItem.id)).scalars().all()
    assert [it.status for it in ing_items] == [ItemStatus.ok, ItemStatus.skipped]
    assert ing_items[0].job_id == jobs[0].id
    assert ing_items[1].job_id == jobs[0].id


def test_run_ingestion_captures_error_for_malformed_item(session):
    # Missing required fields (e.g., source_item_id) will raise when accessed.
    class _Bad:
        source = "stub"
        raw = {"oops": True}

        @property
        def source_item_id(self):
            raise KeyError("source_item_id")

        title = "T"
        company = "C"
        url = "U"
        published_at = None

    rc = run_ingestion(session=session, connector=_StubConnector([_Bad()]), limit=10)
    assert rc == 2

    run = session.execute(select(IngestionRun)).scalar_one()
    assert run.status == RunStatus.failed
    assert run.meta["fatal"]["error_type"] in {"KeyError"}

    # No item is created since it fails before IngestionItem construction.
    assert session.execute(select(IngestionItem)).scalars().all() == []


def test_run_ingestion_noop_on_zero_limit(session):
    rc = run_ingestion(session=session, connector=_StubConnector([]), limit=0)
    assert rc == 0

    run = session.execute(select(IngestionRun)).scalar_one()
    assert run.status == RunStatus.finished
    assert run.meta["limit"] == 0
