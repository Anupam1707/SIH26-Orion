import json
import shutil

from app.precompute import (
    DEFAULT_SCENARIO, GROUND_TRUTH_FILE, WORLD_FILE, ANALYSIS_FILE, PREDICTIONS_FILE, cache_dir_for, load_or_build, scenario_hash,
)
from app.sim.runner import load_world
from app.state import DemoState


def test_hash_is_stable_and_tracks_content(tmp_path):
    copy = tmp_path / "s.json"
    shutil.copy(DEFAULT_SCENARIO, copy)
    assert scenario_hash(copy) == scenario_hash(DEFAULT_SCENARIO)

    data = json.loads(copy.read_text(encoding="utf-8"))
    data["seed"] = 7
    copy.write_text(json.dumps(data), encoding="utf-8")
    assert scenario_hash(copy) != scenario_hash(DEFAULT_SCENARIO)


def test_load_or_build_builds_once_and_writes_artefacts(tmp_path, world):
    cache_dir, manifest, built = load_or_build(DEFAULT_SCENARIO, tmp_path)
    assert built
    assert cache_dir == cache_dir_for(DEFAULT_SCENARIO, tmp_path)
    assert manifest["scenario_hash"] == cache_dir.name
    assert manifest["artefacts"] == [WORLD_FILE, GROUND_TRUTH_FILE, ANALYSIS_FILE, PREDICTIONS_FILE, 'evaluation.json']
    assert manifest['model_files']
    for name in manifest['model_files']:
        assert (cache_dir / name).is_file()
    for name in manifest["artefacts"]:
        assert (cache_dir / name).is_file()

    header = (cache_dir / GROUND_TRUTH_FILE).read_text(encoding="utf-8").splitlines()[0]
    assert header == "structure_id,type,network_id,strategy,members,start_ts,end_ts,is_demo"

    loaded = load_world(cache_dir / WORLD_FILE)
    assert loaded.transactions.equals(world.transactions)  # the cache is the simulation, byte for byte

    _, again, built_again = load_or_build(DEFAULT_SCENARIO, tmp_path)
    assert not built_again
    assert again["built_at"] == manifest["built_at"]


def test_reset_restores_snapshot(tmp_path):
    state = DemoState(cache_dir=tmp_path, manifest={}, data={"alerts": []})
    state.take_snapshot()
    state.demo_running = True
    state.data["alerts"].append("A1")

    state.reset()

    assert state.demo_running is False
    assert state.data == {"alerts": []}
