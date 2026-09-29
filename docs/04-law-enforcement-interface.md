# Module 04: Law Enforcement Interface
## Key Deliverable Component (c) — Technical Specification

---

## 1. Overview & Persona-Centric Design

The **Law Enforcement Interface** serves field investigators, cyber cell superintendents, and bank fraud officers. It provides an end-to-end investigative workbench:
- **Case View:** High-performance, directed Cytoscape graph visualization tracing stolen funds hop-by-hop.
- **Command Center:** Real-time KPI telemetry, incoming complaint feeds, and jurisdictional overview.
- **Evidence Documentation & Chain of Custody:** Structured dossiers formatted for legal compliance under Section 63 of the Bharatiya Sakshya Adhiniyam, 2023 (BSA).
- **Intervention Workbench:** Direct linkage to the min-cut Fund Blocking engine to execute rapid account freezes.

---

## 2. Command Center Overview

The Command Center provides a high-level operational overview:
- **KPI Metrics Strip:**
  - Active Complaints under investigation.
  - Total Traced Fraud Volume (in ₹ Lakhs/Crores).
  - High-Risk Identified Mule Accounts.
  - Active Cash-Out Alerts dispatched to field units.
- **Live Complaint Stream:**
  - Real-time ingestion feed from NCRP.
  - Displays Incident Timestamp, Reported Timestamp, Reporting District, Loss Amount, and Complaint Status.
  - One-click transition into the Case Investigation workbench.
- **Jurisdictional Mini-Map:**
  - Real-time district-level incident distribution without tile server requirements.

---

## 3. Case View & Interactive Graph Engine

### 3.1 Cytoscape Visual Architecture
The Case View renders money flows left-to-right using a specialized directed layout:
- **Victim Node:** Flagged distinctly with amber halo and initial complaint attribution.
- **Intermediary Mule Accounts:** Node size and color correspond to computed risk and inferred structural role (Layer-1 Mule, Collector Hub, Layer-2 Cash-Out Mule).
- **Edge Attributes:** Directed arrows labeled with transaction amounts in Indian currency notation (₹), transaction timestamps in IST, and payment rails (UPI, IMPS, NEFT).
- **Hop-by-Hop Animation:** An interactive "Play Trace" controller animates the progression of stolen funds across chronological hops, allowing investigators to visually grasp syndication speed.

### 3.2 Inferred Role Inference vs. Ground Truth
Crucially, the interface strictly separates **publicly inferred operational roles** from hidden scenario ground truth:
- Nodes display roles inferred strictly through detection rules (e.g., *Mule Fan-In Identified*, *Layering Transit*, *Structuring Node*).
- An investigator inspection panel displays exact triggering transactions, counterparties, and timestamps.
- Zero future records or hidden ground truth labels are ever rendered.

---

## 4. Evidence Documentation & Legal Admissibility

### 4.1 Section 63 Bharatiya Sakshya Adhiniyam, 2023 (BSA)
To ensure electronic evidence produced by MuleTrail is admissible in Indian courts during judicial prosecution:
- **Automated Audit Dossiers:** Each traced case generates an immutable transaction trail logging:
  - System identification and software version hash.
  - Cryptographic SHA-256 hash of ingested complaint records.
  - UTC & IST timestamps of extraction and analysis.
  - Verified bank account numbers, IFSC identifiers, and transaction reference numbers (UTR).
- **Inter-Agency Export:** Investigators can generate Section 63-compliant certificates for forwarding to judicial magistrates and bank nodal authorities.

### 4.2 Persona Switcher
The interface supports role-based views without cumbersome mock authentication:
- **I4C Central Officer:** National overview, multi-district coordination, strategy analytics.
- **State Cyber Cell Investigator:** Case trace, evidence extraction, patrol coordination.
- **Bank Nodal Officer:** Account freeze priorities, CFCFRMS coordination, fund recovery verification.
