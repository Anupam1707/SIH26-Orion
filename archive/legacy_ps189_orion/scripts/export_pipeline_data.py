#!/usr/bin/env python3
"""
scripts/export_pipeline_data.py — Export Pipeline Workbench Data for Web Dashboard
SIH PS 189 · I4C / Ministry of Home Affairs

Runs the pipeline on all test samples and exports structured payloads to
dashboard/src/data/pipeline_data.json for zero-latency, interactive UI execution.
"""

import sys
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.samples import SAMPLES
from pipeline.run_pipeline import run_input_to_leads_pipeline, clean_obj

OUT_FILE = ROOT / "dashboard" / "src" / "data" / "pipeline_data.json"

def main():
    print("Generating pipeline benchmark data for Web Dashboard...")
    payload = {
        "samples": SAMPLES,
        "precomputed_runs": {}
    }

    for sample_key, sample_input in SAMPLES.items():
        print(f"  • Running pipeline for sample: {sample_key}...")
        res = run_input_to_leads_pipeline(sample_input, verbose=False)
        payload["precomputed_runs"][sample_key] = res

    # Ensure output dir exists
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_obj(payload), f, indent=2, ensure_ascii=False)

    print(f"✓ Successfully wrote pipeline data to {OUT_FILE} ({OUT_FILE.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    main()
