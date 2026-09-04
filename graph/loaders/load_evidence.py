"""
graph/loaders/load_evidence.py

Loads provenance / intelligence nodes:
  - Source        (sources.csv)
  - Evidence      (evidence.csv)
  - Document      (documents.csv)
  - Observation   (observations.csv  → stored as :Evidence with label Observation)

Edges:
  - SOURCED_FROM  (Evidence → Source)
  - REFERENCES    (Evidence → Document)
"""

from pathlib import Path

from loguru import logger

from graph.utils import load_csv, run_batches


# ─────────────────────────────────────────────────────────────────────────────
# Sources
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_SOURCE = """
UNWIND $batch AS row
MERGE (s:Source {source_id: row.source_id})
SET
  s.source_name        = row.source_name,
  s.source_type        = row.source_type,
  s.reliability_rating = row.reliability_rating,
  s.jurisdiction       = row.jurisdiction,
  s.contact_info       = row.contact_info,
  s.created_at         = row.created_at,
  s.updated_at         = row.updated_at
"""


def load_sources(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "EVIDENCE" / "sources.csv")
    return run_batches(driver, df, _MERGE_SOURCE, "Sources")


# ─────────────────────────────────────────────────────────────────────────────
# Documents
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_DOCUMENT = """
UNWIND $batch AS row
MERGE (d:Document {document_id: row.document_id})
SET
  d.document_type      = row.document_type,
  d.title              = row.title,
  d.content_summary    = row.content_summary,
  d.language           = row.language,
  d.date_created       = row.date_created,
  d.date_received      = row.date_received,
  d.source_id          = row.source_id,
  d.classification     = row.classification,
  d.confidence_score   = toFloat(row.confidence_score),
  d.created_at         = row.created_at,
  d.updated_at         = row.updated_at
"""


def load_documents(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "UNSTRUCTURED" / "documents.csv")
    return run_batches(driver, df, _MERGE_DOCUMENT, "Documents")


# ─────────────────────────────────────────────────────────────────────────────
# Evidence
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_EVIDENCE = """
UNWIND $batch AS row
MERGE (ev:Evidence {evidence_id: row.evidence_id})
SET
  ev.evidence_type       = row.evidence_type,
  ev.description         = row.description,
  ev.collection_date     = row.collection_date,
  ev.collected_by        = row.collected_by,
  ev.chain_of_custody    = row.chain_of_custody,
  ev.verification_status = row.verification_status,
  ev.source_id           = row.source_id,
  ev.confidence_score    = toFloat(row.confidence_score),
  ev.created_at          = row.created_at,
  ev.updated_at          = row.updated_at
"""

_EVIDENCE_FROM_SOURCE = """
UNWIND $batch AS row
MATCH (ev:Evidence {evidence_id: row.evidence_id})
MATCH (s:Source    {source_id:   row.source_id})
MERGE (ev)-[:SOURCED_FROM]->(s)
"""

_EVIDENCE_REF_DOCUMENT = """
UNWIND $batch AS row
MATCH (ev:Evidence {evidence_id: row.evidence_id})
MATCH (d:Document  {document_id: row.document_id})
MERGE (ev)-[:REFERENCES]->(d)
"""


def load_evidence(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "EVIDENCE" / "evidence.csv")
    total = run_batches(driver, df, _MERGE_EVIDENCE, "Evidence (nodes)")

    run_batches(driver, df[df["source_id"].notna()].copy(), _EVIDENCE_FROM_SOURCE, "SOURCED_FROM")
    if "document_id" in df.columns:
        run_batches(driver, df[df["document_id"].notna()].copy(), _EVIDENCE_REF_DOCUMENT, "REFERENCES")
    return total


# ─────────────────────────────────────────────────────────────────────────────
# Observations  (stored as Evidence nodes with :Observation secondary label)
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_OBSERVATION = """
UNWIND $batch AS row
MERGE (ev:Evidence {evidence_id: row.evidence_id})
SET
  ev:Observation,
  ev.observation_type  = row.observation_type,
  ev.description       = row.description,
  ev.observed_at       = row.observed_at,
  ev.observed_by       = row.observed_by,
  ev.location_id       = row.location_id,
  ev.subject_entity_type = row.subject_entity_type,
  ev.subject_entity_id   = row.subject_entity_id,
  ev.source_id         = row.source_id,
  ev.confidence_score  = toFloat(row.confidence_score),
  ev.created_at        = row.created_at
"""


def load_observations(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "UNSTRUCTURED" / "observations.csv")
    return run_batches(driver, df, _MERGE_OBSERVATION, "Observations")


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def load_all_evidence(driver, dataset_root: Path) -> dict:
    logger.info("=== Loading Evidence / Provenance Nodes ===")
    return {
        "sources":      load_sources(driver, dataset_root),
        "documents":    load_documents(driver, dataset_root),
        "evidence":     load_evidence(driver, dataset_root),
        "observations": load_observations(driver, dataset_root),
    }
