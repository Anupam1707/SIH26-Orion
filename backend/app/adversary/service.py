"""Adversary service layer connecting state with greedy search and curves."""

from __future__ import annotations

from typing import Any

from app.adversary.curves import BUDGET_POINTS, compute_evasion_curve, compute_hardened_curve
from app.adversary.search import EvasionResult, greedy_evasion_search
from app.predict.cases import make_cases, time_split
from app.state import DemoState


def run_adversary_simulation(
    state: DemoState,
    complaint_id: str | None = None,
    hardened: bool = False,
) -> dict[str, Any]:
    """Execute greedy search for a given case."""
    if not complaint_id:
        complaint_id = state.manifest.get("demo_complaint_id", "C00084")

    # Get predictions for this case
    case_predictions = state.predictions.get("cases", {}).get(complaint_id, {})
    xgboost_6h = case_predictions.get("models", {}).get("xgboost", {}).get(6, {})
    atms_pred = xgboost_6h.get("atms", [])

    all_atms = state.public.atms.to_dict("records")

    # Find actual withdrawal ATMs from world data
    actual_atms = []
    world = state.world
    fraud_matches = world.frauds[world.frauds.complaint_id == complaint_id]
    if not fraud_matches.empty:
        fid = fraud_matches.iloc[0]["id"]
        w_subset = world.withdrawals[world.withdrawals.fraud_id == fid]
        actual_atms = list(w_subset["atm_id"].unique())

    complaint = world.complaints[world.complaints.id == complaint_id]
    amount_inr = float(complaint.iloc[0]["amount_inr"]) if not complaint.empty else 50000.0

    freeze_risk = float(state.world.scenario.get("freeze_risk_per_hour", 0.02))

    res: EvasionResult = greedy_evasion_search(
        complaint_id=complaint_id,
        initial_targets=actual_atms,
        amount_inr=amount_inr,
        atm_predictions=atms_pred,
        all_atms=all_atms,
        freeze_risk_per_hour=freeze_risk,
        hardened=hardened,
    )
    return res.to_dict()


def get_adversary_curves(state: DemoState) -> dict[str, Any]:
    """Compute and return evasion curves for baseline and hardened models."""
    world = state.world
    all_cases = make_cases(world)
    from datetime import datetime
    start = datetime.fromisoformat(world.scenario["start_date"] + "T00:00:00+05:30")
    _, test_cases = time_split(all_cases, start)

    all_atms = state.public.atms.to_dict("records")
    predictions_map = state.predictions.get("cases", {})
    freeze_risk = float(world.scenario.get("freeze_risk_per_hour", 0.02))

    baseline_curve = compute_evasion_curve(
        test_cases=test_cases,
        predictions_map=predictions_map,
        all_atms=all_atms,
        world=world,
        hardened=False,
        freeze_risk_per_hour=freeze_risk,
    )

    hardened_curve = compute_hardened_curve(
        test_cases=test_cases,
        predictions_map=predictions_map,
        all_atms=all_atms,
        world=world,
        freeze_risk_per_hour=freeze_risk,
    )

    b0_base = baseline_curve[0]["detection_rate"] * 100
    b0_hard = hardened_curve[0]["detection_rate"] * 100

    return {
        "budgets": BUDGET_POINTS,
        "baseline_curve": baseline_curve,
        "hardened_curve": hardened_curve,
        "test_cases_count": len(test_cases),
        "target_window": "6h",
        "summary": (
            f"At budget ₹0, baseline detection rate is {b0_base:.1f}% vs {b0_hard:.1f}% for the hardened model. "
            "As criminal syndicates spend budget to switch ATMs, delay cash-outs, or add layers, detection drops "
            "monotonically. The hardened model forces criminals to spend higher budgets to evade detection."
        ),
    }
