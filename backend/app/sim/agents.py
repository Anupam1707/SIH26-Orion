"""Simulation agents (spec §7.1).

Every agent has ``step(t)``, called once per simulated hour. Timed behaviour never happens
inside ``step``: agents *schedule events* (spec §7.2). Fraud-chain agents (Mule, Collector,
CashOut) are reactive: the model calls their ``on_receive`` when money lands in their account.

No account balances are modelled; the simulator only guarantees the flows the spec describes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from app.sim.scenario import Network

if TYPE_CHECKING:  # pragma: no cover
    from app.sim.model import Model

STRUCTURING_LOW, STRUCTURING_HIGH = 9_000, 9_900


@dataclass
class Crew:
    """The accounts and cash-out state of one fraud network."""

    network: Network
    l1: list[str]
    collector: str
    l2: list[str]
    pool: list[str] = field(default_factory=list)  # ATM ids, rotate_near_collector only
    rotation: int = 0
    current_district: str = ""  # hop_district only


@dataclass
class Fraud:
    id: str
    network_id: str
    victim: str
    amount: int
    l1: list[str]
    l2: list[str]
    started: datetime
    is_demo: bool
    complaint_id: str
    atm_id: str | None = None  # rotate_near_collector: the ATM used for this fraud
    district_id: str | None = None  # hop_district / split_many_atms: where this fraud cashes out
    l1_done: int = 0
    pooled: int = 0


class Agent:
    def step(self, t: datetime) -> None:
        """Hourly tick. Reactive agents have nothing to do here."""

    def on_receive(self, ts: datetime, tx: dict) -> None:
        """Called when a fraud-chain transaction lands in this agent's account."""


def structured_chunks(rng, total: int) -> list[int]:
    """Split ``total`` into transfers of ₹9,000-₹9,900; the remainder goes out as a last, smaller one."""
    chunks: list[int] = []
    remaining = total
    while remaining >= STRUCTURING_LOW:
        c = min(remaining, rng.randint(STRUCTURING_LOW, STRUCTURING_HIGH))
        chunks.append(c)
        remaining -= c
    if remaining > 0:
        chunks.append(remaining)
    return chunks


def split_amount(rng, total: int, parts: int) -> list[int]:
    """Split ``total`` rupees into ``parts`` random positive shares that sum exactly to ``total``."""
    if parts == 1:
        return [total]
    weights = [rng.uniform(0.6, 1.4) for _ in range(parts)]
    s = sum(weights)
    shares = [int(total * w / s) for w in weights[:-1]]
    shares.append(total - sum(shares))
    return shares


def even_chunks_100(total: int, max_chunk: int) -> list[int]:
    """Split into the fewest equal-ish chunks (multiples of ₹100), none above ``max_chunk``."""
    units = total // 100
    n = max(1, math.ceil(units * 100 / max_chunk))
    q, r = divmod(units, n)
    return [(q + (1 if i < r else 0)) * 100 for i in range(n)]


class Citizen(Agent):
    """Background noise: everyday transfers, rent, and small ATM withdrawals near home."""

    def __init__(
        self,
        model: "Model",
        account_id: str,
        district_id: str,
        is_merchant: bool,
        fav_atms: list[str],
        rent_day: int | None,
        rent_amount: int,
        landlord: str | None,
    ) -> None:
        self.model = model
        self.account_id = account_id
        self.district_id = district_id
        self.is_merchant = is_merchant
        self.fav_atms = fav_atms
        self.rent_day = rent_day
        self.rent_amount = rent_amount
        self.landlord = landlord

    def _at(self, t: datetime) -> datetime:
        return t + timedelta(seconds=self.model.rng.randrange(3600))

    def step(self, t: datetime) -> None:
        m = self.model
        if self.rent_day is not None and t.day == self.rent_day and t.hour == 11 and self.landlord:
            m.schedule(self._at(t), self.pay_rent)
        daytime = 7 <= t.hour < 22
        p_transfer = 0.017 if daytime else 0.003
        p_atm = 0.008 if daytime else 0.001
        r = m.rng.random()
        if r < p_transfer:
            m.schedule(self._at(t), self.transfer)
        elif r < p_transfer + p_atm:
            m.schedule(self._at(t), self.withdraw)

    def pay_rent(self, ts: datetime) -> None:
        assert self.landlord is not None
        self.model.execute_transfer(ts, self.account_id, self.landlord, self.rent_amount, "NEFT")

    def transfer(self, ts: datetime) -> None:
        m = self.model
        rng = m.rng
        for _ in range(5):
            pool = m.merchant_accounts if (m.merchant_accounts and rng.random() < 0.55) else m.citizen_accounts
            dst = rng.choice(pool)
            if dst != self.account_id:
                break
        else:
            return
        amount = min(20_000, max(50, round(rng.lognormvariate(math.log(600), 1.0))))
        channel = "UPI" if rng.random() < 0.8 else "IMPS"
        m.execute_transfer(ts, self.account_id, dst, amount, channel)

    def withdraw(self, ts: datetime) -> None:
        m = self.model
        rng = m.rng
        if rng.random() < 0.8:
            atm = rng.choice(self.fav_atms)
        else:
            atm = rng.choice(m.atms_by_district[self.district_id])
        amount = rng.choices([500, 1_000, 2_000, 3_000, 5_000, 10_000], weights=[3, 4, 4, 2, 2, 1])[0]
        m.execute_withdrawal(ts, self.account_id, atm, amount, None)


