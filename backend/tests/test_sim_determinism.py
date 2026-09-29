import pandas as pd
import pytest

from app.sim.runner import run_scenario
from app.sim.scenario import Scenario

TABLES = ["atms", "persons", "accounts", "transactions", "withdrawals", "complaints", "frauds", "networks", "ground_truth"]


def test_same_seed_gives_identical_output(scenario, world):
    again = run_scenario(scenario)
    for name in TABLES:
        pd.testing.assert_frame_equal(getattr(world, name), getattr(again, name), obj=name)
    assert world.meta == again.meta


def test_different_seed_changes_output(scenario_dict, world):
    other = run_scenario(Scenario.model_validate({**scenario_dict, "seed": 43}))
    assert not other.transactions.equals(world.transactions)
    assert other.meta["counts"]["transactions"] != world.meta["counts"]["transactions"]


@pytest.mark.parametrize("name", ["transactions", "withdrawals"])
def test_ids_are_unique_and_chronological(world, name):
    df = getattr(world, name)
    assert df["id"].is_unique
    assert df["ts"].is_monotonic_increasing
