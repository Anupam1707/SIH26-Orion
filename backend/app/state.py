"""In-memory demo state.

Holds the demo clock and the precomputed world. ``reset()`` restores the snapshot taken at
startup; it never recomputes (spec Phase 6: reset must finish in under 5 seconds).

The world is large and read-only, so it is held by reference and is *not* part of the snapshot;
only the mutable demo state (clock, running flag, alerts, ...) is snapshotted.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class DemoState:
    cache_dir: Path
    manifest: dict
    world: Any = None  # app.sim.model.World; immutable after load
    public: Any = None
    analysis: dict = field(default_factory=dict)
    graphs: dict = field(default_factory=dict)
    predictions: dict = field(default_factory=dict)
    config: Any = None
    demo_clock: datetime | None = None
    demo_running: bool = False
    data: dict = field(default_factory=dict)
    _snapshot: dict | None = field(default=None, repr=False)

    def take_snapshot(self) -> None:
        self._snapshot = copy.deepcopy(
            {"demo_clock": self.demo_clock, "demo_running": self.demo_running, "data": self.data}
        )

    def reset(self) -> None:
        if self._snapshot is None:
            raise RuntimeError("reset() called before take_snapshot()")
        restored = copy.deepcopy(self._snapshot)
        self.demo_clock = restored["demo_clock"]
        self.demo_running = restored["demo_running"]
        self.data = restored["data"]
