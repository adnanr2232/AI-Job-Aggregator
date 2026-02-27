from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from ai_job_aggregator.schemas.job import JobPostingIn


@dataclass(frozen=True)
class ConnectorResult:
    jobs: list[JobPostingIn]


class JobConnector(Protocol):
    source: str

    def fetch(self) -> Iterable[JobPostingIn]: ...
