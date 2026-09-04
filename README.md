# SIH26 — AI-Powered Criminal Network Analysis System

This repository is currently in the **research and planning phase**.

The focus right now is to define:
- problem understanding,
- module-wise scope,
- data and governance needs,
- research deliverables,
- and a clear execution roadmap (**without implementation code yet**).

## Problem Context

Modern criminal activity often operates as interconnected networks across people, phones, locations, vehicles, organizations, events, and financial channels. Investigators usually work with fragmented, multi-source records such as FIRs, CDRs, surveillance notes, transaction traces, intelligence reports, and social media inputs.

This project aims to convert that fragmented data into structured, explainable criminal network intelligence.

## Objective

Build an AI-powered system that can:
1. ingest and process multi-source crime/intelligence data,
2. extract and resolve entities,
3. build a criminal knowledge graph,
4. run graph analytics to identify hidden patterns and key actors,
5. detect anomalies and predict suspicious/missing links,
6. deliver explainable investigator-facing insights.

## Module Roadmap (Research Baseline)

| Part | Module | Primary Focus |
|---|---|---|
| 1 | Data Collection & Preprocessing | Collect, clean, normalize, and structure multi-source data |
| 2 | NLP & Entity Resolution | Extract entities and identify duplicate/same entities |
| 3 | Criminal Knowledge Graph | Build interconnected criminal intelligence graph |
| 4 | Graph Analytics & Network Detection | Find communities, key entities, and hidden relationships |
| 5 | AI-Based Anomaly & Link Prediction | Predict missing links and detect suspicious patterns |
| 6 | Explainable Intelligence & Investigator Dashboard | Convert analysis into actionable, explainable intelligence |

## Repository Structure (Current)

```text
SIH26/
├── README.md
└── docs/
    ├── README.md
    ├── 01-problem-overview.md
    ├── 02-module-roadmap.md
    ├── 03-data-sources-and-governance.md
    ├── 04-research-plan.md
    └── 05-system-blueprint.md
```

## Module 3 — Criminal Knowledge Graph (Neo4j)  ✅ Implemented

### Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure Neo4j connection
cp .env.example .env
# Edit .env → set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# 3. Run the full loader
python main_graph_loader.py

# 4. Verify the graph
python verify_graph.py
```

### Graph Schema
- **13 node labels**: Person, Location, Organization, Vehicle, PhoneNumber, Account, Case, Crime, Event, Evidence, Document, Source, Alias
- **15+ edge types**: CALLED, MEMBER_OF, MOVED_TO, TRANSACTED, LINKED_TO, OWNS_PHONE, OWNS_VEHICLE, HOLDS_ACCOUNT, PART_OF_CASE, OCCURRED_AT, RELATES_TO, SOURCED_FROM, REFERENCES, ALIAS_OF, SAME_ENTITY, DIFFERENT_ENTITY, UNCERTAIN_ENTITY

### Repository Structure
```text
SIH26/
├── graph/
│   ├── config.py                      ← Neo4j connection (.env)
│   ├── schema.py                      ← Constraints + indexes
│   ├── utils.py                       ← Batch UNWIND helpers
│   └── loaders/
│       ├── load_entities.py           ← Person, Location, Org, Vehicle, Phone, Account
│       ├── load_cases.py              ← Case, Crime, Event
│       ├── load_evidence.py           ← Evidence, Source, Document, Observation
│       ├── load_relationships.py      ← CALLED, MEMBER_OF, MOVED_TO, TRANSACTED, LINKED_TO
│       └── load_entity_resolution.py  ← Alias nodes + SAME_ENTITY edges
├── main_graph_loader.py               ← Full-load orchestrator
├── verify_graph.py                    ← Post-load sanity checks
├── requirements.txt
├── .env.example
└── data/dataset/                      ← 117 K-row synthetic dataset
```

## Module 4 — Graph Analytics (Centrality & Detection)  🚀 Active

### Run PageRank Analysis (Phone Communications Network)
```bash
# Run PageRank and display top 20 influential nodes (with owner resolution)
python run_pagerank.py --limit 20

# Run PageRank, export to CSV, and write scores back to Neo4j
python run_pagerank.py --limit 20 --write-back --export pagerank_top20.csv
```

Once written back, you can also query PageRank directly inside Neo4j Browser:
```cypher
MATCH (ph:PhoneNumber)
WHERE ph.pagerank_score IS NOT NULL
OPTIONAL MATCH (p:Person)-[:OWNS_PHONE]->(ph)
RETURN ph.phone_id AS phone, p.full_name AS subscriber, ph.pagerank_score AS score
ORDER BY score DESC
LIMIT 20;
```

## Next Phase
- Module 4: Louvain / Community detection, Betweenness centrality, Shortest path analysis
- Module 5: AI anomaly & link prediction
- Module 6: Investigator dashboard

See `docs/` for the full research documentation map.
