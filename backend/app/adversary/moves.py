"""Adversary moves and economic cost functions (spec §11).

All costs are in ₹ (INR), allowing different tactics to be directly compared.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

MoveType = Literal["switch_atm", "delay", "add_mule_hop", "split_amount"]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in km between two coordinate pairs."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.asin(math.sqrt(max(0.0, min(1.0, a))))
    return r * c


@dataclass(frozen=True)
class MoveResult:
    move: MoveType
    description: str
    cost: float
    target_atms: list[str]


def switch_atm(current_atm: dict, candidate_atm: dict, current_atms: list[str]) -> MoveResult:
    """Switch cash-out to an ATM outside the model's top-5.

    Cost: ₹500 base + travel cost (₹10/km).
    """
    dist_km = haversine_km(current_atm["lat"], current_atm["lng"], candidate_atm["lat"], candidate_atm["lng"])
    cost = round(500.0 + 10.0 * dist_km, 2)
    # Replace current_atm with candidate_atm in the target ATM list
    new_targets = [a if a != current_atm["id"] else candidate_atm["id"] for a in current_atms]
    return MoveResult(
        move="switch_atm",
        description=f"Switch cash-out from {current_atm['id']} ({current_atm.get('bank', 'ATM')}) to {candidate_atm['id']} ({candidate_atm.get('bank', 'ATM')}, {dist_km:.1f} km away)",
        cost=cost,
        target_atms=new_targets,
    )


def delay_withdrawal(amount_held: float, freeze_risk_per_hour: float, current_atms: list[str]) -> MoveResult:
    """Wait 12h before withdrawing.

    Cost: Expected freeze loss = amount held × (1 − (1 − p)^12), where p is the hourly freeze risk.
    """
    p = freeze_risk_per_hour
    loss_fraction = 1.0 - ((1.0 - p) ** 12)
    cost = round(amount_held * loss_fraction, 2)
    return MoveResult(
        move="delay",
        description=f"Delay withdrawal by 12 hours (expected freeze risk loss of {loss_fraction * 100:.1f}% on ₹{amount_held:,.0f})",
        cost=cost,
        target_atms=list(current_atms),
    )


def add_mule_hop(current_atms: list[str]) -> MoveResult:
    """Insert one extra mule layer into the laundering chain.

    Cost: ₹3,000 (mule commission cut) + 1 hour delay.
    """
    return MoveResult(
        move="add_mule_hop",
        description="Insert an additional intermediary mule account (₹3,000 commission + 1h delay)",
        cost=3000.0,
        target_atms=list(current_atms),
    )


def split_amount(extra_atms: list[dict], current_atms: list[str]) -> MoveResult:
    """Split cash-out across 2 more ATMs.

    Cost: ₹1,000 per extra ATM (₹2,000 total).
    """
    extra_ids = [a["id"] for a in extra_atms[:2]]
    cost = 1000.0 * len(extra_ids)
    new_targets = list(set(current_atms + extra_ids))
    return MoveResult(
        move="split_amount",
        description=f"Split cash-out across {len(extra_ids)} additional ATMs: {', '.join(extra_ids)}",
        cost=cost,
        target_atms=new_targets,
    )
