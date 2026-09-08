# Dataset — Audit, Repair & Known Gaps

Dataset location: `data/dataset/`
Ground truth: `data/dataset/GROUND_TRUTH.csv`
Validation report: `data/dataset/VALIDATION_REPORT.txt`
Ontology: `data/dataset/ONTOLOGY.csv`

---

## Dataset Scale

~55,250 nodes / ~90,938 relationships loaded into Neo4j Aura.

---

## Original Dataset — 22 Problems Found

The initial dataset was audited independently rather than trusted. Problems by severity:

### Critical
- No criminal patterns planted — transaction amounts uniform, no structuring/mule patterns
- Communication graph clustering coefficient 0.00011 (below random-graph expectation of 0.00093) — community detection had nothing real to find
- Entity resolution solvable by single threshold (0.88 → 99.05% accuracy) — no hard cases
- `relationships.csv` had semantically impossible triples (PHONE MEMBER_OF LOCATION, etc.)
- `is_explicit`/`is_inferred`/`is_predicted` were independent random booleans — 565 rows all three, 1,594 rows none
- 1,125 of 1,500 `events.csv` rows had type field not matching the entity ID it pointed to

### Major
- Embedded newlines silently inflating row counts in 3 files
- 41% of evidence collected *before* the event it documented
- 0% Devanagari text despite language labels claiming Hindi/Hinglish
- Only two alias patterns (exact copies and initials) — none of the transliteration/OCR/nickname variety required
- 45.8% of relationship end-dates in the future (some to 2029)
- `updated_at` preceding `created_at` in half of cases

### Moderate
- SMS/email records carrying 15-minute call durations
- 594/1,166 female-coded names labelled Male
- 810 invalid PIN codes
- Lorem ipsum in ~900 crime/event descriptions
- Flat (non-bursty) communication timing
- `matching_features` column perfectly correlated with its label (data leakage)

---

## Repair — What Changed

8 criminal patterns planted with time windows and account counts:

| Pattern | Accounts | Details |
|---------|----------|---------|
| Mule fan-in | A00001-A00013 | 12 feeders → A00013 (30h window) → A00014 (161,025 forwarded) |
| Scatter | A00055-A00063 | A00055 → 8 receivers, 5-min intervals. A00069 → A00070+ |
| Structuring | A00069-A00074 | 10 txns each, 9k-9.9k band, hourly, 2026-08-28 |
| Layering | A00043-A00053 | 2 chains: 200k→166k and 250k→207k, 92-98% decay/hop, <30min |
| Circular flow | planted | Detected with 7-day completion window |
| Burner rotation | PH00001-PH00002 | 3 shared contacts, 1-day gap |
| Community pattern | verified | 4 planted communities, Louvain modularity 0.53 |
| Pre-event burst | PH03685's owner | Note: P03685 has no LINKED_TO edge to any Event |

Also added: `ONTOLOGY.csv`, `GROUND_TRUTH.csv`, Devanagari aliases, OCR/transliteration hard cases.

---

## Independent Re-Verification of Repair

| Check | Claimed by report | Independently verified |
|-------|-------------------|----------------------|
| Ontology violations | 0 | Confirmed 0 — but 57% of relationships use ASSOCIATED_WITH catch-all |
| Flag conflicts | 0 | Confirmed 0 |
| Embedded newlines | Fixed | Confirmed |
| Communities | "3.14x random" | Actual Louvain: modularity 0.53, 4 communities at 100% purity |
| Entity resolution difficulty | Improved | Confirmed — accuracy 99.05% → ~84%, 18% ambiguous band |
| Female-name gender errors | 0 | **WRONG — 323/1,166 still wrong** (Ananya/Kavya/Meera/Pooja/Sneha not fixed) |
| Mule fan-in | Planted | Verified node-by-node: 12 accounts → A00013 → A00014 within 30h |

**Verdict:** genuine improvement, load-worthy. Two known gaps that don't block progress: the partial gender fix and the ASSOCIATED_WITH catch-all.

---

## What Was Already Correct (Before Repair)

- Referential integrity across all 15 FK relationships — perfect
- No duplicate primary keys
- All 25,000 evidence hashes unique
- 596 names shared by multiple people — useful as genuine entity-resolution hard cases once labeled
