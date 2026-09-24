# End-to-End Input-to-Leads Investigative Pipeline

**SIH PS 189 · AI-Powered Criminal Network Discovery**  
*Governing Principle: "The system produces leads, not proof"* (Section 63 Bharatiya Sakshya Adhiniyam, 2023)

---

## 1. System Overview

Law enforcement agencies receive fragmented, multi-source raw inputs:
- Unstructured FIR complaints & field statements (in English, Hindi/Devanagari, and transliterated vernacular).
- Structured banking transaction streams (IMPS, UPI, NEFT, RTGS).
- Telecommunications CDR call logs (IMEI, cell towers, duration, caller/receiver).

The **Input-to-Leads Pipeline** transforms these raw inputs into court-admissible, tamper-evident **Investigative Leads** through five automated stages:

```
[RAW MULTI-SOURCE INPUT]
   │  • Sample 1: Cyber Fraud FIR (English + Devanagari suspect name, feeder accounts)
   │  • Sample 2: Banking Feed (Smurfing / Structuring under ₹50,000 PMLA threshold)
   │  • Sample 3: CDR Telecommunications Stream (48-hour pre-event coordination burst)
   │  • Sample 4: Scatter-Gather Layering Stream (Dispersion & rapid reconvergence)
   ▼
[STAGE 1: Ingestion & Text/Stream Extraction]
   │  • Multilingual NER, token parsing, amounts, account/phone identifiers
   ▼
[STAGE 2: Multilingual Entity Resolution & Stitching]
   │  • Resolves Devanagari (राहुल जोशी ➔ Rahul Joshi / P00231), initials (R. Joshi), OCR noise
   │  • Cross-domain KYC stitching: Account ➔ Person, Phone ➔ Subscriber
   ▼
[STAGE 3: Knowledge Graph Expansion & Tri-Partite Taxonomy]
   │  • Ingests into Criminal Knowledge Graph (CKG)
   │  • Enforces Tri-Partite taxonomy:
   │       - Explicit: Directly documented evidentiary links (Transacted, Called)
   │       - Inferred: Cross-domain derived ties (Co-occurrence, shared devices)
   │       - Predicted: ML-forecasted conspirator connections
   ▼
[STAGE 4: Multi-Tier Network & Anomaly Detection]
   │  • Tier 1: Typology Detectors (Mule Fan-In, Structuring, Scatter-Gather)
   │  • Tier 2: OddBall Structural Anomaly (Star hubs vs near-cliques)
   │  • Tier 3: Temporal Spatiotemporal Burst Analyzer (Rolling Z-score spikes)
   │  • Tier 4: Link Prediction Engine (Topological proximity, Adamic-Adar)
   ▼
[STAGE 5: Court-Admissible Lead Synthesis & Section 63 BSA Certification]
      • Prioritized Lead Dossiers (CRITICAL / HIGH / MEDIUM)
      • Primary Identified Suspect & Resolved Aliases
      • Extracted Evidence Subgraph (Exact nodes, edges, transaction amounts)
      • Statutory Action Items (Section 102 CrPC freeze, Section 91 CrPC notices)
      • SHA-256 Digital Custody Hash for courtroom admissibility
```

---

## 2. CLI Execution Instructions

Run the pipeline using the command line interface:

### Run with Built-In Benchmark Samples:
```bash
# 1. Cyber Crime FIR (Mule Hub Syndicate)
python3 pipeline/run_pipeline.py --sample fir

# 2. Bank Smurfing Stream (Evading ₹50,000 regulatory ceiling)
python3 pipeline/run_pipeline.py --sample structuring

# 3. CDR Telecommunications Stream (48h Pre-Event Burst)
python3 pipeline/run_pipeline.py --sample cdr

# 4. Scatter-Gather Transaction Flow
python3 pipeline/run_pipeline.py --sample scatter
```

### Run with Custom Raw File / Narrative:
```bash
python3 pipeline/run_pipeline.py --input /path/to/complaint.txt --out pipeline/output_leads.json
```

---

## 3. Web Dashboard Integration

The complete pipeline is integrated into the deployed Web Dashboard:
- **Live Production URL**: [https://orion26-team.web.app](https://orion26-team.web.app)
- **Dedicated View**: **"Input-to-Leads Pipeline"** (Tab 1 in top navigation)
- **Features**:
  - Sample preset selector & custom input text area.
  - Interactive "Execute Full Pipeline" trigger with live animated step transitions.
  - Multilingual resolution indicator displaying real-time alias stitching.
  - Lead dossiers with threat badges, evidence subgraph counters, and statutory action items.
  - **"Inspect in Graph Studio"** button: instantly renders the lead's evidence subgraph in the D3 Force-Directed visualizer.
  - **"Export BSA Certificate"** button: generates a court-ready Section 63 BSA legal certificate.

---

## 4. Legal Compliance & Section 63 BSA

Every output lead includes:
1. **Governing Legal Principle**:
   > *"LEADS, NOT PROOF: This automated output is an investigative intelligence lead generated under Section 63 of the Bharatiya Sakshya Adhiniyam (BSA), 2023. It assists human investigators in identifying suspicious patterns, freezing proceeds of crime, and issuing statutory notices. It does not constitute conclusive legal evidence of guilt without independent corroboration."*
2. **Statutory Action Items**:
   - Immediate lien/freeze requests under Section 102 Cr.P.C.
   - Statutory notices under Section 91 Cr.P.C. for bank KYC, IP logs, and telecom tower dumps.
   - Central Equipment Identity Register (CEIR) queries for cloned IMEI hardware.
3. **Cryptographic Custody Seal**:
   - SHA-256 tamper-evident hash calculated across the extracted evidence and suspect parameters.
