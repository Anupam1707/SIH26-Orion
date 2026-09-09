# SIH PS 189 — Master Status
*Last updated: Module 5 Phase 2b (temporal anomaly scoring, validated against ground truth)*

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

| Account | Pattern | Score | Rank |
|---------|---------|-------|------|
| A00055 | Scatter source | 1.550 | **1/7** |
| A00070 | Structuring | 1.101 | 2/7 |
| A00073/72/71/74 | Structuring | -0.38 to -0.79 | 3-6/7 |
| A00069 | Structuring/scatter | -1.293 | **7/7 (dead last)** |

**Known reweighting flaw:** `burst_ratio` over-dominates when accounts have high background volume. A00069 (17 total tx) ranks dead-last despite the same hourly burst as A00070 (13 total tx). A launderer who blends in normal activity currently scores *less* suspicious — the opposite of correct.

**Code:** `module5/anomaly_detection/temporal.py`

#### Tier 3 — Link Prediction
**COMPLETE — Level 1 & 2 validated; Level 3 GNN underperforms ML baseline**

##### Level 1 — Heuristic Baselines

| Heuristic | Financial Val AUC | Comm Val AUC |
|-----------|------------------|--------------|
| Adamic-Adar | 0.406 | 0.399 |
| Preferential Attachment | **0.480** | **0.414** |
| Common Neighbors / Jaccard / RA | ~0.407 | ~0.399 |

*Key finding: topology alone is near-random for future link prediction on these sparse graphs — structural heuristics all AUC ≈ 0.40.*

##### Level 2 — ML Classifier (Best: Random Forest)

| Graph | Val AUC | Test AUC | Test AP | vs. Best Heuristic |
|-------|---------|----------|---------|--------------------|
| Financial | 0.506 | **0.529** | 0.189 | +5 pts |
| Communication | 0.602 | **0.618** | 0.322 | +19 pts |

**Top features by importance:** `shortest_path_len` (0.75 fin / 0.62 comm), `same_community` (0.16 comm), `pagerank_dst`, `out_degree_src`, `tx_per_day_src`

##### Level 3 — Node2Vec + MLP

| Graph | Val AUC | Test AUC | vs. RF Classifier |
|-------|---------|----------|-----------------|
| Financial | 0.476 | 0.478 | −5 pts (worse) |
| Communication | 0.450 | 0.443 | −17 pts (worse) |

*Node2Vec with only 5 skip-gram epochs did not converge to representations better than topological features. RF classifier is the production model.*

##### Ground Truth Pattern Discovery (Top-50 predictions)

| Graph | Observation |
|-------|-------------|
| Communication | **11/50 top predictions involve BURST_02 planted pattern members** — model recovers intra-syndicate structure |
| Financial | 1/50 top predictions involves a LAYERING_02 member |
| Bridge recall (BRIDGE_01/02) | Not recovered in top-10K — cross-component edges have shortest_path=∞, zero CN. Confirmed: topological features cannot detect cross-community bridge links |
| Mule recall (A00001→A00013) | Not recovered — mule fan-in is star topology; high-degree mule collector is structurally different from 2-hop prediction targets |

**Code:** `module5/link_prediction/` (5 files)

---

### Module 6 — Explainable Intelligence & Dashboard
**Status: Spec written, not implemented**
- Explainability requirement: every output ships with the specific subgraph/evidence responsible — never a bare number
- The explicit/inferred/predicted taxonomy (from Module 3 spec) governs all UI labels
- No dashboard code written yet

---

## Immediate Next Actions

1. **Composite risk score** — combine Tier 1 typology flags + OddBall + temporal + Module 4 centrality/community into one per-account score; note community_id adds noise for the structuring ring
2. **Fix temporal reweighting** in `module5/anomaly_detection/temporal.py` — reweight so `burst_tx_count` and `mean_gap_min` count more than `burst_ratio`; re-validate A00069-A00074 cluster together
3. **Cross-community bridge detection** — Tier 3 confirmed topology alone cannot detect bridge pairs; needs non-graph features (shared call timing, geolocation proximity) or a dedicated bridge-specific typology rule
4. **Node2Vec improvement path** — increase skip-gram epochs to 20+, tune p/q parameters for criminal networks; or switch to GCN/GraphSAGE if torch_geometric is installed
5. **Explainability wrapper** — every Module 5 output carries its evidence subgraph before Module 6 starts
6. **Team sync** — align on Modules 1, 2, 6 status; resolve the 5 cross-module conflicts from Section 4
