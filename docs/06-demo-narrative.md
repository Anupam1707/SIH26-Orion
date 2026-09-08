# Demo Narrative & Judge Q&A

## Target Demo Flow

> New FIR uploaded → entities extracted → aliases resolved (`Mohd. Arif` = `मोहम्मद आरिफ`)
> → graph updates live → community appears → mule cluster alert fires, explained with its
> source subgraph → investigator traces every edge back to its originating document.

---

## Headline Demo Sequence (Module 5)

1. **Show the mule fan-in alert:** 12 accounts converge on A00013 within 30 hours → A00013 forwards 161,025 to A00014. Rule-based, fully explainable, zero ML.
2. **Show OddBall finding scatter without being told:** A00055 surfaces at rank 6/532 (top 1.1%) from pure structure — no rule, no label. This is the unsupervised win.
3. **Show the structural connection between the two:** run `shortestPath(P00231, P02240)` — length-5 path directly links mule collector and scatter source through two pass-through accounts. *Immediately clarify: timestamps are non-chronological — this is topological evidence, not a money trail.*
4. **Show the structuring ring:** 6 accounts, 10 transactions each, hourly intervals, single day, all in the 9k-9.9k band. Scatter source A00069 likely seeds it.
5. **Show honest limitations:** Louvain sees these 6 as separate communities. OddBall misses them entirely. This is why the three-tier approach exists.

---

## Prepared Judge Q&A

| Question | Answer |
|----------|--------|
| "What's your ground truth?" | `GROUND_TRUTH.csv` specifies 8 planted typologies. Module 5 found 7/9 correctly (2 honest negatives). Tier 3 will additionally be tested against a real published covert network (Caviar or Noordin Top). |
| "Isn't this guilt by association?" | No — the explicit/inferred/predicted taxonomy (enforced at the graph layer) ensures predicted connections are always labeled "potential connection requiring verification." The system produces leads, not proof. |
| "How would a criminal evade this?" | OddBall is blind to temporal fraud — proved empirically (A00069, a structuring account, ranks dead-last). A launderer who blends in normal background activity currently scores *less* suspicious under the temporal metric. Stated openly, not hidden. A k-hop GNN also can't see a k+1-hop laundering chain. |
| "Why trust your centrality rankings?" | We don't, unconditionally. Module 4's robustness experiment: removing just 10% of network nodes changed 65% of the top-20 PageRank list. Reported as a limitation, not hidden. This is why no single number is treated as ground truth. |
| "Why should we believe one algorithm works?" | We don't use one. Phase 1 rules catch mule fan-in and structuring directly. OddBall catches scatter (top 1.1%) but misses structuring. Temporal scoring catches scatter (rank 1/7) and partial structuring. Each catches what the others miss — proved empirically. |
| "Isn't a graph path the same as proof of a money trail?" | No — the A00013-A00055 path (length 5) directly connects two headline typologies, but its own transaction timestamps run out of chronological order. `shortestPath()` proves topological reachability, not that money flowed in that direction. Exactly the failure mode the explicit/inferred/predicted taxonomy was designed to prevent. |
| "Your dataset is synthetic — how do we know it generalizes?" | Tier 3 link prediction will be tested against the Caviar or Noordin Top real covert network dataset. Honest baselines (Adamic-Adar / RA / Katz) are measured first; GNN is added only if it demonstrably beats them. |

---

## Definition of Done Per Module

| Module | Done When |
|--------|-----------|
| 1 | Reload from scratch in one command; validation report passes clean |
| 2 | Precision/recall reported on hard entity-resolution cases (Devanagari, transliteration, OCR, same-name-different-person) |
| 3 | Every edge traceable to a source document in one query; ontology validated at ingest |
| 4 | Centrality/community done and validated; shortest path done with non-chronological caveat documented; robustness plot exists |
| 5 | All 8 typologies fire correctly; unsupervised detection validated; link prediction built and honestly benchmarked; every output explainable |
| 6 | Full demo narrative runs end-to-end without touching a terminal |
