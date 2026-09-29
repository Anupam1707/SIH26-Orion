"""FastAPI entry point. Loads the precompute cache once at startup."""

from __future__ import annotations

import logging
import os
import pickle
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI

from app.api import alerts, blocking, districts, health, investigation, predictions
from app.data import Public
from app.graph.builder import build_graph
from app.sim.scenario import Scenario
from app.precompute import ANALYSIS_FILE, PREDICTIONS_FILE
from app.precompute import DEFAULT_CACHE_ROOT, DEFAULT_SCENARIO, WORLD_FILE, load_or_build
from app.sim.runner import load_world
from app.state import DemoState

log = logging.getLogger("muletrail")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scenario = Path(os.environ.get("MULETRAIL_SCENARIO", DEFAULT_SCENARIO))
    cache_root = Path(os.environ.get("MULETRAIL_CACHE", DEFAULT_CACHE_ROOT))
    cache_dir, manifest, built = load_or_build(scenario, cache_root)
    log.info("precompute cache %s (%s)", cache_dir, "built" if built else "loaded")
    state = DemoState(cache_dir=cache_dir, manifest=manifest, world=load_world(cache_dir / WORLD_FILE))
    # Demo clock (spec §7.3): starts at the end of history; nothing later is visible until the demo advances it.
    state.demo_clock = datetime.fromisoformat(manifest["history_end"])
    state.public = Public.from_world(state.world)
    state.config = Scenario.load(scenario).detection
    with (cache_dir / ANALYSIS_FILE).open('rb') as handle:
        state.analysis = pickle.load(handle)
    with (cache_dir / PREDICTIONS_FILE).open('rb') as handle:
        state.predictions = pickle.load(handle)
    state.graphs = {clock: build_graph(state.public, datetime.fromisoformat(clock)) for clock in state.analysis}
    state.take_snapshot()
    app.state.demo = state
    yield


app = FastAPI(title="MuleTrail", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(districts.router)
app.include_router(investigation.router)
app.include_router(predictions.router)
app.include_router(alerts.router)
app.include_router(blocking.router)
