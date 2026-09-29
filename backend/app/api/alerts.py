"""Alert endpoints: list alerts and acknowledge them (spec §13)."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from app.alerts.service import (
    acknowledge,
    add_alerts,
    ensure_alerts,
    generate_alerts,
)

router = APIRouter()


def _state(request: Request):
    return request.app.state.demo


@router.get("/alerts")
def list_alerts(request: Request) -> list[dict]:
    """Return all alerts generated up to the current demo clock."""
    s = _state(request)
    alerts = ensure_alerts(s)
    # Filter to alerts created at or before the demo clock.
    clock = s.demo_clock
    return [
        a for a in reversed(alerts)
        if datetime.fromisoformat(a["created_at"]) <= clock
    ]


@router.post("/alerts/{alert_id}/ack")
def ack_alert(alert_id: str, request: Request) -> dict:
    """Acknowledge an alert, updating its status."""
    s = _state(request)
    result = acknowledge(s, alert_id, s.demo_clock)
    if result is None:
        raise HTTPException(404, f"Alert {alert_id} not found")
    return result


@router.post("/alerts/generate/{complaint_id}")
def generate(complaint_id: str, request: Request) -> dict:
    """Generate alerts for a complaint from its precomputed predictions.

    This is called by the frontend when the demo advances or the user
    navigates to the alerts screen with a case selected.
    """
    s = _state(request)
    # Check complaint is visible.
    visible = s.public.complaints_upto(s.demo_clock)
    if complaint_id not in set(visible.id):
        raise HTTPException(404, "Complaint not visible at the demo clock")

    # Check we haven't already generated alerts for this case.
    existing = ensure_alerts(s)
    already = [a for a in existing if a["complaint_id"] == complaint_id and a["target_type"] == "ATM"]
    if already:
        return {"complaint_id": complaint_id, "new_alerts": 0,
                "total_alerts": len(existing), "message": "Alerts already generated for this case."}

    # Get prediction.
    case = s.predictions["cases"].get(complaint_id)
    if not case or datetime.fromisoformat(case["prediction_time"]) > s.demo_clock:
        raise HTTPException(409, "Prediction not yet available at the demo clock")

    new_alerts = generate_alerts(complaint_id, case, s.demo_clock)
    added = add_alerts(s, new_alerts)

    return {
        "complaint_id": complaint_id,
        "new_alerts": len(added),
        "total_alerts": len(existing),
        "alerts": added,
    }
