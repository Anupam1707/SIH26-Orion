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
| 5 | AI-Based Anomaly & Link Prediction | Phase 2 done | `module5/` |
| 6 | Explainable Intelligence & Dashboard | Spec written | `docs/` |

---

## Repository Structure

```text
SIH26/
|-- main_graph_loader.py           <- Module 3: full Neo4j load orchestrator
|-- verify_graph.py                <- Post-load sanity checks
|-- requirements.txt
|-- .env.example
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
|-- module5/                       <- Module 5: Anomaly Detection & Link Prediction
|   |-- README.md                  <- Module 5 detail, results, outstanding items
|   |-- anomaly_detection/
|   |   |-- oddball.py             <- Tier 2a: structural anomaly (OddBall)
|   |   `-- temporal.py            <- Tier 2b: temporal burst anomaly
|   |-- cypher_queries/
|   |   `-- aura_exports.cypher    <- Aura export + validation Cypher
|   |-- data/
|   |   |-- inputs/                <- egonet_data.csv, temporal_data.csv (from Aura)
|   |   `-- results/               <- oddball_results.csv, temporal_results.csv
|   `-- link_prediction/           <- Tier 3 (not yet started)
|
|-- data/dataset/                  <- CKG_FINAL_REPAIRED_DATASET (117 K rows)
|-- CKG_FINAL_REPAIRED_DATASET/    <- Original repaired dataset + GROUND_TRUTH.csv
`-- docs/                          <- Research specs for all 6 modules
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
python module5/anomaly_detection/oddball.py
python module5/anomaly_detection/temporal.py
```

See [`module5/README.md`](module5/README.md) for full validated results, honest limitations,
and outstanding items.

---

## Immediate Next Actions

1. Fix `burst_ratio` reweighting in `temporal.py`; re-validate A00069-74 cluster together
2. Confirm A00069 scatter receivers include A00071-74 (full structuring ring structure)
3. Decide Event-linkage routing for burner-swap and pre-event-burst typologies
4. Begin Tier 3 link prediction: Adamic-Adar / Resource Allocation / Katz baselines first
5. Build composite per-account risk score (Phase 1 + OddBall + temporal + Module 4 signals)
6. Explainability wrapper: every output ships with its specific evidence subgraph
7. Align with rest of team on Modules 1, 2, 6 status and cross-module conflicts (Section 4 of project log)

See `docs/` for full research documentation and module specs.
