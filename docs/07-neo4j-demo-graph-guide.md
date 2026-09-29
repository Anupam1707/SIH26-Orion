# Module 07: Neo4j Demo Graph & Visual Presentation Guide
## Problem Statement ID: 26184 — MuleTrail
### Ministry of Home Affairs | Indian Cybercrime Coordination Centre (I4C)

---

## 1. Overview of the Demo Graph

This demo graph models an organized financial cybercrime syndicate operating across the **Haryana / NCR corridor (Nuh, Gurugram, Palwal, Mathura, Faridabad)**. It serves as a visual and evidentiary showcase demonstrating the progression from initial vishing calls to ATM cash-out forecasting.

### Key Metrics:
- **Total Entities:** 39 Nodes
- **Total Relationships:** 50+ Directed Edges
- **Isolation Guarantee:** Every node and relationship is tagged with `{demo: true}`, ensuring zero pollution of production or baseline data.

```
DEMO TOPOLOGY OVERVIEW:

 [Caller K1] ──USES──> [SIM-A] ──REPLACED_BY (20h gap)──> [SIM-B]
                           │                                   │
                           ▼ CALLED                            ▼ CALLED
                [Victims V1 - V4]                     [Victims V5 - V8]
                           │                                   │
                           ▼ TRANSACTED                        ▼ TRANSACTED
                [Layer-1 Mules M1, M2]                [Layer-1 Mules M3, M4, M5]
                           │                                   │
                           ▼ TRANSACTED (Fan-In ~96%)          ▼ TRANSACTED (Fan-In ~96%)
                    [Collector C1]                      [Collector C2]
                           │                                   │
                           ▼ TRANSACTED (Layering)             ▼ TRANSACTED (Layering)
                    [L3 Mule M6]                       [L3 Mules M7, M8]
                     │        │                         │        │
         WITHDREW_AT │        │ PREDICTED_CASHOUT       │        │ Structuring (<₹10k)
                     ▼        ▼                         ▼        ▼
             [Past ATMs]  [PREDICTED ATM P1]     [Past ATMs]  [PREDICTED ATM P2]
             (A1, A2, A3) (Palwal-2, P=0.87)     (A5, A6)     (Faridabad-7, P=0.79)

                     [Normal Citizens N1 - N5] (Background noise)
```

---

## 2. Entity & Relationship Breakdown

| Category | Node Count | Labels & IDs | Operational Meaning |
|---|---|---|---|
| **Victims** | 8 | `:Victim` (`V1` to `V8`) | Citizens filing complaints on NCRP after experiencing financial cyber fraud. |
| **Layer-1 Mules** | 5 | `:Mule {layer: 1}` (`M1` to `M5`) | Immediate recipient accounts receiving initial victim fraud inflows. |
| **Collectors (L2)** | 2 | `:Collector {layer: 2}` (`C1`, `C2`) | Central aggregation hubs pooling funds from multiple L1 mules (Fan-in typology). |
| **Layer-3 Mules** | 3 | `:Mule {layer: 3}` (`M6`, `M7`, `M8`) | Terminal cash-out holding accounts preparing for physical withdrawal. |
| **Caller & SIMs** | 3 | `:Caller` (`K1`), `:SIM` (`SIM-A`, `SIM-B`) | Vishing perpetrator rotating burner SIM cards (`SIM-A` deactivated $\to$ `SIM-B`). |
| **Historical ATMs** | 6 | `:ATM` (`A1` to `A6`) | Physical cash points with past withdrawal records learned by ML models. |
| **Districts** | 5 | `:District` | Nuh, Gurugram, Palwal, Mathura, Faridabad. |
| **Predicted ATMs** | 2 | `:PredictedATM` (`P1`, `P2`) | **Key Deliverable (b):** Forecasted imminent withdrawal locations (Palwal-2, Faridabad-7). |
| **Citizens** | 5 | `:Citizen` (`N1` to `N5`) | Background legitimate civilian transfers (essential noise for anomaly detection). |

---

## 3. How to Load into Neo4j

### Option A: Using the Python Loader
Ensure `.env` contains your Neo4j connection details, then execute:
```bash
python3 scripts/load_neo4j_demo.py
```

### Option B: Direct Execution in Neo4j Browser / Aura
Open Neo4j Browser and run the queries from [`scripts/neo4j_demo_graph.cypher`](file:///Users/anupamkanoongo/Documents/Developer's%20Drive/SIH26/scripts/neo4j_demo_graph.cypher).

1. **Clear Old Demo Data:**
   ```cypher
   MATCH (n {demo: true}) DETACH DELETE n;
   ```
2. **Execute Creation Blocks:** Paste the entity and relationship blocks from `scripts/neo4j_demo_graph.cypher`.

---

## 4. Visual Styling Guide (For Presentation Slides & Screenshots)

In Neo4j Browser / Neo4j Bloom, configure label chips and relationship styles as follows:

### Node Labels Styling:
| Label | Color | Size | Display Caption |
|---|---|---|---|
| **Victim** | Blue (`#4C8EDA`) | Medium | `name` |
| **Mule** | Orange (`#F79767`) | Medium | `name` |
| **Collector** | Purple (`#8D6CAB`) | Medium | `name` |
| **Citizen** | Light Grey (`#D9D9D9`) | Small | `name` |
| **Caller** | Dark Red (`#8B0000`) | Medium | `name` |
| **SIM** | Yellow (`#FFD700`) | Small | `name` |
| **ATM** | Slate Grey (`#6C757D`) | Medium | `name` |
| **District** | Green (`#57C785`) | Small | `name` |
| **PredictedATM** | **Bright Crimson Red (`#FF2D55`)** | **Large (Emphasized)** | `name` |

### Relationship Styling:
- **`PREDICTED_CASHOUT`:** Color: **Red**, Width: **Thick / Bold**, Caption: `probability` or `window`.
- **`TRANSACTED`:** Color: **Teal / Slate**, Width: Proportional to amount, Caption: `amount`.
- **`WITHDREW_AT`:** Color: **Dark Slate**, Caption: `amount`.
- **`CALLED`:** Color: **Orange**, Caption: `ts`.

---

## 5. Visual Queries for Slides & Demos

### 5.1 Full Ecosystem Query (Showing Background Noise & Context)
```cypher
MATCH (n {demo: true})-[r]->(m)
RETURN n, r, m;
```
*Layout Tip:* Drag the main fraud chain linearly from left to right (`Victims` $\to$ `Mules` $\to$ `Collectors` $\to$ `L3 Mules` $\to$ `ATMs`), and position the `Citizen` accounts in a dedicated side-cluster to illustrate how the anomaly engine separates noise from criminal activity.

### 5.2 Clean Fraud-to-Prediction Chain (Recommended for Slide 2 / Key Architecture)
```cypher
MATCH p=(v:Victim)-[:TRANSACTED*1..4]->(m:Mule)-[:PREDICTED_CASHOUT]->(pa:PredictedATM)
RETURN p;
```
*Layout Tip:* This isolates strictly the active criminal path terminating at the predicted cash-out ATMs, creating a crystal-clear visual narrative for judges and evaluators.

### 5.3 Cash-Out Evasion & ATM Dispersion Query
```cypher
MATCH (m:Mule)-[w:WITHDREW_AT]->(a:ATM)-[:IN_DISTRICT]->(d:District)
OPTIONAL MATCH (m)-[p:PREDICTED_CASHOUT]->(pred:PredictedATM)
RETURN m, w, a, d, p, pred;
```
*Shows how the network historically hopped districts (Nuh $\to$ Gurugram $\to$ Palwal) and how the model caught the next hop in advance.*
