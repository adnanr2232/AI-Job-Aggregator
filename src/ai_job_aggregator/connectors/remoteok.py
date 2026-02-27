from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import UTC, datetime

import httpx

from ai_job_aggregator.schemas.job import JobPostingIn
from ai_job_aggregator.settings import Settings


class RemoteOkConnector:
    source = "remoteok"

    def __init__(self, settings: Settings):
        self._settings = settings

    def fetch(self) -> Iterable[JobPostingIn]:
        headers = {"User-Agent": "ai-job-aggregator/0.1 (+https://github.com/)"}
        with httpx.Client(timeout=30.0, headers=headers) as client:
            # noise reduction: we do our own JSON logging
            logging.getLogger("httpx").setLevel(logging.WARNING)
            r = client.get(self._settings.remoteok_url)
            r.raise_for_status()
            data = r.json()

        if not isinstance(data, list):
            raise ValueError("RemoteOK response is not a list")

        # API returns first row as metadata/legal.
        for row in data[1:]:
            if not isinstance(row, dict):
                continue
            job_id = row.get("id")
            if job_id is None:
                continue

            published_at = None
            epoch = row.get("epoch")
            if isinstance(epoch, int | float):
                published_at = datetime.fromtimestamp(epoch, tz=UTC)

            yield JobPostingIn(
                source=self.source,
                source_item_id=str(job_id),
                title=row.get("position"),
                company=row.get("company"),
                url=row.get("url"),
                published_at=published_at,
                raw=row,  # keep full payload
            )
