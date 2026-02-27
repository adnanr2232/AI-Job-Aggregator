from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Optional extracted fields for convenience
    label: Mapped[str | None] = mapped_column(String(128), unique=True, index=True, nullable=True)
    name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    role: Mapped[str | None] = mapped_column(String(256), nullable=True)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Semi-structured canonical payload
    data: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
