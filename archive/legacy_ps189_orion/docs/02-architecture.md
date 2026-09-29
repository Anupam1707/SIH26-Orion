# Architecture & Design Decisions

## Six-Module Breakdown

| # | Module | Core Question | Owner |
|---|--------|---------------|-------|
| 1 | Data Collection & Preprocessing | Collect, clean, normalize, structure multi-source data | TBD |
| 2 | NLP & Entity Resolution | Extract entities; determine which records refer to the same person | TBD |
| 3 | Criminal Knowledge Graph | Build the interconnected graph — nodes, edges, evidence, provenance | TBD |
| 4 | Graph Analytics & Network Detection | Find important people, find groups, trace connections | TBD |
| 5 | AI-Based Anomaly & Link Prediction | Predict missing links; detect suspicious patterns | You |
| 6 | Explainable Intelligence & Dashboard | Turn analysis into investigator-facing interface | Complete (Live at [https://orion26-team.web.app](https://orion26-team.web.app)) |

---

## Governing Principle

**The system produces leads, not proof.** Every output — a predicted link, an anomaly score, a centrality ranking — is a suggestion for human investigator review, never an accusation. This framing is both ethically necessary and the correct answer to the hardest judge question.

---

## Relationship Taxonomy (the best single design decision in the project)

Every relationship in the graph is exactly one of:

| Category | Meaning | UI label |
|----------|---------|----------|
| **Explicit** | Directly stated in a source document | Shown as stated fact |
| **Inferred** | Derived from explicit relationships by logic | "Inferred — [reason]" |
| **Predicted** | Output of an ML model | "Potential connection requiring verification" |

These are mutually exclusive. Never ambiguously more than one. The A00013-A00055 shortest path is a real example of why this matters — it is a topological path (structural connection, Inferred), not a money trail (Explicit).

---

## Module 5 Architecture — Three Tiers, Deliberate Order

> Published benchmarks (BOND, GADBench) found simple methods frequently beat specialised graph neural networks. Simple methods are the baseline; complexity added only where justified.

```
Tier 1 — Rule-based typology matching
  No ML. No training data. Fully explainable. Establishes ground truth for Tier 2 validation.

Tier 2a — OddBall structural anomaly (Akoglu et al. 2010)
  Unsupervised. Catches shape-based anomalies (stars = mule-like, cliques = fraud-cell-like).
  Does NOT catch temporal fraud — proved empirically, not assumed.

Tier 2b — Temporal burst window scoring
  Fills the exact gap Tier 2a left. 48h sliding window, z-scored composite.

Tier 3 — Link prediction (Random Forest selected, GNN gated out)
  Random Forest wins on AUC (0.528 Fin / 0.561 Comm).
  Intra-syndicate precision: 196/200.
```

---

## Cross-Module Contracts (resolved in Module 6 Implementation)

| Conflict | Resolution |
|----------|------------|
| Modules 2 and 3 both claimed entity resolution | Module 2 owns entity resolution outright |
| Module 3 claimed Module 4/5 analytics as its scope | Module 3 exposes this to Modules 4 and 5 |
| Confidence scores across modules | Unified into calibrated 0–100% confidence indices across all cards |
| Verification-status vocabulary | Unified as `VERIFIED_LEAD` vs `REVIEW_REQUIRED` with analyst interactive toggle |
| Module 4 prescribed GNN for Module 5 link prediction | Heuristics/RF beaten GNN; Random Forest deployed per empirical AUC gate |

---

## Module 4 Data Handoff to Module 5

Module 4 writes the following properties back to Aura. Module 5 reads them directly via Cypher:

| Property | Node label | Set by |
|----------|------------|--------|
| `pagerank_score` | PhoneNumber, Account | `graph/analytics/run_pagerank.py` |
| `betweenness_score` | PhoneNumber | `graph/analytics/run_pagerank.py` |
| `community_id` | Any (Louvain) | Module 4 GDS run |

**Known limitation:** `community_id` fragments the structuring ring (A00069-74) across 6 different communities. Using it as a signal in the composite risk score will add noise for this typology specifically.
