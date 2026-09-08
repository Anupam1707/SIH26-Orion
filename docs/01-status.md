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
**Status: PHASE 2 COMPLETE — Phase 3 not started**

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
**NOT STARTED**
- Plan: Adamic-Adar, Resource Allocation, Katz baselines first (measured against held-out real edges)
- SEAL (subgraph-based GNN) only if it demonstrably beats heuristics

---

### Module 6 — Explainable Intelligence & Dashboard
**Status: Spec written, not implemented**
- Explainability requirement: every output ships with the specific subgraph/evidence responsible — never a bare number
- The explicit/inferred/predicted taxonomy (from Module 3 spec) governs all UI labels
- No dashboard code written yet

---

## Immediate Next Actions

1. **Fix temporal reweighting** in `module5/anomaly_detection/temporal.py` — reweight so `burst_tx_count` and `mean_gap_min` count more than `burst_ratio`; re-validate A00069-A00074 cluster together
2. **Confirm A00069 receiver list** — check whether A00069 also scatters to A00071-74 (would confirm structuring ring has a single funding origin)
3. **Decide Event-linkage routing** for burner-swap and pre-event-burst typologies — dedicated phone-graph path, or cross-reference after the fact
4. **Composite risk score** — combine Phase 1 + OddBall + temporal + Module 4 centrality/community into one per-account score; note that community_id will add noise for the structuring ring (all 6 are in different communities)
5. **Tier 3 link prediction** — Adamic-Adar / RA / Katz baselines, evaluated with precision@K on held-out edges
6. **Explainability wrapper** — every Module 5 output carries its evidence subgraph before Module 6 starts
7. **Team sync** — align on Modules 1, 2, 6 status and resolve the 5 cross-module conflicts from Section 4 (confidence score definition, verification-status vocabulary, entity resolution ownership, scope boundary of Module 3 vs 4/5, feature supply for link prediction)
