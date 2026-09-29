# Governance, Ethics & Legal Grounding

## Governing Principle

**The system produces leads, not proof.**

Every output — a predicted link, an anomaly score, a centrality ranking — is a suggestion
for human investigator review, never an accusation. This framing is both ethically
necessary and the correct answer to the hardest judge question.

---

## Legal Framework (India-specific)

| Framework | Relevance |
|-----------|-----------|
| CCTNS / ICJS | Authorized crime data infrastructure — the intended source systems |
| I4C (Indian Cybercrime Coordination Centre) | Problem statement origin; the sponsoring authority |
| Bhartiya Sakshya Adhiniyam (BSA) s.63 | Electronic records admissibility — evidence must be traceable to source |
| DPDP Act 2023 | Personal data processing — purpose limitation, access control, data minimization |

---

## Explicit / Inferred / Predicted Taxonomy

Every relationship in the knowledge graph is exactly one of these. Never ambiguously more than one.

| Category | Source | UI label |
|----------|--------|----------|
| **Explicit** | Directly stated in a source document | Shown as stated fact |
| **Inferred** | Derived from explicit relationships by logic | "Inferred — [reason]" |
| **Predicted** | Output of an ML model | "Potential connection requiring verification" |

This taxonomy is enforced at the graph layer (Module 3) and must be respected by Module 6's UI.

**Concrete example:** the A00013-A00055 shortest path is **Inferred** (topological connection
derived from the graph structure), not Explicit — because its own hop timestamps are
non-chronological. It cannot be labeled as a reconstructed money trail.

---

## Predictive Policing Feedback Loop Risk

**Risk:** if the system's outputs influence which areas/people get more surveillance, and
that surveillance generates more data about those areas/people, the model's training data
becomes self-reinforcing — not more accurate, just more concentrated.

**Mitigation built into Module 5 design:**
- All anomaly scores are *relative to the current dataset* — never projected as absolute risk
- Every output carries its evidence subgraph, so investigators can assess whether the signal
  is real or an artifact of surveillance concentration
- The three-tier approach (rules → OddBall → temporal) means each alert has a specific,
  human-readable explanation rather than an opaque score

---

## Data Governance Checklist

- [x] Source-level authorization documented (CCTNS/ICJS framework)
- [x] Explicit/inferred/predicted taxonomy defined and enforced
- [x] Every edge traceable to a source document in one query (Module 3)
- [x] Ontology enforced at ingest (`ONTOLOGY.csv`)
- [ ] PII handling policy for Module 6 dashboard (not written yet)
- [ ] Data retention and deletion policy (not written yet)
- [ ] Chain-of-custody requirements for evidence output (not written yet)
- [ ] Role-based access control for Module 6 (not designed yet)

---

## Synthetic Data Circularity

**Risk:** if the ML model (Tier 3 link prediction) is trained and evaluated on the same
synthetic dataset used to design it, evaluation metrics are meaningless — the model is
fitting the data generation process, not learning real criminal network structure.

**Mitigation:**
- Tier 1 and Tier 2 are validated against `GROUND_TRUTH.csv` (honest positive/negative/ambiguous findings documented, not forced to fit)
- Tier 3 plan: heuristic baselines evaluated on held-out real edges; additionally test against a real published covert network (Caviar or Noordin Top) for external validity
