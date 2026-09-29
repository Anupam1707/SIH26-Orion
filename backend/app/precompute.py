"""Build the precompute cache.

Everything expensive (simulation, detection, model training, adversary curves)
is computed once and written to ``backend/.cache/<scenario-hash>/``. The API
loads that directory at startup and only rebuilds when the scenario file
changes. Run directly with ``python -m app.precompute``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import pickle
from datetime import datetime, timezone
from pathlib import Path

from app.sim.runner import export_ground_truth, run_scenario, save_world
from app.sim.scenario import Scenario

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SCENARIO = BACKEND_DIR / "scenarios" / "indore_demo.json"
DEFAULT_CACHE_ROOT = BACKEND_DIR / ".cache"

# Bump when the cache layout or any precompute logic changes, so an old cache
# built from the same scenario is not silently reused.
CACHE_VERSION = 5

WORLD_FILE = "world.pkl"
GROUND_TRUTH_FILE = "ground_truth.csv"
ANALYSIS_FILE = "analysis.pkl"
PREDICTIONS_FILE = "predictions.pkl"
MODELS_DIR = 'models'


def scenario_hash(scenario_path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(f"v{CACHE_VERSION}:".encode())
    digest.update(scenario_path.read_bytes())
    return digest.hexdigest()[:16]


def cache_dir_for(scenario_path: Path, cache_root: Path = DEFAULT_CACHE_ROOT) -> Path:
    return cache_root / scenario_hash(scenario_path)


def build(scenario_path: Path = DEFAULT_SCENARIO, cache_root: Path = DEFAULT_CACHE_ROOT) -> Path:
    """Build the cache for ``scenario_path`` and return its directory."""
    scenario = Scenario.load(scenario_path)  # validates before any work is done
    out = cache_dir_for(scenario_path, cache_root)
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    world = run_scenario(scenario)
    sim_seconds = round(time.perf_counter() - t0, 2)
    save_world(world, out / WORLD_FILE)
    export_ground_truth(world, out / GROUND_TRUTH_FILE)

    from app.data import Public
    from app.detect.service import analyze
    public = Public.from_world(world)
    demo = world.frauds[world.frauds.is_demo].iloc[0]
    demo_tx = world.transactions[world.transactions.fraud_id == demo['id']]
    complaint = world.complaints[world.complaints.id == world.meta['demo_complaint_id']].iloc[0]
    trace_clock = max(demo_tx.ts.max(), complaint.reported_at).to_pydatetime()
    snapshots = {clock.isoformat(): analyze(public, clock, scenario.detection)
                 for clock in (scenario.history_end, trace_clock)}
    with (out / ANALYSIS_FILE).open('wb') as handle:
        pickle.dump(snapshots, handle)
    from app.predict.pipeline import build_predictions
    predictions = build_predictions(world, scenario, out / MODELS_DIR)
    with (out / PREDICTIONS_FILE).open('wb') as handle:
        pickle.dump(predictions, handle)
    (out / 'evaluation.json').write_text(json.dumps({**predictions['full_evaluation'], **predictions['metadata']}, indent=2), encoding='utf-8')
    # The manifest is written last so a half-built directory is never mistaken for a complete cache.
    manifest = {
        "scenario_hash": out.name,
        "scenario_file": scenario_path.name,
        "seed": scenario.seed,
        "cache_version": CACHE_VERSION,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "sim_seconds": sim_seconds,
        "history_end": world.meta["history_end"],
        "trace_clock": trace_clock.isoformat(),
        "demo_complaint_id": world.meta["demo_complaint_id"],
        "counts": world.meta["counts"],
        "artefacts": [WORLD_FILE, GROUND_TRUTH_FILE, ANALYSIS_FILE, PREDICTIONS_FILE, 'evaluation.json'],
        "model_files": [p.relative_to(out).as_posix() for p in sorted((out / MODELS_DIR).glob('*.ubj'))],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


def load_or_build(
    scenario_path: Path = DEFAULT_SCENARIO, cache_root: Path = DEFAULT_CACHE_ROOT
) -> tuple[Path, dict, bool]:
    """Return (cache dir, manifest, built_now)."""
    out = cache_dir_for(scenario_path, cache_root)
    manifest_path = out / "manifest.json"
    built_now = False
    if not manifest_path.exists():
        build(scenario_path, cache_root)
        built_now = True
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return out, manifest, built_now


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SCENARIO
    cache, manifest, built = load_or_build(path)
    print(f"cache {'built' if built else 'up to date'}: {cache}")
    print(f"  {manifest['counts']}")
    from app.predict.evaluate import print_table
    print_table(json.loads((cache / 'evaluation.json').read_text(encoding='utf-8')))
