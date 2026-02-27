from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class JobPostingIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    source: str
    source_item_id: str

    title: str | None = None
    company: str | None = None
    url: str | None = None
    published_at: datetime | None = None

    raw: dict[str, Any] = {}


class JobPostingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    source_item_id: str
    title: str | None
    company: str | None
    url: str | None
    published_at: datetime | None
    raw: dict[str, Any]
