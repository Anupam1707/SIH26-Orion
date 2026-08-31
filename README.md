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

## Next Phase

After research sign-off, this repository will move into:
- data schema design,
- proof-of-concept pipelines,
- baseline graph and NLP experiments,
- and incremental prototype development.

See `/home/runner/work/SIH26/SIH26/docs/README.md` for the full research documentation map.
