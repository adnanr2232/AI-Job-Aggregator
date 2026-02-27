from __future__ import annotations

import os

from redis import Redis


def redis_url() -> str:
    return os.environ.get("AJA_REDIS_URL", "redis://localhost:6379/0")


def redis_connection() -> Redis:
    return Redis.from_url(redis_url())


def redis_available() -> bool:
    try:
        return bool(redis_connection().ping())
    except Exception:  # noqa: BLE001
        return False
