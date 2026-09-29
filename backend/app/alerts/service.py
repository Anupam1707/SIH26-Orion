"""Alert generation and management (spec §12 Phase 4).

Alerts are generated from precomputed predictions when an ATM crosses a probability
threshold. They are stored in ``state.data['alerts']`` so ``reset()`` clears them.

Mock delivery channels: SMS (police/field), Email (bank AML), API webhook (freeze auth).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal


# Default probability threshold for alert generation (50%).
DEFAULT_ALERT_THRESHOLD = 0.30

CHANNELS = [
    {"type": "sms", "label": "SMS to field officer", "recipient": "I4C Field Unit"},
    {"type": "email", "label": "Email to bank AML", "recipient": "AML Compliance Desk"},
    {"type": "api", "label": "Bank freeze API", "recipient": "CFCFRMS Gateway"},
]


def _next_alert_id(alerts: list[dict]) -> str:
    n = len(alerts) + 1
    return f"ALR{n:04d}"


def generate_alerts(
    complaint_id: str,
    prediction: dict,
    demo_clock: datetime,
    threshold: float = DEFAULT_ALERT_THRESHOLD,
    window: int = 6,
    model: str = "xgboost",
) -> list[dict]:
    """Generate alerts for ATMs crossing the probability threshold.

    Args:
        complaint_id: The case this alert is for.
        prediction: The precomputed prediction payload (with 'models' key).
        demo_clock: Current demo clock for timestamps.
        threshold: Minimum probability to trigger an alert.
        window: Time window in hours (2, 6, or 24).
        model: Which model's predictions to use.

    Returns:
        List of new alert dicts ready to be appended to state.data['alerts'].
    """
    model_data = prediction.get("models", {}).get(model, {}).get(window)
    if model_data is None:
        return []

    atms = model_data.get("atms", [])
    alerts: list[dict] = []
    case_amount = prediction.get("evidence", {}).get("complaint", {}).get("amount_inr", 0)

    for rank, atm in enumerate(atms):
        prob = atm.get("probability", 0)
        if prob < threshold:
            continue  # ATMs are sorted by probability desc; stop early.

        severity: Literal["critical", "high", "medium"]
        if prob >= 0.6:
            severity = "critical"
        elif prob >= 0.4:
            severity = "high"
        else:
            severity = "medium"

        reasons = atm.get("reasons", [])
        top_reason = reasons[0]["text"] if reasons else "ATM prediction above threshold."

        channels_status = [
            {**ch, "status": "delivered", "delivered_at": demo_clock.isoformat()}
            for ch in CHANNELS
        ]

        alert = {
            "id": "",  # Filled by the caller after determining the sequence.
            "complaint_id": complaint_id,
            "created_at": demo_clock.isoformat(),
            "severity": severity,
            "title": f"Predicted cash-out at {atm['id']} ({prob*100:.0f}% in {window}h)",
            "description": top_reason,
            "target_type": "ATM",
            "target_id": atm["id"],
            "target_district": atm.get("district_id", ""),
            "target_bank": atm.get("bank", ""),
            "probability": prob,
            "window_hours": window,
            "model": model,
            "case_amount_inr": case_amount,
            "rank": rank + 1,
            "channels": channels_status,
            "status": "triggered",
            "acknowledged_at": None,
        }
        alerts.append(alert)

        # Limit to top 5 ATMs per case to avoid alert fatigue.
        if len(alerts) >= 5:
            break

    return alerts


def generate_account_alerts(
    complaint_id: str,
    recommendations: dict,
    demo_clock: datetime,
) -> list[dict]:
    """Generate alerts for accounts recommended for freezing."""
    alerts: list[dict] = []
    for acct in recommendations.get("recommended_accounts", []):
        channels_status = [
            {**ch, "status": "delivered", "delivered_at": demo_clock.isoformat()}
            for ch in CHANNELS
        ]
        alert = {
            "id": "",
            "complaint_id": complaint_id,
            "created_at": demo_clock.isoformat(),
            "severity": "critical",
            "title": f"Freeze recommended: {acct['id']} ({acct.get('inferred_role', 'unknown')})",
            "description": acct.get("reason", "Account recommended for freezing by min-cut analysis."),
            "target_type": "account",
            "target_id": acct["id"],
            "target_district": acct.get("home_district_id", ""),
            "target_bank": acct.get("bank", ""),
            "probability": acct.get("risk", 0),
            "window_hours": 0,
            "model": "min-cut",
            "case_amount_inr": 0,
            "rank": 0,
            "channels": channels_status,
            "status": "triggered",
            "acknowledged_at": None,
        }
        alerts.append(alert)
    return alerts


def ensure_alerts(state) -> list[dict]:
    """Get or initialise the alerts list in state.data."""
    if "alerts" not in state.data:
        state.data["alerts"] = []
    return state.data["alerts"]


def add_alerts(state, new_alerts: list[dict]) -> list[dict]:
    """Assign IDs and append new alerts to the state."""
    existing = ensure_alerts(state)
    for alert in new_alerts:
        alert["id"] = _next_alert_id(existing)
        existing.append(alert)
    return new_alerts


def acknowledge(state, alert_id: str, demo_clock: datetime) -> dict | None:
    """Acknowledge an alert by ID. Returns the updated alert or None if not found."""
    alerts = ensure_alerts(state)
    for alert in alerts:
        if alert["id"] == alert_id:
            alert["status"] = "acknowledged"
            alert["acknowledged_at"] = demo_clock.isoformat()
            return alert
    return None
