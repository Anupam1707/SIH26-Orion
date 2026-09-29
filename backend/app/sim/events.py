"""Deterministic priority queue for timed events (spec §7.2).

``step()`` is hourly but behaviour happens at second resolution, so agents schedule
events instead of acting directly. Ties on timestamp break on insertion order.
"""

from __future__ import annotations

import heapq
from datetime import datetime
from typing import Any, Callable


class EventQueue:
    def __init__(self) -> None:
        self._heap: list[tuple[datetime, int, Callable[..., None], tuple[Any, ...]]] = []
        self._seq = 0

    def schedule(self, ts: datetime, fn: Callable[..., None], *args: Any) -> None:
        """Run ``fn(ts, *args)`` at ``ts``."""
        heapq.heappush(self._heap, (ts, self._seq, fn, args))
        self._seq += 1

    def run_until(self, limit: datetime) -> int:
        """Execute, in timestamp order, every event with ``ts < limit``. Events may schedule more."""
        n = 0
        while self._heap and self._heap[0][0] < limit:
            ts, _, fn, args = heapq.heappop(self._heap)
            fn(ts, *args)
            n += 1
        return n

    def __len__(self) -> int:
        return len(self._heap)
