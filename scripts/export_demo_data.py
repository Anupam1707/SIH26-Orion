#!/usr/bin/env python3
"""Export demo data from FastAPI backend into frontend/public/data/demoData.json for standalone Vercel deployment."""

import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "backend"))

from app.main import app

def main():
    with TestClient(app) as client:
        # 1. Initial state (history end)
        client.post("/demo/reset")
        init_health = client.get("/health").json()
        init_summary = client.get("/summary").json()
        init_complaints = client.get("/complaints").json()
        districts = client.get("/districts").json()
        init_prediction_cases = client.get("/prediction-cases").json()
        init_alerts = client.get("/alerts").json()
        curves = client.get("/adversary/curves").json()

        # 2. Advance to start state (trace clock)
        start_res = client.post("/demo/start").json()
        demo_complaint_id = start_res["complaint_id"]
        started_health = client.get("/health").json()
        started_summary = client.get("/summary").json()
        started_complaints = client.get("/complaints").json()
        started_prediction_cases = client.get("/prediction-cases").json()
        evaluation = client.get("/evaluation").json()

        # 3. Traces and Accounts
        traces = {}
        accounts = {}
        block_recs = {}
        predictions = {}

        cases_to_fetch = [demo_complaint_id, "C00083", "C00082", "C00081"]
        for c in started_complaints[:6]:
            if c["id"] not in cases_to_fetch:
                cases_to_fetch.append(c["id"])

        for cid in cases_to_fetch:
            try:
                tr = client.get(f"/cases/{cid}/trace").json()
                traces[cid] = tr
                for node in tr.get("nodes", []):
                    nid = node["id"]
                    if nid not in accounts:
                        try:
                            acc = client.get(f"/accounts/{nid}").json()
                            if "transactions" in acc:
                                acc["transactions"] = acc["transactions"][-30:]
                            if "source_transactions" in acc:
                                acc["source_transactions"] = acc["source_transactions"][-30:]
                            accounts[nid] = acc
                        except Exception:
                            pass
            except Exception as e:
                print(f"Warning: trace for {cid} failed: {e}")

            try:
                br = client.get(f"/block/{cid}").json()
                block_recs[cid] = br
            except Exception as e:
                print(f"Warning: block rec for {cid} failed: {e}")

            # Fetch predictions for the primary demo cases
            if cid in (demo_complaint_id, "C00083"):
                for m in ["baseline", "kde", "xgboost"]:
                    for w in [2, 6, 24]:
                        try:
                            pr = client.get(f"/predictions/{cid}?model={m}&window={w}").json()
                            if "evidence" in pr and "withdrawals" in pr["evidence"]:
                                pr["evidence"]["withdrawals"] = pr["evidence"]["withdrawals"][-60:]
                            if "evidence" in pr and "transactions" in pr["evidence"]:
                                pr["evidence"]["transactions"] = pr["evidence"]["transactions"][-60:]
                            predictions[f"{cid}_{m}_{w}"] = pr
                        except Exception as e:
                            pass

        # 4. Generate alerts for demo complaint
        gen_alerts_res = client.post(f"/alerts/generate/{demo_complaint_id}").json()
        alerts_after_gen = client.get("/alerts").json()

        # 5. Adversary simulation
        adv_baseline = client.post("/adversary/run", json={"complaint_id": demo_complaint_id, "hardened": False}).json()
        adv_hardened = client.post("/adversary/run", json={"complaint_id": demo_complaint_id, "hardened": True}).json()

        demo_data = {
            "demo_complaint_id": demo_complaint_id,
            "districts": districts,
            "evaluation": evaluation,
            "curves": curves,
            "initial": {
                "health": init_health,
                "summary": init_summary,
                "complaints": init_complaints,
                "prediction_cases": init_prediction_cases,
                "alerts": init_alerts,
            },
            "started": {
                "health": started_health,
                "summary": started_summary,
                "complaints": started_complaints,
                "prediction_cases": started_prediction_cases,
                "alerts": alerts_after_gen if alerts_after_gen else (gen_alerts_res.get("alerts") or []),
            },
            "traces": traces,
            "accounts": accounts,
            "block_recs": block_recs,
            "predictions": predictions,
            "adversary": {
                "baseline": adv_baseline,
                "hardened": adv_hardened,
            },
        }

        out_dir = root / "frontend" / "public" / "data"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "demoData.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(demo_data, f, separators=(',', ':'))

        print(f"Successfully exported demo data to {out_path} ({round(out_path.stat().st_size / 1024, 1)} KB)")

if __name__ == "__main__":
    main()
