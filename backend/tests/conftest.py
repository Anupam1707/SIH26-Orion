import json

import pytest
from fastapi.testclient import TestClient

from app.precompute import DEFAULT_SCENARIO
from app.sim.runner import run_scenario
from app.sim.scenario import Scenario


@pytest.fixture(scope="session")
def scenario_dict() -> dict:
    return json.loads(DEFAULT_SCENARIO.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def scenario() -> Scenario:
    return Scenario.load(DEFAULT_SCENARIO)


@pytest.fixture(scope="session")
def world(scenario):
    """The full demo scenario, simulated once for the whole test session (~2 s)."""
    return run_scenario(scenario)


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    """An API client backed by a throwaway cache, so tests never touch backend/.cache."""
    mp = pytest.MonkeyPatch()
    mp.setenv("MULETRAIL_CACHE", str(tmp_path_factory.mktemp("cache")))
    mp.delenv("MULETRAIL_SCENARIO", raising=False)
    from app.main import app

    with TestClient(app) as c:
        yield c
    mp.undo()
