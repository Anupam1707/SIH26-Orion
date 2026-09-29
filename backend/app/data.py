"""Public view of the world: what the system is allowed to know.

The simulator's tables carry hidden ground truth (``role_truth``, ``fraud_id``, ``network_id``).
Detection, tracing, prediction and every API response read the world *only* through this module,
which strips those columns and enforces the demo clock (spec §5, §7.3).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from app.sim.model import World

HIDDEN_TX = ["fraud_id"]
HIDDEN_WD = ["fraud_id", "network_id"]
HIDDEN_ACCOUNT = ["role_truth"]


def to_epoch_seconds(ts: pd.Series) -> pd.Series:
    return ts.dt.as_unit("s").astype("int64")


@dataclass
class Public:
    """Ground-truth-free tables, sorted by time, with an integer epoch-seconds column ``t``."""

    transactions: pd.DataFrame
    withdrawals: pd.DataFrame
    accounts: pd.DataFrame
    persons: pd.DataFrame
    atms: pd.DataFrame
    complaints: pd.DataFrame
    districts: list[dict]

    @classmethod
    def from_world(cls, world: World) -> "Public":
        tx = world.transactions.drop(columns=HIDDEN_TX).sort_values(["ts", "id"], kind="stable").reset_index(drop=True)
        tx["t"] = to_epoch_seconds(tx["ts"])
        wd = world.withdrawals.drop(columns=HIDDEN_WD).sort_values(["ts", "id"], kind="stable").reset_index(drop=True)
        wd["t"] = to_epoch_seconds(wd["ts"])
        complaints = world.complaints.sort_values(["reported_at", "id"], kind="stable").reset_index(drop=True)
        complaints["reported_t"] = to_epoch_seconds(complaints["reported_at"])
        return cls(
            transactions=tx,
            withdrawals=wd,
            accounts=world.accounts.drop(columns=HIDDEN_ACCOUNT),
            persons=world.persons,
            atms=world.atms,
            complaints=complaints,
            districts=world.districts,
        )

    def tx_upto(self, clock: datetime) -> pd.DataFrame:
        """Transactions with ts <= clock."""
        n = int(np.searchsorted(self.transactions["t"].to_numpy(), int(clock.timestamp()), side="right"))
        return self.transactions.iloc[:n]

    def withdrawals_upto(self, clock: datetime) -> pd.DataFrame:
        n = int(np.searchsorted(self.withdrawals["t"].to_numpy(), int(clock.timestamp()), side="right"))
        return self.withdrawals.iloc[:n]

    def complaints_upto(self, clock: datetime) -> pd.DataFrame:
        """Complaints already reported at ``clock``."""
        n = int(np.searchsorted(self.complaints["reported_t"].to_numpy(), int(clock.timestamp()), side="right"))
        return self.complaints.iloc[:n]
