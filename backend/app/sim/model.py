"""The simulation model: builds the world, runs the hourly loop, produces the tables (spec §5, §7)."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd

from app.sim.agents import (
    Agent, Caller, CashOutAgent, CollectorAgent, Crew, Citizen, Fraud, MuleAgent,
)
from app.sim.events import EventQueue
from app.sim.geo import random_point_in_ring
from app.sim.names import BANKS, FIRST_NAMES, LAST_NAMES
from app.sim.scenario import Scenario

CHANNELS = ("UPI", "IMPS", "NEFT")


@dataclass
class World:
    """Everything the simulation produced. ``fraud_id`` / ``network_id`` columns and ``role_truth``
    are hidden ground truth: for evaluation and the scenario only, never a model input."""

    scenario: dict
    districts: list[dict]
    atms: pd.DataFrame
    persons: pd.DataFrame
    accounts: pd.DataFrame
    transactions: pd.DataFrame
    withdrawals: pd.DataFrame
    complaints: pd.DataFrame
    frauds: pd.DataFrame
    networks: pd.DataFrame
    ground_truth: pd.DataFrame
    meta: dict


class Model:
    def __init__(self, sc: Scenario) -> None:
        self.sc = sc
        self.rng = random.Random(sc.seed)
        self.queue = EventQueue()
        self._counters: dict[str, int] = {}

        self.districts = {d.id: d for d in sc.districts}
        self.atms: list[dict] = []
        self.atms_by_district: dict[str, list[str]] = {d.id: [] for d in sc.districts}
        self.persons: list[dict] = []
        self.accounts: list[dict] = []
        self.transactions: list[dict] = []
        self.withdrawals: list[dict] = []
        self.complaints: list[dict] = []
        self.frauds: dict[str, Fraud] = {}

        self.citizens: list[Citizen] = []
        self.citizen_accounts: list[str] = []
        self.merchant_accounts: list[str] = []
        self.callers: list[Caller] = []
        self.crews: dict[str, Crew] = {}
        self.agents: dict[str, Agent] = {}  # account id -> reactive fraud-chain agent

        self._build_atms()
        self._build_citizens()
        self._build_crews()

        demo_caller = next(c for c in self.callers if c.crew.network.id == sc.demo_case.network_id)
        self.schedule(sc.demo_case.inject_at, demo_caller.start_fraud, True)

    # ------------------------------------------------------------------ plumbing

    def next_id(self, prefix: str, width: int) -> str:
        n = self._counters.get(prefix, 0) + 1
        self._counters[prefix] = n
        return f"{prefix}{n:0{width}d}"

    def schedule(self, ts: datetime, fn, *args) -> None:
        self.queue.schedule(ts, fn, *args)

    def execute_transfer(
        self, ts: datetime, src: str, dst: str, amount: int, channel: str, fraud_id: str | None = None
    ) -> None:
        tx = {
            "id": self.next_id("T", 7), "src": src, "dst": dst, "amount_inr": int(amount),
            "ts": ts, "channel": channel, "fraud_id": fraud_id,
        }
        self.transactions.append(tx)
        if fraud_id is not None:
            agent = self.agents.get(dst)
            if agent is not None:
                agent.on_receive(ts, tx)

    def execute_withdrawal(
        self, ts: datetime, account_id: str, atm_id: str, amount: int, fraud_id: str | None
    ) -> None:
        self.withdrawals.append(
            {
                "id": self.next_id("W", 7), "account_id": account_id, "atm_id": atm_id,
                "amount_inr": int(amount), "ts": ts,
                "network_id": self.frauds[fraud_id].network_id if fraud_id else None,
                "fraud_id": fraud_id,
            }
        )

    # ------------------------------------------------------------------ world building

    def _new_account(self, district_id: str, role: str, opened_at: datetime) -> str:
        rng = self.rng
        pid = self.next_id("P", 5)
        aid = self.next_id("A", 5)
        self.persons.append(
            {"id": pid, "name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}", "district_id": district_id}
        )
        self.accounts.append(
            {
                "id": aid, "holder_id": pid, "bank": rng.choice(BANKS), "home_district_id": district_id,
                "opened_at": opened_at, "role_truth": role,
            }
        )
        return aid

    def _build_atms(self) -> None:
        for d in self.sc.districts:
            for _ in range(self.sc.atms_per_district):
                lng, lat = random_point_in_ring(self.rng, d.polygon[0])
                aid = self.next_id("ATM", 3)
                self.atms.append(
                    {
                        "id": aid, "district_id": d.id, "lat": round(lat, 6), "lng": round(lng, 6),
                        "bank": self.rng.choice(BANKS),
                    }
                )
                self.atms_by_district[d.id].append(aid)

    def _build_citizens(self) -> None:
        sc, rng = self.sc, self.rng
        ids = [d.id for d in sc.districts]
        n_merchants = round(sc.citizens * sc.merchant_share)
        merchant_idx = set(rng.sample(range(sc.citizens), n_merchants))

        # First pass: accounts (rent needs landlords that already exist).
        rows: list[tuple[str, str, bool]] = []
        for i in range(sc.citizens):
            district = rng.choice(ids)
            is_merchant = i in merchant_idx
            opened = sc.start - timedelta(days=rng.randint(365, 365 * 12))
            acct = self._new_account(district, "merchant" if is_merchant else "citizen", opened)
            rows.append((acct, district, is_merchant))
            (self.merchant_accounts if is_merchant else self.citizen_accounts).append(acct)

        # Rent is paid in ₹500 steps from ₹10,000 up, so it never lands in the ₹9,000-9,900 structuring band.
        landlords = [a for a, _, m in rows if not m]
        for acct, district, is_merchant in rows:
            pays_rent = (not is_merchant) and rng.random() < 0.15
            landlord = rng.choice([a for a in landlords if a != acct]) if pays_rent else None
            self.citizens.append(
                Citizen(
                    self, acct, district, is_merchant,
                    fav_atms=rng.sample(self.atms_by_district[district], 2),
                    rent_day=rng.randint(1, 5) if pays_rent else None,
                    rent_amount=rng.randrange(10_000, 25_001, 500) if pays_rent else 0,
                    landlord=landlord,
                )
            )

    def _build_crews(self) -> None:
        sc, rng = self.sc, self.rng
        ids = [d.id for d in sc.districts]
        # Mule accounts are young (opened 20-120 days before the history starts).
        young = lambda: sc.start - timedelta(days=rng.randint(20, 120))  # noqa: E731

        for net in sc.networks:
            l1 = [self._new_account(rng.choice(ids), "mule_l1", young()) for _ in range(net.mules.l1)]
            collector = self._new_account(net.collector_district, "collector", young())
            # L2 accounts sit near the collector, except for hop_district networks.
            l2_district = (lambda: rng.choice(ids)) if net.strategy == "hop_district" else (lambda: net.collector_district)
            l2 = [self._new_account(l2_district(), "mule_l2", young()) for _ in range(net.mules.l2)]

            crew = Crew(network=net, l1=l1, collector=collector, l2=l2, current_district=net.collector_district)
            if net.strategy == "rotate_near_collector":
                crew.pool = rng.sample(self.atms_by_district[net.collector_district], net.atm_pool_size)
            self.crews[net.id] = crew

            for a in l1:
                self.agents[a] = MuleAgent(self, a)
            self.agents[collector] = CollectorAgent(self, collector)
            for a in l2:
                self.agents[a] = CashOutAgent(self, a)
            self.callers.append(Caller(self, crew))

    # ------------------------------------------------------------------ running

    def run(self) -> "Model":
        t = self.sc.start
        end = self.sc.sim_end
        hour = timedelta(hours=1)
        while t < end:
            for c in self.citizens:
                c.step(t)
            for c in self.callers:
                c.step(t)
            self.queue.run_until(t + hour)
            t += hour
        return self

    # ------------------------------------------------------------------ output

    def to_world(self) -> World:
        sc = self.sc
        accounts = pd.DataFrame(self.accounts)
        victims = {f.victim for f in self.frauds.values()}
        accounts.loc[accounts["id"].isin(victims) & (accounts["role_truth"] == "citizen"), "role_truth"] = "victim"

        tx = pd.DataFrame(self.transactions)
        wd = pd.DataFrame(self.withdrawals)
        complaints = pd.DataFrame(self.complaints)

        frauds = pd.DataFrame(
            [
                {
                    "id": f.id, "network_id": f.network_id, "complaint_id": f.complaint_id,
                    "victim_account_id": f.victim, "amount_inr": f.amount, "started_at": f.started,
                    "is_demo": f.is_demo,
                }
                for f in self.frauds.values()
            ]
        )

        networks = pd.DataFrame(
            [
                {
                    "id": n.id, "strategy": n.strategy, "transfer_style": n.transfer_style,
                    "members": [*self.crews[n.id].l1, self.crews[n.id].collector, *self.crews[n.id].l2],
                }
                for n in sc.networks
            ]
        )

        gt_rows: list[dict] = []
        for n in sc.networks:
            crew = self.crews[n.id]
            gt_rows.append(
                {
                    "structure_id": n.id, "type": "fraud_network", "network_id": n.id, "strategy": n.strategy,
                    "members": ";".join([*crew.l1, crew.collector, *crew.l2]),
                    "start_ts": sc.start.isoformat(), "end_ts": sc.sim_end.isoformat(), "is_demo": False,
                }
            )
        for f in self.frauds.values():
            crew = self.crews[f.network_id]
            f_tx = tx[tx["fraud_id"] == f.id]
            f_wd = wd[wd["fraud_id"] == f.id] if len(wd) else wd
            end_ts = max([f_tx["ts"].max()] + ([f_wd["ts"].max()] if len(f_wd) else []))
            gt_rows.append(
                {
                    "structure_id": f.id, "type": "fraud_case", "network_id": f.network_id,
                    "strategy": crew.network.strategy,
                    "members": ";".join([f.victim, *f.l1, crew.collector, *f.l2]),
                    "start_ts": f_tx["ts"].min().isoformat(), "end_ts": end_ts.isoformat(), "is_demo": f.is_demo,
                }
            )
        ground_truth = pd.DataFrame(gt_rows)

        demo = next(f for f in self.frauds.values() if f.is_demo)
        meta = {
            "seed": sc.seed,
            "history_end": sc.history_end.isoformat(),
            "sim_end": sc.sim_end.isoformat(),
            "demo_fraud_id": demo.id,
            "demo_complaint_id": demo.complaint_id,
            "counts": {
                "accounts": len(accounts), "atms": len(self.atms), "persons": len(self.persons),
                "transactions": len(tx), "withdrawals": len(wd), "complaints": len(complaints),
                "frauds": len(frauds),
            },
        }
        return World(
            scenario=sc.model_dump(mode="json"),
            districts=[
                {
                    "id": d.id, "name": d.name, "neighbours": d.neighbours, "polygon": d.polygon,
                    "centroid": list(d.centroid),
                }
                for d in sc.districts
            ],
            atms=pd.DataFrame(self.atms),
            persons=pd.DataFrame(self.persons),
            accounts=accounts,
            transactions=tx,
            withdrawals=wd,
            complaints=complaints,
            frauds=frauds,
            networks=networks,
            ground_truth=ground_truth,
            meta=meta,
        )
