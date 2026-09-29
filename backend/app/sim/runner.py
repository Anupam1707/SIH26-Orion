"""Run a scenario and persist the result."""

from __future__ import annotations

import pickle
from pathlib import Path

from app.sim.model import Model, World
from app.sim.scenario import Scenario


def run_scenario(sc: Scenario) -> World:
    return Model(sc).run().to_world()


def save_world(world: World, path: Path) -> None:
    with open(path, "wb") as f:
        pickle.dump(world, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_world(path: Path) -> World:
    # Pickle is safe here only because this file is the local precompute cache that save_world
    # wrote itself (backend/.cache, gitignored). Never point this at a file from anywhere else.
    with open(path, "rb") as f:
        return pickle.load(f)


def export_ground_truth(world: World, path: Path) -> None:
    """Every planted structure with its type, member ids, and time window (spec §5)."""
    world.ground_truth.to_csv(path, index=False)
