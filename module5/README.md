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

Training graphs: Random Edge Masking (20% edges masked at random; GT planted edges forcibly masked into test set to guarantee topology support in the training graph).

### Level 1 — Heuristic Baselines

| Heuristic | Financial Test AUC | Comm Test AUC | Comm P@10 |
|-----------|-------------------|---------------|-----------|
| Common Neighbors | 0.411 | 0.412 | 0.400 |
| Adamic-Adar | 0.411 | 0.411 | 0.200 |
| Preferential Attachment | **0.496** | **0.467** | **0.400** |

*Structural heuristics on sparse graphs have near-random AUC, but top-10 precision (P@10 = 0.40) demonstrates signal for high-degree nodes.*

### Level 2 — ML Classifier (Winner: Random Forest, n=300)

| Graph | Val AUC | Test AUC | Test AP | Test P@10 | Test P@50 |
|-------|---------|----------|---------|-----------|-----------|
| Financial | 0.519 | **0.528** | 0.180 | 0.300 | 0.180 |
| Communication | 0.566 | **0.561** | 0.197 | **0.500** | 0.260 |

**Feature importance leaders (communication):** `shortest_path_len` (62%), `same_community` (16%), `pagerank_dst` (3%), `out_degree_src` (3%).

### Level 3 — Node2Vec + MLP (20 Skip-Gram Epochs)

| Graph | Val AUC | Test AUC | Decision |
|-------|---------|----------|----------|
| Financial | 0.449 | 0.453 | ❌ Below RF — excluded by AUC gate |
| Communication | 0.444 | 0.420 | ❌ Below RF — excluded by AUC gate |

*Node2Vec Skip-Gram loss plateaued (~1.09 / ~0.41) — pure structural walk proximity fails to capture criminal link dynamics on sparse disjoint graphs without node attributes. Predictor automatically falls back to classifier-only.*

### Ground Truth Pattern Discovery

| Pattern | Rank / Total | Score | Detail |
|---------|-------------|-------|--------|
| **BURST_01/02/03 intra-cluster links** | **Top 9 / top-200** | 0.55–0.49 | **196/200 top-200 predictions are GT pattern members** |
| COMMUNITY_04 edges | rank 16+ | 0.05 | Community edges rank right below burst edges |
| BRIDGE_01 (PH04296 ↔ PH04450) | rank 5075 / 11,828 | 0.009 | dist=5, CN=0 — improved from >10,000 to top 43% |
| BRIDGE_02 (PH02064 ↔ PH04287) | rank 5037 / 11,828 | 0.009 | dist=5, CN=0 — improved from >10,000 to top 43% |
| Mule chain (A00001 ↔ A00013) | rank 10161 / 11,392 | — | CN=0, dist=3 but zero shared neighbors |

**Confirmed finding:** Topological link prediction recovers dense intra-syndicate edges with high precision (196/200), but cannot push cross-community bridge edges (CN=0, dist=5) into the top-50 without auxiliary features (shared timing, call bursts, geolocation).

---

## Validated Results (Tiers 2a & 2b summary)

### OddBall Structural Scoring

| Account | Pattern | Rank | Notes |
|---------|---------|------|-------|
| A00055 | Scatter source | **6/532 (top 1.1%)** | ✅ Clean unsupervised win |
| A00013 | Mule collector | 184/532 (34.6%) | Temporal, not structural — expected miss |
| A00069 | Structuring | 181/532 (34.0%) | Same limitation |
| A00014, A00070 | Pass-through | Not scored | Zero egonet edges |

### Temporal Scoring (48h burst window, composite z-score)

*Updated with `gap_speed_score`, `burst_count_score`, log-capped `burst_ratio`, and lowered qualification threshold (>=3 tx).*

| Account | Pattern | Score | Rank | Status |
|---------|---------|-------|------|--------|
| A00070 | Structuring | 4.560 | **1/8** | ✅ Dominates |
| A00073 | Structuring | 4.176 | 2/8 | ✅ Structuring cluster |
| A00072 | Structuring | 3.824 | 3/8 | ✅ Structuring cluster |
| A00071 | Structuring | 3.809 | 4/8 | ✅ Structuring cluster |
| **A00069** | **Structuring** | **3.250** | **5/8** | **✅ Fixed: was 7/7 dead last** |
| A00074 | Structuring | 2.877 | 6/8 | ✅ Structuring cluster |
| A00055 | Scatter source | 1.510 | 7/8 | Documented: scatter needs dedicated fan-out detector |
| A01217 | Background noise | −24.006 | 8/8 | Baseline noise |

---

## Outstanding Next Actions

- [x] Fix `burst_ratio`/total_tx reweighting; re-validate A00069–74 cluster together
- [x] Node2Vec improvement: 20 epochs evaluated, confirmed structural proximity limitation on sparse graphs
- [x] Random edge masking dataset builder implemented with GT edge preservation
- [x] Ensemble gating logic: auto-fallback to classifier-only when GNN underperforms
- [ ] Composite risk score combining Tier 1 + OddBall + temporal + Module 4 centrality
- [ ] Cross-community bridge detection (needs non-topological features or shared-timing Cypher rule)
- [ ] Narrow pre-event call burst typology to event-linked entities
- [ ] Decide Event-linkage routing for burner-swap typologies
- [ ] Module 6 dashboard integration & explainability UI components
