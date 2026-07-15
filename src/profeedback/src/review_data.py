from __future__ import annotations

import time
from functools import lru_cache

from aqt import mw

from .logging_utils import log_error


class TTLCache[V]:
    __slots__ = ("_store", "_ttl")

    def __init__(self, ttl: float = 30.0) -> None:
        self._store: dict[int, tuple[V, float]] = {}
        self._ttl: float = ttl

    def get(self, key: int) -> V | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, timestamp = entry
        if time.monotonic() - timestamp > self._ttl:
            del self._store[key]
            return None
        return value

    def put(self, key: int, value: V) -> None:
        self._store[key] = (value, time.monotonic())

    def clear(self) -> None:
        self._store.clear()


@lru_cache(maxsize=512)
def fetch_review_history(card_id: int, limit: int) -> tuple[int, ...]:
    try:
        rows: list[list[int]] = mw.col.db.all(
            "SELECT ease FROM revlog WHERE cid=? ORDER BY id DESC LIMIT ?",
            card_id,
            limit,
        )
        return tuple(ease for (ease,) in rows)
    except Exception as error:
        log_error("fetch_review_history", error)
        return ()


def node_has_due(node: object) -> bool:
    return bool(
        getattr(node, "review_count", 0)
        or getattr(node, "learn_count", 0)
        or getattr(node, "new_count", 0)
        or any(node_has_due(child) for child in getattr(node, "children", []))
    )


def clear_history_cache() -> None:
    fetch_review_history.cache_clear()
