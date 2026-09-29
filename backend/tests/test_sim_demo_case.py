"""Phase 1 check: the demo case exists with exactly the configured path."""

import pandas as pd
import pytest


@pytest.fixture(scope="module")
def demo(world):
    f = world.frauds[world.frauds["is_demo"]]
    assert len(f) == 1
    f = f.iloc[0]
    tx = world.transactions[world.transactions["fraud_id"] == f["id"]]
    wd = world.withdrawals[world.withdrawals["fraud_id"] == f["id"]]
    role = dict(zip(world.accounts["id"], world.accounts["role_truth"]))
    return f, tx, wd, role


def test_demo_case_follows_the_configured_path(demo, scenario):
    f, tx, _, role = demo
    cfg = scenario.demo_case
    victim = f["victim_account_id"]

    l1 = tx.loc[tx["src"] == victim, "dst"]
    assert len(l1) == cfg.path.l1_mules and l1.is_unique
    assert {role[a] for a in l1} == {"mule_l1"}

    to_collector = tx[tx["src"].isin(l1)]
    assert len(to_collector) == cfg.path.l1_mules  # plain style: one forward per mule
    assert to_collector["dst"].nunique() == cfg.path.collector == 1
    (collector,) = to_collector["dst"].unique()
    assert role[collector] == "collector"

    to_l2 = tx[tx["src"] == collector]
    assert to_l2["dst"].nunique() == cfg.path.l2_accounts
    assert {role[a] for a in to_l2["dst"]} == {"mule_l2"}

    assert len(tx) == cfg.path.l1_mules * 2 + cfg.path.l2_accounts  # nothing else moves


def test_demo_case_victim_amount_and_district(demo, world, scenario):
    f, tx, _, _ = demo
    cfg = scenario.demo_case
    assert f["network_id"] == cfg.network_id
    assert f["amount_inr"] == cfg.amount_inr
    assert tx.loc[tx["src"] == f["victim_account_id"], "amount_inr"].sum() == cfg.amount_inr
    victim_home = world.accounts.set_index("id").loc[f["victim_account_id"], "home_district_id"]
    assert victim_home == cfg.victim_district
    assert world.persons.set_index("id").loc[
        world.accounts.set_index("id").loc[f["victim_account_id"], "holder_id"], "district_id"
    ] == cfg.victim_district


def test_demo_case_starts_at_the_configured_time_after_history(demo, world, scenario):
    f, tx, _, _ = demo
    cfg = scenario.demo_case
    assert f["started_at"] == pd.Timestamp(cfg.inject_at)
    assert tx["ts"].min() == pd.Timestamp(cfg.inject_at)
    assert tx["ts"].min() >= pd.Timestamp(scenario.history_end)
    c = world.complaints.set_index("id").loc[f["complaint_id"]]
    assert c["incident_at"] == pd.Timestamp(cfg.inject_at)
    assert c["reported_at"] > c["incident_at"]
    assert c["district_id"] == cfg.victim_district
    assert world.meta["demo_complaint_id"] == f["complaint_id"]


def test_demo_case_cashes_out_before_the_simulation_ends(demo, scenario):
    _, tx, wd, _ = demo
    assert len(wd) == tx.loc[tx["src"].isin(tx["src"]) & tx["dst"].isin(wd["account_id"]), "dst"].nunique()
    assert wd["ts"].max() < pd.Timestamp(scenario.sim_end)
    assert wd["atm_id"].nunique() == 1  # N_A uses one pool ATM per fraud
