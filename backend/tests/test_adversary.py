"""Tests for Phase 5 — Adversary Lab (moves, greedy search, evasion curves, API)."""

import pytest
from fastapi.testclient import TestClient

from app.adversary.curves import BUDGET_POINTS, compute_evasion_curve, compute_hardened_curve
from app.adversary.moves import add_mule_hop, delay_withdrawal, haversine_km, split_amount, switch_atm
from app.adversary.search import greedy_evasion_search
from app.main import app
from app.predict.cases import make_cases, time_split
from datetime import datetime


def test_haversine_distance():
    # Distance between two known coordinates (e.g. ~10 km apart)
    dist = haversine_km(22.7196, 75.8577, 22.8000, 75.8577)
    assert 8.0 < dist < 10.0


def test_move_costs():
    curr = {"id": "ATM001", "lat": 22.72, "lng": 75.85, "bank": "SBI"}
    cand = {"id": "ATM002", "lat": 22.75, "lng": 75.85, "bank": "HDFC"}

    # Switch ATM: 500 + 10 * dist
    res_switch = switch_atm(curr, cand, ["ATM001"])
    assert res_switch.cost >= 500.0
    assert "ATM002" in res_switch.target_atms
    assert "ATM001" not in res_switch.target_atms

    # Delay: amount * (1 - (1 - 0.02)^12) ~ 21.5% of 50000
    res_delay = delay_withdrawal(50000.0, 0.02, ["ATM001"])
    assert 10000.0 < res_delay.cost < 11500.0

    # Add mule hop: fixed 3000
    res_hop = add_mule_hop(["ATM001"])
    assert res_hop.cost == 3000.0

    # Split amount: 1000 per extra ATM
    res_split = split_amount([cand, {"id": "ATM003"}], ["ATM001"])
    assert res_split.cost == 2000.0
    assert len(res_split.target_atms) == 3


def test_greedy_search_already_undetected():
    all_atms = [{"id": f"ATM{i:03d}", "lat": 22.7, "lng": 75.8} for i in range(1, 20)]
    predictions = [{"id": f"ATM{i:03d}", "probability": 0.05 * (20 - i)} for i in range(1, 20)]

    # Target is ATM015 which is outside top 5 (top 5 are ATM001-ATM005)
    res = greedy_evasion_search(
        complaint_id="C001",
        initial_targets=["ATM015"],
        amount_inr=50000.0,
        atm_predictions=predictions,
        all_atms=all_atms,
    )
    assert not res.initial_detected
    assert not res.final_detected
    assert res.total_cost == 0.0
    assert len(res.moves) == 0


def test_greedy_search_detected_evades():
    all_atms = [{"id": f"ATM{i:03d}", "lat": 22.7 + i * 0.01, "lng": 75.8} for i in range(1, 20)]
    predictions = [{"id": f"ATM{i:03d}", "probability": 0.05 * (20 - i)} for i in range(1, 20)]

    # Target is ATM001 which is the #1 ranked ATM (top 5)
    res = greedy_evasion_search(
        complaint_id="C001",
        initial_targets=["ATM001"],
        amount_inr=50000.0,
        atm_predictions=predictions,
        all_atms=all_atms,
    )
    assert res.initial_detected
    assert len(res.moves) > 0
    assert res.total_cost > 0
    # The cumulative cost is monotonically increasing across moves
    for idx in range(1, len(res.moves)):
        assert res.moves[idx].cumulative_cost >= res.moves[idx - 1].cumulative_cost


def test_evasion_curve_monotonicity(client):
    """The curve must be non-increasing in detection rate as budget rises (spec §11, §12)."""
    r = client.get("/adversary/curves")
    assert r.status_code == 200
    data = r.json()

    base_curve = data["baseline_curve"]
    hard_curve = data["hardened_curve"]

    assert len(base_curve) == len(BUDGET_POINTS)
    assert len(hard_curve) == len(BUDGET_POINTS)

    # Monotonicity check: detection rate must be non-increasing as budget rises
    for i in range(len(base_curve) - 1):
        assert base_curve[i]["detection_rate"] >= base_curve[i + 1]["detection_rate"]
        assert base_curve[i]["detected_count"] >= base_curve[i + 1]["detected_count"]

    for i in range(len(hard_curve) - 1):
        assert hard_curve[i]["detection_rate"] >= hard_curve[i + 1]["detection_rate"]
        assert hard_curve[i]["detected_count"] >= hard_curve[i + 1]["detected_count"]

    # Hardening effectiveness: hardened detection rate >= baseline detection rate
    for b_pt, h_pt in zip(base_curve, hard_curve):
        assert h_pt["detection_rate"] >= b_pt["detection_rate"]


def test_adversary_run_api(client):
    r = client.post("/adversary/run", json={"hardened": False})
    assert r.status_code == 200
    body = r.json()
    assert "complaint_id" in body
    assert "initial_detected" in body
    assert "final_detected" in body
    assert "moves" in body
    assert isinstance(body["moves"], list)