class Caller(Agent):
    """Runs one network's scams: picks a victim and starts a fraud (spec §7.1)."""

    def __init__(self, model: "Model", crew: Crew) -> None:
        self.model = model
        self.crew = crew
        self.p_per_hour = crew.network.frauds_per_week / (7 * 24)

    def step(self, t: datetime) -> None:
        m = self.model
        # No random frauds after history: the tail only plays out the scripted demo case.
        if t < m.sc.history_end and m.rng.random() < self.p_per_hour:
            m.schedule(t + timedelta(seconds=m.rng.randrange(3600)), self.start_fraud, False)

    def start_fraud(self, ts: datetime, demo: bool) -> None:
        m = self.model
        rng = m.rng
        sc = m.sc
        crew = self.crew
        net = crew.network

        if demo:
            candidates = [
                c for c in m.citizens if not c.is_merchant and c.district_id == sc.demo_case.victim_district
            ]
            amount = sc.demo_case.amount_inr
            k = sc.demo_case.path.l1_mules
            n_l2 = sc.demo_case.path.l2_accounts
        else:
            candidates = [c for c in m.citizens if not c.is_merchant]
            amount = min(200_000, max(10_000, int(round(rng.lognormvariate(math.log(45_000), 0.8), -2))))
            k = rng.randint(1, min(3, len(crew.l1)))
            n_l2 = len(crew.l2) if net.transfer_style == "scatter" else rng.randint(1, min(2, len(crew.l2)))

        victim = rng.choice(candidates)
        l1 = rng.sample(crew.l1, k)
        l2 = rng.sample(crew.l2, n_l2)

        fid = m.next_id("F", 5)
        cid = m.next_id("C", 5)
        fraud = Fraud(
            id=fid, network_id=net.id, victim=victim.account_id, amount=amount,
            l1=l1, l2=l2, started=ts, is_demo=demo, complaint_id=cid,
        )
        if net.strategy == "rotate_near_collector":
            fraud.atm_id = crew.pool[crew.rotation % len(crew.pool)]
            crew.rotation += 1
        elif net.strategy == "hop_district":
            crew.current_district = rng.choice(m.districts[crew.current_district].neighbours)
            fraud.district_id = crew.current_district
        else:  # split_many_atms
            fraud.district_id = net.collector_district
        m.frauds[fid] = fraud

        base = amount // k
        shares = [base] * (k - 1) + [amount - base * (k - 1)]
        t_i = ts
        for mule, share in zip(l1, shares):
            channel = "UPI" if rng.random() < 0.5 else "IMPS"
            m.schedule(t_i, m.execute_transfer, victim.account_id, mule, share, channel, fid)
            last_ts = t_i
            t_i = t_i + timedelta(seconds=rng.randint(30, 180))

        lo, hi = sc.complaint_delay_min
        m.complaints.append(
            {
                "id": cid,
                "victim_account_id": victim.account_id,
                "amount_inr": amount,
                "incident_at": ts,
                "reported_at": last_ts + timedelta(minutes=rng.randint(lo, hi)),
                "district_id": victim.district_id,
                "description": (
                    "Caller posing as a bank official obtained an OTP over the phone; "
                    "the victim then found several unauthorised transfers."
                ),
            }
        )


