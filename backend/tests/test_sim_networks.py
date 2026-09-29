"""Phase 1 check: each network produces the topology, transfer style and cash-out strategy configured."""

import pandas as pd
import pytest

MIN = pd.Timedelta(minutes=1)


@pytest.fixture(scope="module")
def ctx(world):
    role = dict(zip(world.accounts["id"], world.accounts["role_truth"]))
    home = dict(zip(world.accounts["id"], world.accounts["home_district_id"]))
    atm_district = dict(zip(world.atms["id"], world.atms["district_id"]))
    members = {r.id: r.members for r in world.networks.itertuples()}
    return {"role": role, "home": home, "atm_district": atm_district, "members": members}


def fraud_parts(world, fid):
    tx = world.transactions[world.transactions["fraud_id"] == fid]
    wd = world.withdrawals[world.withdrawals["fraud_id"] == fid]
    return tx, wd


def frauds_of(world, network_id):
    f = world.frauds[world.frauds["network_id"] == network_id]
    return f.sort_values("started_at")


# ---------------------------------------------------------------- scale and noise


def test_world_scale_matches_spec(world):
    assert len(world.districts) == 4
    assert len(world.atms) == 60
    assert 1_800 <= len(world.accounts) <= 2_100  # "about 2,000 accounts"
    assert (world.accounts["role_truth"] == "merchant").sum() == 36  # 2% of 1,800


def test_citizens_withdraw_near_home(world, ctx):
    wd = world.withdrawals[world.withdrawals["fraud_id"].isna()]
    assert len(wd) > 10_000
    home_d = wd["account_id"].map(ctx["home"])
    atm_d = wd["atm_id"].map(ctx["atm_district"])
    assert (home_d == atm_d).all()


def test_merchants_receive_far_more_than_they_send(world):
    merchants = set(world.accounts.loc[world.accounts["role_truth"] == "merchant", "id"])
    tx = world.transactions
    received = tx.loc[tx["dst"].isin(merchants), "amount_inr"].sum()
    sent = tx.loc[tx["src"].isin(merchants), "amount_inr"].sum()
    assert received > 0 and sent < 0.2 * received


# ---------------------------------------------------------------- fraud topology (all networks)


def test_every_fraud_has_a_complaint_and_a_cash_out(world):
    complaints = world.complaints.set_index("id")
    assert len(world.complaints) == len(world.frauds)
    for f in world.frauds.itertuples():
        tx, wd = fraud_parts(world, f.id)
        c = complaints.loc[f.complaint_id]
        assert c["victim_account_id"] == f.victim_account_id
        assert c["amount_inr"] == f.amount_inr
        assert c["incident_at"] == tx["ts"].min() == f.started_at
        last_victim_tx = tx.loc[tx["src"] == f.victim_account_id, "ts"].max()
        assert 15 * MIN <= c["reported_at"] - last_victim_tx <= 90 * MIN
        assert len(wd) >= 1, f.id


def test_money_only_follows_victim_l1_collector_l2(world, ctx):
    role = ctx["role"]
    for f in world.frauds.itertuples():
        tx, wd = fraud_parts(world, f.id)
        assert role[f.victim_account_id] == "victim"
        for r in tx.itertuples():
            edge = (role[r.src], role[r.dst])
            assert edge in {("victim", "mule_l1"), ("mule_l1", "collector"), ("collector", "mule_l2")}, (f.id, edge)
        assert set(wd["account_id"].map(role)) == {"mule_l2"}
        n_l1 = tx.loc[tx["src"] == f.victim_account_id, "dst"].nunique()
        assert 1 <= n_l1 <= 3
        assert tx.loc[tx["src"] == f.victim_account_id, "amount_inr"].sum() == f.amount_inr


def test_forwarding_ratios_and_timing(world):
    for f in world.frauds.itertuples():
        tx, _ = fraud_parts(world, f.id)
        from_victim = tx[tx["src"] == f.victim_account_id]
        to_collector = tx[tx["dst"].isin(tx.loc[tx["src"].isin(from_victim["dst"]), "dst"])]
        # layer 1: 92-98% of what each mule received, first forward 5-45 min after receipt
        for r in from_victim.itertuples():
            out = tx[tx["src"] == r.dst]
            assert 0.92 - 1e-3 <= out["amount_inr"].sum() / r.amount_inr <= 0.98 + 1e-3, f.id
            assert 5 * MIN <= out["ts"].min() - r.ts <= 45 * MIN, f.id
        # collector: ~95% (93-97%) of the pooled inflow, starting 20-90 min after the last L1 forward
        collector = to_collector["dst"].iloc[0]
        pooled = tx.loc[tx["dst"] == collector, "amount_inr"].sum()
        out = tx[tx["src"] == collector]
        assert 0.93 - 1e-3 <= out["amount_inr"].sum() / pooled <= 0.97 + 1e-3, f.id
        gap = out["ts"].min() - tx.loc[tx["dst"] == collector, "ts"].max()
        assert 20 * MIN <= gap <= 90 * MIN, f.id


