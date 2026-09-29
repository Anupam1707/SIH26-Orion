"""Feature extraction can see only Public tables, never outcome labels or membership."""
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from app.data import Public
from app.detect.temporal import temporal
from app.graph.builder import build_graph
from app.graph.trace import trace_case
from app.sim.scenario import DetectionConfig

FEATURE_NAMES = ['distance_km', 'withdrawals_7d', 'withdrawals_30d', 'kde_density',
                 'holder_hops', 'temporal_burst', 'hour', 'weekday', 'different_district']


def coordinates_km(lng: np.ndarray, lat: np.ndarray, origin: tuple[float, float]) -> np.ndarray:
    """Local equirectangular projection for this compact fictional district map."""
    return np.column_stack((np.radians(lng - origin[0]) * 6371 * np.cos(np.radians(origin[1])),
                            np.radians(lat - origin[1]) * 6371))


def records(frame: pd.DataFrame) -> list[dict]:
    return [{k: v.isoformat() if isinstance(v, datetime) else v for k, v in r.items()
             if k not in ('t', 'reported_t')} for r in frame.to_dict('records')]


@dataclass
class Features:
    complaint_id: str
    clock: datetime
    atms: list[dict]
    atm_xy: np.ndarray
    history_xy: np.ndarray
    history: pd.DataFrame
    base: np.ndarray
    last_age_days: np.ndarray
    chain_ids: list[str]
    linked_ids: list[str]
    holder_ids: list[str]
    evidence: dict
    max_input_ts: str

    def matrix(self, density: np.ndarray) -> np.ndarray:
        result = self.base.copy()
        result[:, FEATURE_NAMES.index('kde_density')] = density
        return result


def extract(public: Public, complaint_id: str, clock: datetime, config: DetectionConfig) -> Features:
    visible = public.complaints_upto(clock)
    found = visible[visible.id == complaint_id]
    if found.empty:
        raise ValueError('Complaint is not visible at prediction time')
    graph = build_graph(public, clock)
    trace = trace_case(graph, found.iloc[0].to_dict(), max_hops=config.trace_max_hops,
                       min_share=config.trace_min_share)
    chain = {n['id'] for n in trace['nodes']}
    linked = set(chain)
    for aid in chain:
        linked.update(graph.predecessors(aid))
        linked.update(graph.successors(aid))
    max_hop = max((n['hop'] for n in trace['nodes']), default=0)
    holders = sorted(n['id'] for n in trace['nodes'] if n['hop'] == max_hop)
    accounts = public.accounts[public.accounts.opened_at <= clock].set_index('id')
    centres = {d['id']: d['centroid'] for d in public.districts}
    origin = tuple(np.mean(list(centres.values()), axis=0))
    atms = public.atms.sort_values('id').reset_index(drop=True)
    atm_xy = coordinates_km(atms.lng.to_numpy(), atms.lat.to_numpy(), origin)
    home = np.array([centres[accounts.loc[aid, 'home_district_id']] for aid in holders])
    home_xy = coordinates_km(home[:, 0], home[:, 1], origin)
    distance = np.linalg.norm(atm_xy[:, None, :] - home_xy[None, :, :], axis=2).min(axis=1)
    history = public.withdrawals_upto(clock)
    history = history[history.account_id.isin(linked)].copy()
    locations = atms.set_index('id')
    wd_xy = coordinates_km(history.atm_id.map(locations.lng).to_numpy(),
                           history.atm_id.map(locations.lat).to_numpy(), origin)
    counts = []
    for days in (7, 30):
        recent = history[history.t >= clock.timestamp() - days * 86400]
        counts.append(atms.id.map(recent.groupby('atm_id').size()).fillna(0).to_numpy())
    last = history.groupby('atm_id').t.max()
    ages = (clock.timestamp() - atms.id.map(last).to_numpy()) / 86400
    ages = np.where(np.isnan(ages), np.inf, ages)
    scores = temporal(graph)
    burst = max((scores[a]['temporal_score'] for a in chain), default=0.)
    last_district = locations.loc[history.iloc[-1].atm_id, 'district_id'] if len(history) else None
    different = (atms.district_id != last_district).astype(float).to_numpy() if last_district else np.zeros(len(atms))
    matrix = np.column_stack((distance, counts[0], counts[1], np.zeros(len(atms)),
                              np.full(len(atms), max_hop), np.full(len(atms), burst),
                              np.full(len(atms), clock.hour), np.full(len(atms), clock.weekday()), different))
    tx = public.tx_upto(clock)
    source_ids = {e['id'] for e in trace['edges']}
    source_ids.update(tid for a in chain for tid in scores[a]['temporal_tx_ids'])
    # Include the edges establishing direct-neighbour linkage.
    source_ids.update(tx.loc[tx.src.isin(chain) | tx.dst.isin(chain), 'id'])
    evidence = {'transactions': records(tx[tx.id.isin(source_ids)]), 'withdrawals': records(history),
                'accounts': records(accounts.loc[sorted(linked)].reset_index()),
                'complaint': records(found)[0], 'temporal_population_n': len(graph)}
    max_ts = max([found.iloc[0].reported_at, *tx.ts.tail(1), *history.ts.tail(1)])
    return Features(complaint_id, clock, records(atms), atm_xy, wd_xy, history, matrix, ages,
                    sorted(chain), sorted(linked), holders, evidence, max_ts.isoformat())