class MuleAgent(Agent):
    """Layer-1 mule: forwards 92-98% of each receipt to the collector within 5-45 minutes."""

    def __init__(self, model: "Model", account_id: str) -> None:
        self.model = model
        self.account_id = account_id

    def on_receive(self, ts: datetime, tx: dict) -> None:
        m = self.model
        rng = m.rng
        fraud = m.frauds[tx["fraud_id"]]
        crew = m.crews[fraud.network_id]
        forward = int(round(tx["amount_inr"] * rng.uniform(0.92, 0.98)))
        t = ts + timedelta(minutes=rng.randint(5, 45))

        if crew.network.transfer_style == "structured":
            chunks = structured_chunks(rng, forward)
        else:
            chunks = [forward]

        last_ts = t
        for i, c in enumerate(chunks):
            if i:
                t = t + timedelta(minutes=rng.randint(1, 5))
            m.schedule(t, m.execute_transfer, self.account_id, crew.collector, c, "IMPS", fraud.id)
            last_ts = t
        # Scheduled after the transfers, so it runs after the last one at the same timestamp.
        m.schedule(last_ts, m.agents[crew.collector].on_l1_done, fraud.id)


class CollectorAgent(Agent):
    """Pools the L1 forwards of one fraud, then pays ~95% onward to the L2 accounts."""

    def __init__(self, model: "Model", account_id: str) -> None:
        self.model = model
        self.account_id = account_id

    def on_receive(self, ts: datetime, tx: dict) -> None:
        self.model.frauds[tx["fraud_id"]].pooled += tx["amount_inr"]

    def on_l1_done(self, ts: datetime, fraud_id: str) -> None:
        m = self.model
        fraud = m.frauds[fraud_id]
        fraud.l1_done += 1
        if fraud.l1_done == len(fraud.l1):
            m.schedule(ts + timedelta(minutes=m.rng.randint(20, 90)), self.payout, fraud_id)

    def payout(self, ts: datetime, fraud_id: str) -> None:
        m = self.model
        rng = m.rng
        fraud = m.frauds[fraud_id]
        crew = m.crews[fraud.network_id]
        total = int(round(fraud.pooled * rng.uniform(0.93, 0.97)))
        shares = split_amount(rng, total, len(fraud.l2))
        # The first payment leaves exactly at the payout time (20-90 min after the last L1 forward);
        # the rest follow, all inside two hours for scatter.
        if crew.network.transfer_style == "scatter":
            offsets = [0] + sorted(rng.randint(0, 100) for _ in fraud.l2[1:])
        else:
            offsets, acc = [0], 0
            for _ in fraud.l2[1:]:
                acc += rng.randint(1, 10)
                offsets.append(acc)
        for dst, share, off in zip(fraud.l2, shares, offsets):
            m.schedule(ts + timedelta(minutes=off), m.execute_transfer, self.account_id, dst, share, "IMPS", fraud.id)


class CashOutAgent(Agent):
    """Final-layer account: withdraws 2-10 hours after funds arrive, per the network strategy."""

    def __init__(self, model: "Model", account_id: str) -> None:
        self.model = model
        self.account_id = account_id

    def on_receive(self, ts: datetime, tx: dict) -> None:
        m = self.model
        rng = m.rng
        fraud = m.frauds[tx["fraud_id"]]
        net = m.crews[fraud.network_id].network
        amount = tx["amount_inr"] // 100 * 100  # ATMs dispense whole hundreds
        if amount <= 0:
            return
        t = ts + timedelta(minutes=rng.randint(120, 600))

        if net.strategy == "rotate_near_collector":
            assert fraud.atm_id is not None
            m.schedule(t, m.execute_withdrawal, self.account_id, fraud.atm_id, amount, fraud.id)
        elif net.strategy == "hop_district":
            assert fraud.district_id is not None
            atm = rng.choice(m.atms_by_district[fraud.district_id])
            m.schedule(t, m.execute_withdrawal, self.account_id, atm, amount, fraud.id)
        else:  # split_many_atms: chunks up to split_max_inr, each at a different ATM in one district
            assert fraud.district_id is not None
            chunks = even_chunks_100(amount, net.split_max_inr)
            pool = m.atms_by_district[fraud.district_id]
            atms = rng.sample(pool, len(chunks)) if len(chunks) <= len(pool) else rng.choices(pool, k=len(chunks))
            for i, (chunk, atm) in enumerate(zip(chunks, atms)):
                if i:
                    t = t + timedelta(minutes=rng.randint(3, 20))
                m.schedule(t, m.execute_withdrawal, self.account_id, atm, chunk, fraud.id)
