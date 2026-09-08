# Module 5 — AI-Based Anomaly Detection & Link Prediction
### SIH PS 189 · Criminal Network Discovery

---

## Architecture — Three Tiers, Deliberate Order

> Published benchmarks (BOND, GADBench) found simple methods frequently beat
> specialised graph neural networks. Simple methods are established as the
> baseline before complexity is added — not assumed inferior.

| Tier | Directory | Status | Method |
|------|-----------|--------|--------|
| 1 | `cypher_queries/` | ✅ 7/9 typologies clean | Rule-based Cypher pattern matching |
| 2a | `anomaly_detection/oddball.py` | ✅ Validated | OddBall structural scoring (Akoglu et al. 2010) |
| 2b | `anomaly_detection/temporal.py` | ✅ Validated | 48h burst window, z-scored composite |
| 3 | `link_prediction/` | 🔲 Not started | Adamic-Adar / RA / Katz → SEAL GNN |

---

## Directory Layout

```
module5/
├── anomaly_detection/
│   ├── oddball.py          # Tier 2a — structural anomaly detection
│   └── temporal.py         # Tier 2b — temporal anomaly detection
├── cypher_queries/
│   └── aura_exports.cypher # Aura export + validation Cypher
├── data/
│   ├── inputs/
│   │   ├── egonet_data.csv     # Egonet features exported from Aura
│   │   └── temporal_data.csv   # Transaction timestamps per account from Aura
│   └── results/
│       ├── oddball_results.csv  # OddBall output (all accounts scored)
│       └── temporal_results.csv # Temporal scorer output
└── link_prediction/        # Tier 3 — not yet started
```

---

## Running the Scripts

Both scripts resolve paths relative to their own file location, so they work
from any working directory:

```bash
# From project root:
python module5/anomaly_detection/oddball.py
python module5/anomaly_detection/temporal.py

# Or from the anomaly_detection directory:
cd module5/anomaly_detection
python oddball.py
python temporal.py
```

To refresh the input CSVs from Aura, run the queries in
`cypher_queries/aura_exports.cypher` in the Aura Browser and export as CSV
to `data/inputs/`.

---

## Validated Results (Phase 2 summary)

### OddBall Structural Scoring

| Account | Pattern | Rank | Notes |
|---------|---------|------|-------|
| A00055 | Scatter source | **6/532 (top 1.1%)** | ✅ Clean unsupervised win |
| A00013 | Mule collector | 184/532 (34.6%) | Temporal, not structural — expected miss |
| A00069 | Structuring | 181/532 (34.0%) | Same limitation |
| A00014, A00070 | Pass-through | Not scored | Zero egonet edges |

### Temporal Scoring (7 accounts with 5+ tx and a 5+ tx burst window)

| Account | Pattern | Score | Rank |
|---------|---------|-------|------|
| A00055 | Scatter source | 1.550 | **1/7** |
| A00070 | Structuring | 1.101 | 2/7 |
| A00073–A00072–A00071–A00074 | Structuring | –0.377 to –0.787 | 3–6/7 |
| A00069 | Structuring / scatter source | –1.293 | 7/7 |

**Known limitation:** `burst_ratio` over-dominates when accounts have high
background tx volume — A00069 (17 total tx) scores dead-last despite the same
planted burst as A00070 (13 total tx). Fix outstanding: reweight so
`burst_tx_count` and `mean_gap_min` count more than `burst_ratio`.

---

## Outstanding (from project log Section 8.5)

- [ ] Fix burst_ratio/total_tx reweighting; re-validate A00069–74 cluster together
- [ ] Narrow pre-event call burst typology to event-linked entities
- [ ] Confirm A00069 scatter receivers include A00071–74 (full ring structure)
- [ ] Decide Event-linkage routing for burner-swap typologies
- [ ] Tier 3: Adamic-Adar / Resource Allocation / Katz heuristic baselines
- [ ] Composite risk score combining Phase 1 + OddBall + temporal + Module 4 centrality
- [ ] Explainability wrapper (every output ships with its evidence subgraph)
