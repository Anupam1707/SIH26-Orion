"""Tests for alert generation and management."""

from datetime import datetime

import pytest

from app.alerts.service import (
    acknowledge,
    add_alerts,
    ensure_alerts,
    generate_alerts,
)


class FakeState:
    """Minimal mock of DemoState with a data dict."""
    def __init__(self):
        self.data = {}


def _make_prediction(prob: float = 0.5) -> dict:
    """Create a minimal prediction payload with one ATM."""
    return {
        "models": {
            "xgboost": {
                6: {
                    "atms": [
                        {
                            "id": "ATM001",
                            "bank": "SBI",
                            "district_id": "D01",
                            "lat": 22.7,
                            "lng": 75.8,
                            "probability": prob,
                            "reasons": [
                                {"text": "4 withdrawals here in 7 days.", "source_group": "wd_7d",
                                 "feature": "withdrawals_7d", "contribution": 0.3}
                            ],
                        }
                    ],
                }
            }
        },
        "evidence": {"complaint": {"amount_inr": 50_000}},
    }


class TestAlertGeneration:
    def test_generates_alert_above_threshold(self):
        pred = _make_prediction(0.5)
        clock = datetime.fromisoformat("2026-08-30T12:00:00+05:30")
        alerts = generate_alerts("C001", pred, clock, threshold=0.3)
        assert len(alerts) == 1
        assert alerts[0]["target_id"] == "ATM001"
        assert alerts[0]["severity"] in ("critical", "high", "medium")

    def test_no_alert_below_threshold(self):
        pred = _make_prediction(0.1)
        clock = datetime.fromisoformat("2026-08-30T12:00:00+05:30")
        alerts = generate_alerts("C001", pred, clock, threshold=0.3)
        assert len(alerts) == 0

    def test_severity_levels(self):
        for prob, expected in [(0.7, "critical"), (0.5, "high"), (0.35, "medium")]:
            pred = _make_prediction(prob)
            clock = datetime.fromisoformat("2026-08-30T12:00:00+05:30")
            alerts = generate_alerts("C001", pred, clock, threshold=0.3)
            assert alerts[0]["severity"] == expected, f"prob={prob} expected {expected}"

    def test_channels_present(self):
        pred = _make_prediction(0.5)
        clock = datetime.fromisoformat("2026-08-30T12:00:00+05:30")
        alerts = generate_alerts("C001", pred, clock, threshold=0.3)
        channels = alerts[0]["channels"]
        assert len(channels) == 3
        types = {c["type"] for c in channels}
        assert types == {"sms", "email", "api"}


class TestAlertState:
    def test_add_alerts_assigns_ids(self):
        state = FakeState()
        pred = _make_prediction(0.5)
        clock = datetime.fromisoformat("2026-08-30T12:00:00+05:30")
        alerts = generate_alerts("C001", pred, clock, threshold=0.3)
        added = add_alerts(state, alerts)
        assert all(a["id"].startswith("ALR") for a in added)
        assert state.data["alerts"] == added

    def test_acknowledge(self):
        state = FakeState()
        pred = _make_prediction(0.5)
        clock = datetime.fromisoformat("2026-08-30T12:00:00+05:30")
        alerts = generate_alerts("C001", pred, clock, threshold=0.3)
        add_alerts(state, alerts)
        alert_id = state.data["alerts"][0]["id"]
        result = acknowledge(state, alert_id, clock)
        assert result is not None
        assert result["status"] == "acknowledged"

    def test_acknowledge_nonexistent(self):
        state = FakeState()
        ensure_alerts(state)
        clock = datetime.fromisoformat("2026-08-30T12:00:00+05:30")
        result = acknowledge(state, "NONEXISTENT", clock)
        assert result is None

    def test_ensure_alerts_idempotent(self):
        state = FakeState()
        a1 = ensure_alerts(state)
        a2 = ensure_alerts(state)
        assert a1 is a2
