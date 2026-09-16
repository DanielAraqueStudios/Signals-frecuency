"""In-memory result store, process lifetime only -- see README.md for why
that's an intentional, documented simplification for this LAN/demo mode
(no DB, no persistence across restarts)."""

from __future__ import annotations

from threading import Lock
from typing import Optional

_results: dict[str, dict] = {}
_latest_id: Optional[str] = None
_lock = Lock()


def save_result(sample_id: str, result: dict) -> None:
    global _latest_id
    with _lock:
        _results[sample_id] = result
        _latest_id = sample_id


def get_result(sample_id: str) -> Optional[dict]:
    with _lock:
        return _results.get(sample_id)


def get_latest_result() -> Optional[dict]:
    with _lock:
        if _latest_id is None:
            return None
        return _results.get(_latest_id)
