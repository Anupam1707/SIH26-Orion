<div align="center">
  <img src="assets/orion-logo-horizontal.png" alt="ORION Logo" width="340" />
  <h2>ORION Technical Documentation Suite</h2>
  <h4>Smart India Hackathon 2026 · Problem Statement ID: 26184</h4>
  <p><strong>Ministry of Home Affairs | Indian Cybercrime Coordination Centre (I4C)</strong></p>
  <p><em>Development of a Predictive Analytics Framework for Cybercrime Complaints to Forecast Likely Cash Withdrawal Locations in Advance</em></p>
</div>

---

## Documentation Index

| Document | Focus Area | Deliverable Alignment |
|---|---|---|
| [01-system-overview.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/01-system-overview.md) | Executive Mandate, National Cybercrime Reporting Portal (NCRP) integration, Reactive-to-Proactive paradigm shift, and system boundaries. | Overall System Architecture |
| [02-predictive-analytics-engine.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/02-predictive-analytics-engine.md) | Multi-hop transaction graph tracing, 5 typology detection rules, OddBall structural scoring, sliding-window temporal bursts, Spatial KDE, and Graph-Aware XGBoost. | **Key Deliverable (a)** |
| [03-risk-heatmap-dashboard.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/03-risk-heatmap-dashboard.md) | GIS vector visualization without external map tiles, ATM coordinate scoring, time-horizon filters (2h, 6h, 24h), probability thresholds, and model explainability drawers. | **Key Deliverable (b)** |
| [04-law-enforcement-interface.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/04-law-enforcement-interface.md) | Command Center, Cytoscape directed money flow visualizer, chronological step-by-step playback, inferred role tagging, and Section 63 BSA evidence compliance. | **Key Deliverable (c)** |
| [05-alert-and-notification-system.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/05-alert-and-notification-system.md) | Real-time threshold-based alerting engine, multi-channel dispatch (SMS, Email, REST API, In-app bell), and investigator acknowledgement lifecycle. | **Key Deliverable (d)** |
| [06-mincut-fund-blocking.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/06-mincut-fund-blocking.md) | Mathematical modeling of node-capacity minimum cut on directed transaction graphs, greedy fallback, and before/after fund interception simulation. | Actionable Interventions & CFCFRMS |
| [07-neo4j-demo-graph-guide.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/07-neo4j-demo-graph-guide.md) | Complete 39-node demo knowledge graph for Neo4j (Haryana/NCR cluster), visual color & size styling guide for slides, and presentation queries. | Visual Intelligence & Slides |
| [PROTOTYPE_OVERVIEW_SCRIPT.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/PROTOTYPE_OVERVIEW_SCRIPT.md) | **Refined 2.5–3 min prototype walkthrough script** with exact mouse cues, screen transitions, and expanded voiceover text. | Quick Demo & Video Recording |
| [DEMO_VIDEO_PLAN_AND_SCRIPT.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/DEMO_VIDEO_PLAN_AND_SCRIPT.md) | Full 5-minute deep-dive video demonstration blueprint, storyboard, and voiceover script. | Full Technical Presentation |
| [SUBMISSION_METADATA.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/SUBMISSION_METADATA.md) | **Official video titles, YouTube description with timestamps, short abstract, tags, and hashtags.** | Video Upload & Portal Submission |
| [phase-2.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/phase-2.md) | Phase 2 implementation summary: Graph engine, Typology detection, Case View, Command Center. | Historical Build Traceability |
| [phase-3.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/phase-3.md) | Phase 3 implementation summary: Prediction models (Baseline, KDE, XGBoost), Holdout evaluation, Risk Heatmap. | Historical Build Traceability |
| [phase-4.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/phase-4.md) | Phase 4 implementation summary: Multi-channel Alerts, Min-Cut Fund Blocking workbench. | Historical Build Traceability |
| [phase-5.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/phase-5.md) | Phase 5 implementation summary: Adversary Lab, Evasion Cost Curves, Greedy Search, Model Hardening. | Historical Build Traceability |
| [spec-v1.md](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/docs/spec-v1.md) | Original design specification and engineering constraints. | Reference Spec |

---

## Technical Specifications Summary

- **Backend:** FastAPI (Python 3.10 / 3.11), NetworkX, Scikit-Learn, XGBoost, Mesa, Pandas, NumPy, Pytest.
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Leaflet / React-Leaflet (Tile-free offline vector mode), Cytoscape.js, Recharts.
- **Data Integrity:** Strict chronological temporal filter ($t \le t_{\text{clock}}$), zero future leakage, Section 63 BSA compliance audit hashing.
- **Portability:** Deterministic seeding, precomputed cold-start caching, dual-platform startup (`./run.sh` for Unix/macOS, `.\run.ps1` for Windows PowerShell).
