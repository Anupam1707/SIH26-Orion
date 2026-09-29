# Module 01: System Overview & Problem Statement Context
## Problem Statement ID: 26184
### Ministry of Home Affairs | Indian Cybercrime Coordination Centre (I4C)

---

## 1. Executive Context & National Challenge

The **National Cybercrime Reporting Portal (NCRP)** serves as the centralized digital backbone for cybercrime reporting across India. Operated under the aegis of the **Indian Cybercrime Coordination Centre (I4C), Ministry of Home Affairs (MHA)**, NCRP receives **upwards of 8,000 complaints daily**, a significant proportion of which relate to financial cyber frauds—including vishing, phishing, investment scams, task-based frauds, and instant loan app schemes.

Currently, financial fraud mitigation in India relies heavily on reactive interventions:
1. **Citizen Complaint Filing:** Victims report losses on NCRP or the 1930 Citizen Financial Cyber Fraud Helpline.
2. **Citizen Financial Cyber Fraud Reporting and Management System (CFCFRMS):** Law Enforcement Agencies (LEAs) and Banks/Financial Institutions (FIs) attempt to freeze transacted accounts hop-by-hop.
3. **The Velocity Gap:** Cyber syndicates operate automated networks of "mule accounts" that rapidly disperse stolen funds within minutes (layer-1 and layer-2 mules), culminating in swift cash withdrawals at Automated Teller Machines (ATMs) or micro-ATMs before formal freezing instructions can propagate through inter-bank clearing channels.

Once funds are withdrawn in cash, the trail goes dark, drastically reducing recovery rates and burdening LEAs with post-facto physical forensics.

---

## 2. The MuleTrail Paradigm: From Reactive to Proactive Defense

**MuleTrail** introduces a paradigm shift: **predicting likely cash-out locations in advance** to enable proactive intervention before the physical withdrawal occurs.

```
       REACTIVE PARADIGM (Conventional)
Victim Loss ──> Complaint (Hours later) ──> Hop-by-Hop Freezing (Delayed) ──> [Cash Out Already Done]

       PROACTIVE PARADIGM (MuleTrail Framework)
Victim Loss ──> Rapid Graph Trace ──> Typology Detection ──> Predictive AI/ML Forecast
                                                                   │
                       ┌───────────────────────────────────────────┴───────────────────────────────────────────┐
                       ▼                                                                                       ▼
           Proactive ATM Deployment                                                                 Min-Cut Account Freezing
   (LEAs deploy patrols / alert ATM nodal ops)                                             (CFCFRMS blocks chokepoints in minutes)
```

By synthesizing transaction graphs, historical cybercrime patterns, spatial ATM usage, and network behavior, MuleTrail forecasts:
- **Which ATMs** are at high risk of cash withdrawal.
- **In which time window** (2h, 6h, 24h) the withdrawal is expected.
- **Which mule accounts** act as critical bottlenecks where freezing yields the maximum fund recovery with minimal operational friction.

---

## 3. Mapping to Official Key Deliverables

| Deliverable Component | Description Mandate | MuleTrail Implementation |
|---|---|---|
| **a. Predictive Analytics Engine** | AI/ML-based system to analyze historical cybercrime and financial data to predict potential withdrawal hotspots. Features include pattern detection, geospatial risk modelling, and real-time alerts. | Multi-tier engine comprising: (1) Graph Tracing, (2) 5 Typology Detectors (Fan-in, Layering, Structuring, Scatter, Pass-through), (3) OddBall structural anomaly scoring, (4) Temporal burst metrics, and (5) Trio of cash-out models: Recency Baseline, Equirectangular KDE, and Graph-Aware XGBoost. |
| **b. Risk Heatmap Dashboard** | GIS-enabled dashboard visualizing real-time and potential risk zones with drill-down filters by time, location, and crime category etc. | Offline-capable GIS interface rendering district polygons, ATM coordinate layers, dynamic probability circles, 2h/6h/24h time-horizon filters, model switcher, and plain-language explanation cards. |
| **c. Law Enforcement Interface** | Secure interface for investigators to access alerts, intelligence reports, and evidence documentation. | Case View & Command Center featuring Cytoscape interactive graph visualization, chronological transaction playback, inferred role tagging, node evidence drawers, and Section 63 BSA compliance audit logging. |
| **d. Alert & Notification System** | Real-time notifications to law enforcements, banks, and I4C officers via SMS, email, API, or dashboard triggers. | Multi-channel dispatch hub generating high/medium/critical alerts with configurable thresholds, mock SMS/Email/API delivery logging, live notification bells, and investigator acknowledgement workflows. |

---

## 4. Key Architectural Tenets

1. **Zero Future Leakage:** In accordance with rigorous scientific standards, no model, feature extractor, or evaluation metric may access transaction or withdrawal timestamps past the active simulation clock ($t \le t_{\text{clock}}$).
2. **Offline-First Resilience:** Zero external CDN, tile server, or live internet dependencies. All district polygons, fonts, maps, and graph engines execute self-contained within local memory and local network perimeters.
3. **Actionable Explainability:** No bare black-box scores. Every prediction, anomaly score, and fund-freeze recommendation surfaces top-3 plain-language reasons and links directly to evidentiary source transactions.
4. **Section 63 BSA Integrity:** All electronic transaction traces, graph extractions, and model inferences maintain strict hash integrity conforming to Section 63 of the Bharatiya Sakshya Adhiniyam, 2023 (BSA).