def test_cash_out_starts_2_to_10_hours_after_funds_arrive(world):
    for f in world.frauds.itertuples():
        tx, wd = fraud_parts(world, f.id)
        for r in tx[tx["dst"].isin(wd["account_id"])].itertuples():
            mine = wd[wd["account_id"] == r.dst]
            first = mine["ts"].min() - r.ts
            assert 120 * MIN <= first <= 600 * MIN, f.id
            # whole hundreds are dispensed, so at most ₹99 is left behind
            assert 0 <= r.amount_inr - mine["amount_inr"].sum() < 100, f.id


def test_no_random_frauds_after_history(world, scenario):
    later = world.frauds[world.frauds["started_at"] >= scenario.history_end]
    assert later["is_demo"].tolist() == [True]


# ---------------------------------------------------------------- N_A: plain transfers, rotating ATM pool


def test_n_a_rotates_a_fixed_pool_of_three_atms_near_the_collector(world, ctx):
    fs = frauds_of(world, "N_A")
    assert len(fs) > 10
    per_fraud = []
    for f in fs.itertuples():
        _, wd = fraud_parts(world, f.id)
        assert wd["atm_id"].nunique() == 1  # one ATM per fraud
        per_fraud.append(wd["atm_id"].iloc[0])
    assert len(set(per_fraud[:3])) == 3
    assert per_fraud == [per_fraud[i % 3] for i in range(len(per_fraud))]  # strict rotation
    assert {ctx["atm_district"][a] for a in per_fraud} == {"D03"}  # the collector's district


def test_n_a_pays_one_or_two_l2_accounts_plainly(world, ctx):
    for f in frauds_of(world, "N_A").itertuples():
        tx, _ = fraud_parts(world, f.id)
        collector_out = tx[tx["src"].map(ctx["role"]) == "collector"]
        assert 1 <= collector_out["dst"].nunique() <= 2
        assert len(collector_out) == collector_out["dst"].nunique()  # one transfer per receiver


# ---------------------------------------------------------------- N_B: structured L1 transfers, district hopping


def test_n_b_l1_mules_forward_in_structuring_chunks(world, ctx):
    in_band = 0
    for f in frauds_of(world, "N_B").itertuples():
        tx, _ = fraud_parts(world, f.id)
        l1_out = tx[tx["src"].map(ctx["role"]) == "mule_l1"]
        for _, chunks in l1_out.groupby("src"):
            body = chunks.sort_values("ts")["amount_inr"].iloc[:-1]  # the last chunk is the remainder
            assert body.between(9_000, 9_900).all(), f.id
            in_band += len(body)
    assert in_band >= 3


def test_n_b_hops_to_a_neighbouring_district_after_each_fraud(world, ctx, scenario):
    neighbours = {d.id: set(d.neighbours) for d in scenario.districts}
    previous = "D02"  # the collector's district is where the network starts
    fs = frauds_of(world, "N_B")
    assert len(fs) > 8
    for f in fs.itertuples():
        _, wd = fraud_parts(world, f.id)
        districts = {ctx["atm_district"][a] for a in wd["atm_id"]}
        assert len(districts) == 1
        (current,) = districts
        assert current in neighbours[previous], (f.id, previous, current)
        previous = current


# ---------------------------------------------------------------- N_C: scatter, many ATMs in one district


def test_n_c_collector_scatters_to_all_l2_accounts_within_two_hours(world, ctx):
    for f in frauds_of(world, "N_C").itertuples():
        tx, _ = fraud_parts(world, f.id)
        out = tx[tx["src"].map(ctx["role"]) == "collector"]
        assert out["dst"].nunique() == 6, f.id
        assert out["ts"].max() - out["ts"].min() <= 120 * MIN, f.id


def test_n_c_splits_cash_into_chunks_across_many_atms_in_one_district(world, ctx):
    multi_atm = 0
    for f in frauds_of(world, "N_C").itertuples():
        tx, wd = fraud_parts(world, f.id)
        assert wd["amount_inr"].max() <= 20_000
        assert {ctx["atm_district"][a] for a in wd["atm_id"]} == {"D04"}
        for r in tx[tx["dst"].isin(wd["account_id"])].itertuples():
            mine = wd[wd["account_id"] == r.dst]
            if r.amount_inr > 20_000:
                assert len(mine) >= 2 and mine["atm_id"].is_unique
                multi_atm += 1
    assert multi_atm >= 1


# ---------------------------------------------------------------- ground truth export


def test_ground_truth_lists_every_planted_structure(world):
    gt = world.ground_truth
    assert set(gt["type"]) == {"fraud_network", "fraud_case"}
    assert (gt["type"] == "fraud_network").sum() == 3
    assert (gt["type"] == "fraud_case").sum() == len(world.frauds)
    assert gt["is_demo"].sum() == 1
    assert (pd.to_datetime(gt["end_ts"]) >= pd.to_datetime(gt["start_ts"])).all()
    assert gt["members"].str.len().gt(0).all()
