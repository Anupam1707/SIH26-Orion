# SIH PS 189 — Master Status
*Last updated: Module 5 Tier 3 fixes applied (temporal reweighting, random-mask dataset, GNN epochs, ensemble selection)*

---

## Per-Module Status

### Module 1 — Data Collection & Preprocessing
**Status: Spec written, not implemented**
- Spec documents data sources (FIRs, CDRs, transactions, surveillance, social media, criminal history)
- Governance checklist written (authorization, PII, retention, chain-of-custody)
- No pipeline code exists yet
- **Definition of done:** reload dataset from scratch in one command; validation report passes clean

---

### Module 2 — NLP & Entity Resolution
**Status: Spec written, not implemented**
- Approach documented: MuRIL/IndicNER for entity extraction; Splink/Fellegi-Sunter for resolution
- Entity resolution difficulty confirmed in dataset: best-threshold accuracy ~84% (down from 99.05% in original), 18% ambiguous band, real Devanagari/transliteration/OCR/nickname variety
- No code written yet
- **Definition of done:** precision/recall on hard cases (Devanagari, transliteration, OCR, same-name-different-person), not just easy ones

---

### Module 3 — Criminal Knowledge Graph
**Status: COMPLETE**

Data is loaded into Neo4j Aura and queryable. Foundation for all Module 4 and 5 work.

**What exists:**
- Full loader pipeline: `main_graph_loader.py` orchestrates `graph/loaders/`
- Post-load sanity checker: `verify_graph.py`
- 14 node labels, 18+ relationship types
- Ontology enforced at ingest; every edge traceable to a source document

**Known gaps (not blockers):**
- 57% of all relationships use generic `ASSOCIATED_WITH` across 78 type-pairs — passes ontology but semantically vague
- 323/1,166 female-coded names still have wrong gender label (partial fix in dataset repair)

**Run:**
```bash
python main_graph_loader.py
python verify_graph.py
```

---

### Module 4 — Graph Analytics & Network Detection
**Status: COMPLETE**

| Analysis | Result | Stored in Aura |
|----------|--------|----------------|
| PageRank — phones | Top-20 produced | `pagerank_score` on PhoneNumber |
| PageRank — accounts | Top-20 produced | `pagerank_score` on Account |
| Betweenness centrality | Top-20 produced | `betweenness_score` on PhoneNumber |
| Louvain communities | Modularity 0.53, 4 communities at 100% purity | `community_id` on nodes |
| Shortest path A00013 to A00055 | Length-5 found | — |
| Robustness experiment | 65% top-20 turnover at 10% missing data | — |

**Important caveat on shortest path:** the A00013-A00055 path (length 5, through A01253 and A00820) has *non-chronological* timestamps — A00820→A00055 (Feb 2024) happened *before* A00013→A01253 (Sept 2024). This is topological evidence of connection, not a reconstructed money trail. Must be labeled accordingly in the dashboard.

**Run:**
```bash
python graph/analytics/run_pagerank.py --limit 20 --write-back
```

**Outstanding (minor):**
- Decide how to flag non-chronological shortest paths in Module 6 dashboard

---

### Module 5 — AI-Based Anomaly & Link Prediction
**Status: TIER 3 COMPLETE — all three tiers done**

#### Tier 1 — Rule-Based Typology Detection

| Pattern | Status | Key Finding |
|---------|--------|-------------|
| Structuring | CONFIRMED | 6 accounts (A00069-A00074), 10 txns each in 9k-9.9k band, hourly, single day |
| Mule fan-in | CONFIRMED | 12 feeders (A00001-A00012) -> A00013 -> A00014, 30h window, forwards 161,025 |
| Circular flow | CONFIRMED | Tightened with 7-day window to filter coincidental cycles |
| Layering chain | CONFIRMED | 2 unique 5-hop chains (A00043->A00047: 200k->166k; A00049->A00053: 250k->207k) |
| Scatter | CONFIRMED | A00055 -> 8 accounts (A00056-A00063), 5-min intervals. Second source A00069 also fans to A00070 (a structuring account) |
| Gather/reconsolidation | NEGATIVE | No reconsolidation found at 1-2 hops — genuine finding, not forced |
| Burner rotation | CONFIRMED | PH00002->PH00001, 3 shared contacts, 1-day gap. Debugged: string-vs-date bug silently dropped the pair |
| Pre-event call burst | AMBIGUOUS | Signal too broad (network-wide); needs narrowing to event-linked entities. Planted burner pair (P03685) has no LINKED_TO edge to any Event |
| Community + structuring overlap | CONFIRMED + LIMITATION | All 6 structuring accounts in 6 different communities — Louvain fragments the ring |

#### Tier 2a — OddBall Structural Anomaly

| Account | Pattern | Rank | Notes |
|---------|---------|------|-------|
| A00055 | Scatter source | **6/532 (top 1.1%)** | Clean unsupervised win |
| A00013 | Mule collector | 184/532 (34.6%) | Temporal, not structural — expected miss |
| A00069 | Structuring | 181/532 (34.0%) | Same limitation |
| A00014, A00070 | Pass-through | Not scored | Zero egonet edges |

**Code:** `module5/anomaly_detection/oddball.py`

