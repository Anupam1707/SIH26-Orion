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
| 3 | `link_prediction/` | ✅ Complete | Heuristics → RF classifier → Node2Vec+MLP |

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
│   │   ├── egonet_data.csv
│   │   └── temporal_data.csv
│   ├── results/
│   │   ├── oddball_results.csv
│   │   └── temporal_results.csv
│   └── link_prediction/    # Tier 3 outputs
│       ├── *_pos/neg_{financial,communication}.csv  # Edge splits
│       ├── features_{train,val,test}_{graph}.parquet
│       ├── heuristics_{val,test}_{graph}.csv
│       ├── best_model_{graph}.pkl
│       ├── node_embeddings_{graph}.npy + node_index_{graph}.json
│       ├── predictions_{graph}.csv
│       └── evidence_subgraphs_{graph}.json
└── link_prediction/        # Tier 3 code
    ├── dataset_builder.py    # Temporal train/val/test splits + neg sampling
    ├── heuristics.py         # Level 1: AA, RA, Jaccard, PA, CN baselines
    ├── feature_pipeline.py   # Level 2: Edge feature engineering
    ├── train_classifier.py   # Level 2: LR / RF / GBM training + evaluation
    ├── gnn_embedder.py       # Level 3: Node2Vec + MLP link prediction head
    └── predict_and_explain.py # Inference + evidence subgraphs + GT recall
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

## Validated Results — Tier 3 (Link Prediction)

Training graphs: 70% temporal split. Evaluated against held-out 15% val / 15% test.

### Level 1 — Heuristic Baselines

| Heuristic | Financial Val AUC | Comm Val AUC |
|-----------|------------------|--------------|
| Adamic-Adar | 0.406 | 0.399 |
| Preferential Attachment | **0.480** | **0.414** |

*Near-random: topology alone insufficient. Every Level 2+ model must beat this.*

### Level 2 — ML Classifier (Winner: Random Forest, n=300)

| Graph | Val AUC | Test AUC | Test AP |
|-------|---------|----------|---------|
| Financial | 0.506 | **0.529** | 0.189 |
| Communication | 0.602 | **0.618** | 0.322 |

**Feature importance leaders (communication):** `shortest_path_len` (62%), `same_community` (16%), `pagerank_dst` (3%), `out_degree_src` (3%)

### Level 3 — Node2Vec + MLP

| Graph | Val AUC | Test AUC | Decision |
|-------|---------|----------|----------|
| Financial | 0.476 | 0.478 | ❌ Below RF — not used in production |
| Communication | 0.450 | 0.443 | ❌ Below RF — not used in production |

### Ground Truth Pattern Discovery (Top-50 predictions)

| Pattern | Recovered? | Detail |
|---------|------------|--------|
| BURST_02 intra-cluster links | **✅ 11/50 in top-50** | Model discovers BURST_02 members as most likely to link |
| LAYERING_02 | Partial (rank 15) | 1 member pair appears in top-50 |
| BRIDGE_01 / BRIDGE_02 | ❌ Not recovered | Cross-component: no shared neighbors, shortest path = ∞ |
| MULE_01 chain | ❌ Not recovered | Star-topology mule chains not captured by 2-hop heuristics |

---

## Validated Results (Tiers 2a & 2b summary)

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
- [ ] Decide Event-linkage routing for burner-swap typologies
- [ ] Composite risk score combining Tier 1 + OddBall + temporal + Module 4 centrality
- [ ] Cross-community bridge detection (needs non-topological features)
- [ ] Node2Vec improvement: more epochs / p,q tuning / torch_geometric GCN option
- [ ] Explainability wrapper (every output ships with its evidence subgraph)
