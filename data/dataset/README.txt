Synthetic Criminal Knowledge Graph Dataset — FINAL PART 4 INTEGRATION
Generated: 2026-09-03

All data are synthetic and intended only for competition/MVP prototyping.
No real persons, criminal records, phone numbers, bank accounts, or intelligence records are represented.

This archive preserves the team's original dataset and adds the complete Part 4 modules:
- UNSTRUCTURED/documents.csv
- UNSTRUCTURED/observations.csv
- EVIDENCE/evidence.csv
- EVIDENCE/sources.csv
- ENTITY_RESOLUTION/aliases.csv
- ENTITY_RESOLUTION/entity_resolution.csv

Existing structured/relation/case files are retained unchanged.

Part 4 row counts:
- documents.csv: 6,000
- observations.csv: 12,000
- evidence.csv: 25,000
- sources.csv: 50
- aliases.csv: 6,000
- entity_resolution.csv: 15,000

Existing dataset rows: 53,564
Final total CSV rows: 117,614

Important integration details:
1. Evidence IDs EV00001–EV05000 are preserved so references in the team's existing files resolve.
2. Existing case/crime source_document_id values (DOC00001–DOC03000 range) are represented in documents.csv.
3. Document evidence uses EV05001–EV11000.
4. Observation evidence uses EV11001–EV23000.
5. Supplementary analytical evidence uses EV23001–EV25000.
6. Entity-resolution aliases are synthetic variants of IDs/names already present in persons, organizations, locations, vehicles, phones and accounts.
7. entity_resolution.csv contains SAME_ENTITY, DIFFERENT_ENTITY and UNCERTAIN examples for model evaluation.
8. Documents intentionally contain entity mentions suitable for NER, relation extraction, temporal extraction and entity-resolution experiments.
9. Confidence and verification fields are included so AI outputs can be treated as analytical signals rather than facts.

Recommended first workflow:
Documents/observations → NLP/NER → alias/entity resolution → evidence/provenance → CKG nodes/edges → graph analytics.