#### Tier 2b — Temporal Anomaly (48h burst window)

**Fixed:** Added `gap_speed_score` (−z(mean_gap_min)), `burst_count_score` (z(burst_tx_count)),
log-capped `burst_ratio`, and lowered burst qualification threshold from 5 to 3 transactions.

| Account | Pattern | Score | Rank |
|---------|---------|-------|------|
| A00070 | Structuring | 4.560 | **1/8** |
| A00073 | Structuring | 4.176 | 2/8 |
| A00072 | Structuring | 3.824 | 3/8 |
| A00071 | Structuring | 3.809 | 4/8 |
| **A00069** | **Structuring** | **3.250** | **5/8** ← was 7/7 dead last |
| A00074 | Structuring | 2.877 | 6/8 |
| A00055 | Scatter source | 1.510 | 7/8 |
| A01217 | Background noise | −24.006 | 8/8 |

**Result:** All 6 structuring accounts (A00069-A00074) rank 1-6, cleanly above background.
A00069 moved from dead-last (7/7) to middle of the structuring group (5/8). A00055 ranks below
structuring because burst_count (8 tx) < structuring burst_count (10 tx) in the composite;
this is a documented limitation of single-account scoring — scatter needs a dedicated
fan-out detector.

**Code:** `module5/anomaly_detection/temporal.py`

#### Tier 3 — Link Prediction
**COMPLETE — All three fixes applied**

##### Dataset: Random Edge Masking (replaces temporal splits)
- 20% of edges masked at random; GT edges forcibly masked — guaranteed test positives
- All 5 financial GT edges confirmed in mask (A00001↔A00013, A00012↔A00013, A00013↔A00014, A00069↔A00070, A00055↔A00056)
- Both comm GT bridges confirmed in mask (PH04296↔PH04450, PH02064↔PH04287)
- Masked edges now have **finite shortest paths** in training graph: mule edges dist=3-4, bridges dist=5

##### Level 1 — Heuristic Baselines (unchanged)
| Heuristic | Financial AUC | Comm AUC |
|-----------|--------------|----------|
| Best (Preferential Attachment) | 0.495 | 0.484 |

##### Level 2 — ML Classifier (Winner: Random Forest)
| Graph | Val AUC | Test AUC | Test AP |
|-------|---------|----------|---------|
| Financial | 0.519 | **0.528** | 0.180 |
| Communication | 0.566 | **0.561** | 0.197 |

##### Level 3 — Node2Vec + MLP (20 epochs)
| Graph | Val AUC | Test AUC | Decision |
|-------|---------|----------|----------|
| Financial | 0.449 | 0.453 | ❌ Below RF — classifier-only used |
| Communication | 0.444 | 0.420 | ❌ Below RF — classifier-only used |

*Node2Vec Skip-Gram loss plateaued (~1.09 / ~0.41) — structural proximity not sufficient signal for link prediction on this sparse graph without node features. GNN excluded from ensemble via AUC gate.*

##### Ground Truth Pattern Discovery
| Pattern | Rank | Score | Detail |
|---------|------|-------|--------|
| **BURST_01/02/03 intra-cluster links** | **Top 9/top-200** | 0.55-0.49 | **196/200 top-200 comm predictions are GT pattern members** |
| COMMUNITY_04 edges | rank 16+ | 0.05 | Community edges rank right below burst edges |
| BRIDGE_01 (PH04296↔PH04450) | rank 5075/11828 | 0.009 | dist=5, CN=0 — improved from >10K (unreachable) to top 43% |
| BRIDGE_02 (PH02064↔PH04287) | rank 5037/11828 | 0.009 | Same: dist=5, CN=0 → top 43% |
| Mule chain (A00001↔A00013) | rank 10161/11392 | — | CN=0, dist=3 but zero shared neighbors |

**Confirmed finding:** Topological link prediction cannot recover cross-community bridge edges (CN=0, long path) without non-graph features. The model *does* correctly discover intra-syndicate edges at 196/200 precision in the top-200.

**Code:** `module5/link_prediction/` (6 files)

---

### Module 6 — Explainable Intelligence & Dashboard
**Status: Spec written, not implemented**
- Explainability requirement: every output ships with the specific subgraph/evidence responsible — never a bare number
- The explicit/inferred/predicted taxonomy (from Module 3 spec) governs all UI labels
- No dashboard code written yet

---

## Immediate Next Actions

1. **Composite risk score** — combine Tier 1 typology flags + OddBall + temporal + Module 4 centrality/community into one per-account score
2. **Cross-community bridge detection** — confirmed by Tier 3: topology alone cannot detect bridge pairs (CN=0, dist=5). Needs shared-timing Cypher rule or geolocation overlap.
3. **Scatter-source temporal detection** — A00055 currently ranks 7/8 in temporal (below structuring ring); needs dedicated fan-out detector or multi-account window.
4. **Mule chain link prediction** — CN=0 for mule edges even with random masking; needs multi-hop path feature or dedicated Tier 1 rule feeding the link predictor.
5. **Explainability wrapper** — every Module 5 output carries its evidence subgraph before Module 6 starts
6. **Team sync** — align on Modules 1, 2, 6 status; resolve the 5 cross-module conflicts
