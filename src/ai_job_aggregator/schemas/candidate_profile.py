from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateProfileIn(BaseModel):
    """Semi-structured candidate profile payload.

    Keep this separate from the DB model so we can evolve the DB schema without
    locking the API/CLI shape.
    """

    label: str | None = None
    name: str | None = None
    location: str | None = None
    role: str | None = None
    skills: list[str] = Field(default_factory=list)

    # free-form
    data: dict = Field(default_factory=dict)
