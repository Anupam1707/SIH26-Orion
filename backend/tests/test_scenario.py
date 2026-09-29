import copy
import random

import pytest
from pydantic import ValidationError

from app.sim.events import EventQueue
from app.sim.geo import point_in_ring, random_point_in_ring
from app.sim.scenario import Scenario


def with_changes(base: dict, mutate) -> dict:
    d = copy.deepcopy(base)
    mutate(d)
    return d


def test_default_scenario_loads(scenario):
    assert scenario.seed == 42
    assert len(scenario.districts) == 4
    assert scenario.history_end.isoformat() == "2026-08-30T00:00:00+05:30"
    assert scenario.demo_case.inject_at >= scenario.history_end


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda d: d["districts"][0]["neighbours"].append("D99"), "unknown neighbour"),
        (lambda d: d["networks"][0].update(collector_district="D99"), "collector_district"),
        (lambda d: d["demo_case"]["path"].update(l1_mules=99), "layer-1 mules"),
        (lambda d: d["demo_case"]["path"].update(l2_accounts=99), "layer-2 accounts"),
        (lambda d: d["demo_case"].update(inject_at="2026-08-01T10:15:00+05:30"), "end of history"),
        (lambda d: d["demo_case"].update(inject_at="2026-08-30T10:15:00"), "UTC offset"),
        (lambda d: d["demo_case"].update(network_id="N_Z"), "not a network"),
        (lambda d: d.update(complaint_delay_min=[90, 15]), "complaint_delay_min"),
    ],
)
def test_invalid_scenarios_are_rejected(scenario_dict, mutate, message):
    with pytest.raises(ValidationError, match=message):
        Scenario.model_validate(with_changes(scenario_dict, mutate))


def test_district_centroids_lie_inside_their_polygons(scenario):
    for d in scenario.districts:
        lng, lat = d.centroid
        assert point_in_ring(lng, lat, d.polygon[0]), d.id


def test_random_points_fall_inside_polygon(scenario):
    rng = random.Random(1)
    ring = scenario.districts[0].polygon[0]
    for _ in range(200):
        assert point_in_ring(*random_point_in_ring(rng, ring), ring)


def test_event_queue_orders_by_time_then_insertion(scenario):
    from datetime import timedelta

    t0 = scenario.start
    q = EventQueue()
    seen: list[str] = []
    q.schedule(t0 + timedelta(minutes=5), lambda ts, tag: seen.append(tag), "late")
    q.schedule(t0, lambda ts, tag: seen.append(tag), "first")
    q.schedule(t0, lambda ts, tag: seen.append(tag), "second")  # same ts: insertion order

    def spawn(ts):  # events may schedule more events inside the same window
        seen.append("spawner")
        q.schedule(ts + timedelta(minutes=1), lambda ts2: seen.append("child"))

    q.schedule(t0 + timedelta(minutes=2), spawn)
    q.run_until(t0 + timedelta(minutes=10))
    assert seen == ["first", "second", "spawner", "child", "late"]
    assert len(q) == 0


def test_event_queue_leaves_future_events(scenario):
    from datetime import timedelta

    q = EventQueue()
    q.schedule(scenario.start + timedelta(hours=2), lambda ts: None)
    assert q.run_until(scenario.start + timedelta(hours=1)) == 0
    assert len(q) == 1
