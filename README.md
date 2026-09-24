# SIH26 — AI-Powered Criminal Network Analysis System
### SIH PS 189 · I4C / Ministry of Home Affairs

> **Governing principle:** the system produces **leads, not proof**. Every output — a predicted link, an anomaly score, a centrality ranking — is a suggestion for human investigator review, never an accusation.

---

## Module Status

| # | Module | Status | Location |
|---|--------|--------|----------|
| 1 | Data Collection & Preprocessing | Spec written | `docs/` |
| 2 | NLP & Entity Resolution | Spec written | `docs/` |
| 3 | Criminal Knowledge Graph | Complete | `graph/`, `main_graph_loader.py` |
| 4 | Graph Analytics & Network Detection | Complete | `graph/analytics/` |
| 5 | AI-Based Anomaly & Link Prediction | Complete | `intelligence/` |
| 6 | Explainable Intelligence & Dashboard | **Complete (Live)** | `dashboard/`, [https://orion26-team.web.app](https://orion26-team.web.app) |

---

## Repository Structure

```text
SIH26/
|-- dashboard/                     <- Module 6: Live Investigator Dashboard (Vite + React + D3)
|   |-- src/                       <- Components, D3 Force Graph, Dossier, Typology Viewer
|   |-- package.json
|   `-- dist/                      <- Production build deployed to Firebase
|
|-- main_graph_loader.py           <- Module 3: full Neo4j load orchestrator
|-- verify_graph.py                <- Post-load sanity checks
|-- requirements.txt
|-- .env.example
|-- .firebaserc                    <- Firebase project: orion26-team
|-- firebase.json                  <- Hosting configuration pointing to dashboard/dist
|
|-- graph/                         <- Module 3 & 4 code
|   |-- config.py                  <- Neo4j connection (.env)
|   |-- schema.py                  <- Constraints + indexes
|   |-- utils.py                   <- Batch UNWIND helpers
|   |-- loaders/                   <- One loader per entity/relationship type
|   |   |-- load_entities.py
|   |   |-- load_cases.py
|   |   |-- load_evidence.py
|   |   |-- load_relationships.py
|   |   `-- load_entity_resolution.py
|   `-- analytics/
|       |-- pagerank.py            <- PageRank implementation
|       `-- run_pagerank.py        <- CLI entry point
|
|-- pipeline/                      <- End-to-End Input-to-Leads Processing Pipeline
|   |-- README.md                  <- Pipeline documentation & execution instructions
|   |-- samples.py                 <- Multi-source test samples (FIR, Banking, CDR)
|   |-- extractor.py               <- Multilingual entity & flow extractor
|   |-- entity_resolver.py         <- Devanagari, initials & OCR alias resolution
|   |-- graph_updater.py           <- Tri-partite knowledge graph manager
|   |-- detector.py                <- 4-Tier Anomaly Engine (Typology, OddBall, Burst, LP)
|   |-- lead_generator.py          <- Section 63 BSA certified lead synthesis
|   `-- run_pipeline.py            <- CLI & programmatic pipeline orchestrator
|
|-- intelligence/                  <- Module 5: Intelligence, Anomaly Detection & Link Prediction
|   |-- README.md                  <- Architecture, validated results, honest scientific benchmarks
|   |-- anomaly_detection/
|   |   |-- oddball.py             <- Tier 2a: structural anomaly (OddBall)
|   |   `-- temporal.py            <- Tier 2b: temporal burst anomaly
|   |-- cypher_queries/
|   |   `-- aura_exports.cypher    <- Aura export + validation Cypher
|   |-- data/
|   |   |-- inputs/                <- egonet_data.csv, temporal_data.csv
|   |   |-- results/               <- oddball_results.csv, temporal_results.csv
|   |   `-- link_prediction/       <- Trained models, predictions, and evidence subgraphs
|   `-- link_prediction/           <- Tier 3 Link Prediction models & evidence subgraphs
|
|-- data/dataset/                  <- CKG_FINAL_REPAIRED_DATASET (117 K rows)
|-- CKG_FINAL_REPAIRED_DATASET/    <- Original repaired dataset + GROUND_TRUTH.csv
`-- docs/                          <- Research specs for all 6 modules
```

### Core System: Input-to-Leads Pipeline Quickstart
```bash
# Run pipeline on sample Cyber Fraud FIR (extracts Devanagari suspect, stitches aliases, outputs BSA leads)
python3 pipeline/run_pipeline.py --sample fir

# Run pipeline on bank smurfing transaction stream (detects sub-threshold structuring)
python3 pipeline/run_pipeline.py --sample structuring

# Run pipeline on CDR telecommunications stream (detects 48h pre-event coordination bursts)
python3 pipeline/run_pipeline.py --sample cdr
```

---

## Module 3 — Criminal Knowledge Graph  (Complete)

```bash
pip install -r requirements.txt
cp .env.example .env          # set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
python main_graph_loader.py   # full load
python verify_graph.py        # post-load sanity check
```

**Graph schema:** 14 node labels (`Person`, `Account`, `PhoneNumber`, `Organization`,
`Vehicle`, `Location`, `Event`, `Case`, `Crime`, `Evidence`, `Document`, `Alias`,
`Source`, `Observation`) and 18+ relationship types including `HOLDS_ACCOUNT`,
`OWNS_PHONE`, `CALLED`, `TRANSACTED`, `MEMBER_OF`, `SAME_ENTITY` /
`DIFFERENT_ENTITY` / `UNCERTAIN_ENTITY`.

**Infrastructure note:** all date/time fields in Aura are stored as **plain strings**,
not native Neo4j datetime types. Fix pattern: `datetime(replace(field, ' ', 'T'))` for
timestamps, `date(field)` for date-only fields. Bare string comparisons silently return
empty results with no error — see project log Section 6.

---

## Module 4 — Graph Analytics  (Complete)

| Analysis | Result |
|----------|--------|
| PageRank (phones + accounts) | Top-20 written back to Aura as `pagerank_score` |
| Betweenness centrality | Top-20 written back as `betweenness_score` |
| Louvain community detection | Modularity **0.53** — 4 planted communities at 100% purity |
| Shortest path (A00013 to A00055) | Length-5 path found — topological connection, not a money trail (timestamps are non-chronological; labeled accordingly) |
| Robustness experiment | Removing 10% of nodes changed **65% of the top-20** PageRank list — documented honestly, not hidden |

```bash
python graph/analytics/run_pagerank.py --limit 20
python graph/analytics/run_pagerank.py --limit 20 --write-back --export pagerank_top20.csv
```

---

## Module 5 — Anomaly Detection & Link Prediction  (Phase 2 complete)

Three-tier architecture — simple methods proven first, complexity added only where justified
(per BOND / GADBench published benchmarks):

| Tier | Method | Status |
|------|--------|--------|
| 1 | Rule-based Cypher typologies | 7/9 typologies validated against GROUND_TRUTH.csv |
| 2a | OddBall structural scoring | Validated — A00055 (scatter source) top 1.1% of 532 accounts |
| 2b | 48h burst window, z-scored composite | Validated — one reweighting fix outstanding |
| 3 | Adamic-Adar / RA / Katz baselines -> SEAL GNN | Not started |

**Key honest findings documented (not hidden):**
- OddBall is structurally blind to temporal fraud (structuring, mule fan-in) — this motivated Tier 2b
- `burst_ratio` over-dominates the temporal composite when accounts have high background volume — fix outstanding before feeding the composite risk score
- Mule fan-in (A00013) missed by OddBall and temporal scoring — confirmed 3x that cross-account convergence needs a dedicated cross-account detector
- Louvain fragments the structuring ring (A00069-74) across 6 communities — citable limitation

```bash
python intelligence/anomaly_detection/oddball.py
python intelligence/anomaly_detection/temporal.py
```

See [`intelligence/README.md`](intelligence/README.md) for full validated results, honest limitations,
and outstanding items.

---

## Module 6 — Explainable Intelligence & Dashboard  (Complete & Live)

**Production Web App:** [https://orion26-team.web.app](https://orion26-team.web.app) (Firebase Hosting)

| Feature | Implementation | Live Status |
|---------|----------------|-------------|
| Knowledge Graph Explorer | D3 force simulation, smooth zoom/pan/drag, entity badging | ✅ Active |
| Evidentiary Taxonomy | Strict Explicit (solid green) / Inferred (dashed amber) / Predicted (dotted purple) | ✅ Active |
| Typology & Anomaly Center | 8 Ground Truth Typologies + A00013-A00055 topological bridge | ✅ Active |
| Link Prediction Studio | Evidence subgraphs, multi-hop paths, RF vs GNN benchmarks | ✅ Active |
| Entity Resolution Workbench | Devanagari (`नेहा`), transliterations (`Arjd.`), OCR corruptions (`Nikhi1`) | ✅ Active |
| Section 63 BSA Lead Export | Real-time SHA-256 digital signature hash, JSON download, 1-click print PDF | ✅ Active |
| Guided Demo Tour for Judges | 5-step evaluator tour executable via UI or keyboard shortcuts | ✅ Active |

```bash
# Run locally
cd dashboard
npm install
npm run dev     # dev server at http://localhost:5173

# Deploy to Firebase Hosting
npm run build
cd ..
firebase deploy --only hosting
```

---

## Immediate Next Actions

1. Module 1 Ingestion Pipeline: Build unified CSV/JSON automated CLI importer for heterogeneous police FIRs.
2. Module 2 NLP Fine-Tuning: MuRIL transformer model adaptation on Devanagari transliteration pairs.
3. Cross-Community Telecom Bridge Prediction: Incorporate auxiliary cell tower coordinates and timing synchrony.
4. Practice Live Judge Demo using the **"Guided Demo (Judges Tour)"** feature on [https://orion26-team.web.app](https://orion26-team.web.app).

See `docs/` for full research documentation and module specs.
