"""Evaluation-only truth boundary: case scheduling and outcome labels, never features."""
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np

from app.sim.model import World

WINDOWS = (2, 6, 24)
MODELS = ('baseline', 'kde', 'xgboost')


@dataclass(frozen=True)
class Case:
    complaint_id: str
    prediction_time: datetime
    strategy: str
    is_demo: bool
    labels: dict[int, np.ndarray]

    @property
    def outcome_end(self) -> datetime:
        return self.prediction_time + timedelta(hours=max(WINDOWS))


def make_cases(world: World) -> list[Case]:
    """Ground truth determines the scheduled clock and evaluation labels only."""
    atms = sorted(world.atms.id)
    strategies = world.networks.set_index('id').strategy.to_dict()
    complaints = world.complaints.set_index('id')
    result = []
    for fraud in world.frauds.itertuples():
        tx = world.transactions[world.transactions.fraud_id == fraud.id]
        clock = max(complaints.loc[fraud.complaint_id, 'reported_at'], tx.ts.max()).to_pydatetime()
        wd = world.withdrawals[world.withdrawals.fraud_id == fraud.id]
        if (wd.ts <= clock).any():
            raise ValueError(f'{fraud.complaint_id}: cash-out precedes prediction time')
        labels = {}
        for hours in WINDOWS:
            actual = set(wd.loc[(wd.ts > clock) & (wd.ts <= clock + timedelta(hours=hours)), 'atm_id'])
            labels[hours] = np.array([a in actual for a in atms], dtype=np.float32)
        result.append(Case(fraud.complaint_id, clock, strategies[fraud.network_id], fraud.is_demo, labels))
    return sorted(result, key=lambda c: (c.prediction_time, c.complaint_id))


def time_split(cases: list[Case], start: datetime) -> tuple[list[Case], list[Case]]:
    cutoff, end = start + timedelta(days=70), start + timedelta(days=90)
    history = [c for c in cases if not c.is_demo]
    return ([c for c in history if start <= c.prediction_time < cutoff],
            [c for c in history if cutoff <= c.prediction_time < end])
