from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ai_job_aggregator.connectors.remoteok import RemoteOkConnector
from ai_job_aggregator.settings import Settings


class _FakeResponse:
    def __init__(self, payload, *, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, payload):
        self._payload = payload
        self.requested_url: str | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url: str):
        self.requested_url = url
        return _FakeResponse(self._payload)


def test_remoteok_fetch_parses_jobs_without_network(monkeypatch: pytest.MonkeyPatch):
    payload = [
        {"legal": "meta"},
        {
            "id": 123,
            "position": "Python Developer",
            "company": "Acme",
            "url": "https://remoteok.com/remote-jobs/123",
            "epoch": 1700000000,
        },
        {"id": None, "position": "skip"},
        "not-a-dict",
    ]

    def _fake_httpx_client(*args, **kwargs):
        return _FakeClient(payload)

    monkeypatch.setattr("ai_job_aggregator.connectors.remoteok.httpx.Client", _fake_httpx_client)

    settings = Settings(remoteok_url="https://example.test/api")
    conn = RemoteOkConnector(settings)
    jobs = list(conn.fetch())

    assert len(jobs) == 1
    job = jobs[0]
    assert job.source == "remoteok"
    assert job.source_item_id == "123"
    assert job.title == "Python Developer"
    assert job.company == "Acme"
    assert job.url == "https://remoteok.com/remote-jobs/123"
    assert isinstance(job.published_at, datetime)
    assert job.published_at.tzinfo == UTC
    assert job.raw["id"] == 123


def test_remoteok_fetch_raises_on_non_list_json(monkeypatch: pytest.MonkeyPatch):
    def _fake_httpx_client(*args, **kwargs):
        return _FakeClient({"not": "a list"})

    monkeypatch.setattr("ai_job_aggregator.connectors.remoteok.httpx.Client", _fake_httpx_client)

    conn = RemoteOkConnector(Settings(remoteok_url="https://example.test/api"))
    with pytest.raises(ValueError, match="not a list"):
        list(conn.fetch())
