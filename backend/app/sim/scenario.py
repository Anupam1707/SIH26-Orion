"""Scenario file loader and validation (spec §6). The scenario is the single source of truth."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.sim.geo import ring_centroid

IST = timezone(timedelta(hours=5, minutes=30))

# The simulator keeps running this long after history ends so the demo case can fully cash out.
TAIL_DAYS = 3


class District(BaseModel):
    id: str
    name: str
    neighbours: list[str]
    polygon: list[list[list[float]]]  # GeoJSON Polygon coordinates: [ring][vertex][lng, lat]

    @property
    def centroid(self) -> tuple[float, float]:
        return ring_centroid(self.polygon[0])


class Mules(BaseModel):
    l1: int = Field(ge=1)
    l2: int = Field(ge=1)


class Network(BaseModel):
    id: str
    strategy: Literal["rotate_near_collector", "hop_district", "split_many_atms"]
    transfer_style: Literal["plain", "structured", "scatter"]
    mules: Mules
    collector_district: str
    frauds_per_week: float = Field(gt=0)
    atm_pool_size: int = 3
    split_max_inr: int = 20_000


class DemoPath(BaseModel):
    l1_mules: int = Field(ge=1)
    collector: Literal[1] = 1
    l2_accounts: int = Field(ge=1)


class DemoCase(BaseModel):
    network_id: str
    victim_district: str
    amount_inr: int = Field(gt=0)
    inject_at: datetime
    path: DemoPath


class DetectionConfig(BaseModel):
    fan_senders: int = Field(default=3, ge=2)
    fan_in_hours: float = Field(default=6, gt=0)
    fan_out_hours: float = Field(default=24, gt=0)
    forward_share: float = Field(default=.9, gt=0, le=1)
    fan_repeats: int = Field(default=2, ge=2)
    layer_hours: float = Field(default=3, gt=0)
    layer_min_share: float = Field(default=.85, gt=0, le=1)
    layer_max_share: float = Field(default=.98, gt=0, le=1)
    structuring_min_inr: int = Field(default=9000, gt=0)
    structuring_max_inr: int = Field(default=9900, gt=0)
    structuring_count: int = Field(default=3, ge=3)
    scatter_receivers: int = Field(default=6, ge=2)
    scatter_hours: float = Field(default=2, gt=0)
    rapid_minutes: float = Field(default=60, gt=0)
    rapid_repeats: int = Field(default=3, ge=3)
    trace_max_hops: int = Field(default=5, ge=1, le=10)
    trace_min_share: float = Field(default=.05, gt=0, le=1)

    @model_validator(mode='after')
    def ordered_bounds(self):
        if self.layer_min_share > self.layer_max_share or self.structuring_min_inr > self.structuring_max_inr:
            raise ValueError('detection minimum must not exceed maximum')
        return self


class Scenario(BaseModel):
    seed: int
    start_date: date
    days: int = Field(gt=0)
    districts: list[District]
    atms_per_district: int = Field(gt=0)
    citizens: int = Field(gt=0)
    merchant_share: float = Field(ge=0, lt=1)
    complaint_delay_min: tuple[int, int]
    freeze_risk_per_hour: float = Field(ge=0, le=1)
    networks: list[Network]
    demo_case: DemoCase
    detection: DetectionConfig = Field(default_factory=DetectionConfig)

    @property
    def start(self) -> datetime:
        return datetime.combine(self.start_date, time(0, 0), IST)

    @property
    def history_end(self) -> datetime:
        return self.start + timedelta(days=self.days)

    @property
    def sim_end(self) -> datetime:
        return self.history_end + timedelta(days=TAIL_DAYS)

    @model_validator(mode="after")
    def _check_references(self) -> "Scenario":
        district_ids = [d.id for d in self.districts]
        if len(set(district_ids)) != len(district_ids):
            raise ValueError("duplicate district ids")
        known = set(district_ids)
        for d in self.districts:
            for n in d.neighbours:
                if n not in known:
                    raise ValueError(f"district {d.id} lists unknown neighbour {n}")
            if not d.neighbours:
                raise ValueError(f"district {d.id} has no neighbours (hop_district needs one)")

        net_ids = [n.id for n in self.networks]
        if len(set(net_ids)) != len(net_ids):
            raise ValueError("duplicate network ids")
        for n in self.networks:
            if n.collector_district not in known:
                raise ValueError(f"network {n.id}: unknown collector_district {n.collector_district}")
            if n.strategy == "rotate_near_collector" and n.atm_pool_size > self.atms_per_district:
                raise ValueError(f"network {n.id}: atm_pool_size exceeds atms_per_district")

        lo, hi = self.complaint_delay_min
        if not 0 < lo <= hi:
            raise ValueError("complaint_delay_min must be [low, high] with 0 < low <= high")

        demo = self.demo_case
        net = next((n for n in self.networks if n.id == demo.network_id), None)
        if net is None:
            raise ValueError(f"demo_case.network_id {demo.network_id} is not a network")
        if demo.path.l1_mules > net.mules.l1:
            raise ValueError("demo path needs more layer-1 mules than the network has")
        if demo.path.l2_accounts > net.mules.l2:
            raise ValueError("demo path needs more layer-2 accounts than the network has")
        if demo.victim_district not in known:
            raise ValueError(f"demo victim_district {demo.victim_district} is unknown")
        if demo.inject_at.tzinfo is None:
            raise ValueError("demo_case.inject_at must carry a UTC offset")
        if demo.inject_at < self.history_end:
            raise ValueError("demo_case.inject_at must not be before the end of history")
        if demo.inject_at >= self.sim_end:
            raise ValueError("demo_case.inject_at must fall inside the simulated tail")
        return self

    @classmethod
    def load(cls, path: str | Path) -> "Scenario":
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))
