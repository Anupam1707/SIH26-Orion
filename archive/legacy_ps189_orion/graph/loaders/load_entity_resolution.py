"""
graph/loaders/load_entity_resolution.py

Loads entity-resolution artefacts:

  - Alias nodes  (aliases.csv)
    Connected to their canonical entity via :ALIAS_OF edge.

  - Resolution edges  (entity_resolution.csv)
    SAME_ENTITY      → SAME_ENTITY relationship between two records
    DIFFERENT_ENTITY → DIFFERENT_ENTITY relationship (negative signal)
    UNCERTAIN        → UNCERTAIN_ENTITY relationship
"""

from pathlib import Path

from loguru import logger

from graph.utils import load_csv, run_batches

# Entity type → (label, id_property)  — reuse the same map as relationships loader
_ENTITY_MAP = {
    "PERSON":       ("Person",       "person_id"),
    "ORGANIZATION": ("Organization", "organization_id"),
    "LOCATION":     ("Location",     "location_id"),
    "VEHICLE":      ("Vehicle",      "vehicle_id"),
    "PHONE":        ("PhoneNumber",  "phone_id"),
    "ACCOUNT":      ("Account",      "account_id"),
    "CASE":         ("Case",         "case_id"),
    "CRIME":        ("Crime",        "crime_id"),
    "EVENT":        ("Event",        "event_id"),
    "ALIAS":        ("Alias",        "alias_id"),
}


# ─────────────────────────────────────────────────────────────────────────────
# Alias nodes  +  ALIAS_OF edges
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_ALIAS = """
UNWIND $batch AS row
MERGE (a:Alias {alias_id: row.alias_id})
SET
  a.entity_type      = row.entity_type,
  a.entity_id        = row.entity_id,
  a.alias_value      = row.alias_value,
  a.alias_type       = row.alias_type,
  a.source_id        = row.source_id,
  a.confidence_score = toFloat(row.confidence_score),
  a.created_at       = row.created_at
"""

_ALIAS_OF_PERSON = """
UNWIND $batch AS row
MATCH (a:Alias  {alias_id:  row.alias_id})
MATCH (p:Person {person_id: row.entity_id})
MERGE (a)-[:ALIAS_OF {confidence_score: toFloat(row.confidence_score)}]->(p)
"""

_ALIAS_OF_ORG = """
UNWIND $batch AS row
MATCH (a:Alias        {alias_id:        row.alias_id})
MATCH (o:Organization {organization_id: row.entity_id})
MERGE (a)-[:ALIAS_OF {confidence_score: toFloat(row.confidence_score)}]->(o)
"""

_ALIAS_OF_LOCATION = """
UNWIND $batch AS row
MATCH (a:Alias    {alias_id:    row.alias_id})
MATCH (l:Location {location_id: row.entity_id})
MERGE (a)-[:ALIAS_OF {confidence_score: toFloat(row.confidence_score)}]->(l)
"""


def load_aliases(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "ENTITY_RESOLUTION" / "aliases.csv")
    total = run_batches(driver, df, _MERGE_ALIAS, "Aliases (nodes)")

    for entity_type, cypher in [
        ("PERSON",       _ALIAS_OF_PERSON),
        ("ORGANIZATION", _ALIAS_OF_ORG),
        ("LOCATION",     _ALIAS_OF_LOCATION),
    ]:
        subset = df[df["entity_type"] == entity_type].copy()
        if not subset.empty:
            run_batches(driver, subset, cypher, f"ALIAS_OF ({entity_type})")

    return total


# ─────────────────────────────────────────────────────────────────────────────
# Resolution edges  (SAME_ENTITY / DIFFERENT_ENTITY / UNCERTAIN_ENTITY)
# ─────────────────────────────────────────────────────────────────────────────

_RESOLUTION_TEMPLATE = """
UNWIND $batch AS row
MATCH (n1:{label1} {{{id1}: row.record_1_id}})
MATCH (n2:{label2} {{{id2}: row.record_2_id}})
MERGE (n1)-[r:{rel_type} {{resolution_id: row.resolution_id}}]->(n2)
SET
  r.similarity_score   = toFloat(row.similarity_score),
  r.matching_features  = row.matching_features,
  r.resolution_method  = row.resolution_method,
  r.confidence_score   = toFloat(row.confidence_score),
  r.verified           = toBoolean(row.verified),
  r.created_at         = row.created_at
"""

_RESULT_TO_REL = {
    "SAME_ENTITY":      "SAME_ENTITY",
    "DIFFERENT_ENTITY": "DIFFERENT_ENTITY",
    "UNCERTAIN":        "UNCERTAIN_ENTITY",
}


def load_entity_resolution(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "ENTITY_RESOLUTION" / "entity_resolution.csv")
    total = 0

    for result_val, rel_type in _RESULT_TO_REL.items():
        subset = df[df["resolution_result"] == result_val].copy()
        if subset.empty:
            continue

        # Group by type pair so we can build concrete Cypher
        for (t1, t2), group in subset.groupby(["record_1_type", "record_2_type"]):
            info1 = _ENTITY_MAP.get(t1.upper())
            info2 = _ENTITY_MAP.get(t2.upper())
            if not info1 or not info2:
                logger.warning(f"Skipping unknown type pair in resolution: {t1}→{t2}")
                continue
            label1, id1 = info1
            label2, id2 = info2
            cypher = _RESOLUTION_TEMPLATE.format(
                label1=label1, id1=id1,
                label2=label2, id2=id2,
                rel_type=rel_type,
            )
            written = run_batches(
                driver, group, cypher,
                desc=f"{rel_type} ({t1}→{t2})",
            )
            total += written

    return total


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def load_all_entity_resolution(driver, dataset_root: Path) -> dict:
    logger.info("=== Loading Entity Resolution Artefacts ===")
    return {
        "aliases":    load_aliases(driver, dataset_root),
        "resolution": load_entity_resolution(driver, dataset_root),
    }
