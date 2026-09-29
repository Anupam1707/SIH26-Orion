"""
graph/loaders/load_relationships.py

Loads all relationship-table edges:

  CALLED        communications.csv  : PhoneNumber → PhoneNumber
  MEMBER_OF     memberships.csv     : Person       → Organization
  MOVED_TO      movements.csv       : (Person/Vehicle/Org) → Location
  TRANSACTED    transactions.csv    : Account      → Account
  LINKED_TO     relationships.csv   : generic cross-type (catch-all)

Each edge carries evidence_id, source_id, confidence_score, and temporal
properties so provenance is always traceable.
"""

from pathlib import Path

from loguru import logger

from graph.utils import load_csv, run_batches


# ─────────────────────────────────────────────────────────────────────────────
# CALLED  (PhoneNumber → PhoneNumber)
# ─────────────────────────────────────────────────────────────────────────────

_CALLED = """
UNWIND $batch AS row
MATCH (src:PhoneNumber {phone_id: row.source_phone_id})
MATCH (tgt:PhoneNumber {phone_id: row.target_phone_id})
MERGE (src)-[r:CALLED {communication_id: row.communication_id}]->(tgt)
SET
  r.communication_type    = row.communication_type,
  r.timestamp             = row.timestamp,
  r.duration_seconds      = toInteger(row.duration_seconds),
  r.cell_tower_source     = row.cell_tower_source,
  r.cell_tower_target     = row.cell_tower_target,
  r.communication_direction = row.communication_direction,
  r.message_id_hash       = row.message_id_hash,
  r.source_id             = row.source_id,
  r.evidence_id           = row.evidence_id,
  r.confidence_score      = toFloat(row.confidence_score)
"""


def load_communications(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "RELATIONSHIPS" / "communications.csv")
    return run_batches(driver, df, _CALLED, "CALLED (communications)")


# ─────────────────────────────────────────────────────────────────────────────
# MEMBER_OF  (Person → Organization)
# ─────────────────────────────────────────────────────────────────────────────

_MEMBER_OF = """
UNWIND $batch AS row
MATCH (p:Person       {person_id:       row.person_id})
MATCH (o:Organization {organization_id: row.organization_id})
MERGE (p)-[r:MEMBER_OF {membership_id: row.membership_id}]->(o)
SET
  r.role              = row.role,
  r.membership_type   = row.membership_type,
  r.start_date        = row.start_date,
  r.end_date          = row.end_date,
  r.status            = row.status,
  r.source_id         = row.source_id,
  r.evidence_id       = row.evidence_id,
  r.confidence_score  = toFloat(row.confidence_score),
  r.created_at        = row.created_at,
  r.updated_at        = row.updated_at
"""


def load_memberships(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "RELATIONSHIPS" / "memberships.csv")
    return run_batches(driver, df, _MEMBER_OF, "MEMBER_OF (memberships)")


# ─────────────────────────────────────────────────────────────────────────────
# MOVED_TO  (Person | Vehicle | Organization → Location)
# Movements table has mixed entity_type; we handle each separately.
# ─────────────────────────────────────────────────────────────────────────────

_MOVED_TO_PERSON = """
UNWIND $batch AS row
MATCH (p:Person   {person_id:   row.entity_id})
MATCH (l:Location {location_id: row.location_id})
MERGE (p)-[r:MOVED_TO {movement_id: row.movement_id}]->(l)
SET
  r.arrival_timestamp   = row.arrival_timestamp,
  r.departure_timestamp = row.departure_timestamp,
  r.movement_type       = row.movement_type,
  r.vehicle_id          = row.vehicle_id,
  r.source_id           = row.source_id,
  r.evidence_id         = row.evidence_id,
  r.confidence_score    = toFloat(row.confidence_score)
"""

_MOVED_TO_VEHICLE = """
UNWIND $batch AS row
MATCH (v:Vehicle  {vehicle_id:  row.entity_id})
MATCH (l:Location {location_id: row.location_id})
MERGE (v)-[r:MOVED_TO {movement_id: row.movement_id}]->(l)
SET
  r.arrival_timestamp   = row.arrival_timestamp,
  r.departure_timestamp = row.departure_timestamp,
  r.movement_type       = row.movement_type,
  r.source_id           = row.source_id,
  r.evidence_id         = row.evidence_id,
  r.confidence_score    = toFloat(row.confidence_score)
"""

_MOVED_TO_ORG = """
UNWIND $batch AS row
MATCH (o:Organization {organization_id: row.entity_id})
MATCH (l:Location     {location_id:     row.location_id})
MERGE (o)-[r:MOVED_TO {movement_id: row.movement_id}]->(l)
SET
  r.arrival_timestamp   = row.arrival_timestamp,
  r.departure_timestamp = row.departure_timestamp,
  r.movement_type       = row.movement_type,
  r.vehicle_id          = row.vehicle_id,
  r.source_id           = row.source_id,
  r.evidence_id         = row.evidence_id,
  r.confidence_score    = toFloat(row.confidence_score)
"""


def load_movements(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "RELATIONSHIPS" / "movements.csv")

    persons = df[df["entity_type"] == "PERSON"].copy()
    vehicles = df[df["entity_type"] == "VEHICLE"].copy()
    orgs = df[df["entity_type"] == "ORGANIZATION"].copy()

    total = 0
    total += run_batches(driver, persons,  _MOVED_TO_PERSON,  "MOVED_TO (person)")
    total += run_batches(driver, vehicles, _MOVED_TO_VEHICLE, "MOVED_TO (vehicle)")
    total += run_batches(driver, orgs,     _MOVED_TO_ORG,     "MOVED_TO (org)")
    return total


# ─────────────────────────────────────────────────────────────────────────────
# TRANSACTED  (Account → Account)
# ─────────────────────────────────────────────────────────────────────────────

_TRANSACTED = """
UNWIND $batch AS row
MATCH (src:Account {account_id: row.source_account_id})
MATCH (tgt:Account {account_id: row.target_account_id})
MERGE (src)-[r:TRANSACTED {transaction_id: row.transaction_id}]->(tgt)
SET
  r.transaction_type           = row.transaction_type,
  r.amount                     = toFloat(row.amount),
  r.currency                   = row.currency,
  r.timestamp                  = row.timestamp,
  r.transaction_reference_hash = row.transaction_reference_hash,
  r.source_location_id         = row.source_location_id,
  r.destination_location_id    = row.destination_location_id,
  r.channel                    = row.channel,
  r.description                = row.description,
  r.source_id                  = row.source_id,
  r.evidence_id                = row.evidence_id,
  r.confidence_score           = toFloat(row.confidence_score)
"""


def load_transactions(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "RELATIONSHIPS" / "transactions.csv")
    return run_batches(driver, df, _TRANSACTED, "TRANSACTED (transactions)")


# ─────────────────────────────────────────────────────────────────────────────
# LINKED_TO  (generic cross-entity relationships)
# The relationships.csv uses free-form source/target entity types.
# We dynamically match by entity type via apoc-style approach or label routing.
# Since we can't use dynamic labels in Cypher without APOC, we group by
# (source_entity_type, target_entity_type) pair and run targeted queries.
# ─────────────────────────────────────────────────────────────────────────────

# Entity type → Neo4j label + ID property
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
}

_LINKED_TO_TEMPLATE = """
UNWIND $batch AS row
MATCH (src:{src_label} {{{src_id}: row.source_entity_id}})
MATCH (tgt:{tgt_label} {{{tgt_id}: row.target_entity_id}})
MERGE (src)-[r:LINKED_TO {{relationship_id: row.relationship_id}}]->(tgt)
SET
  r.relationship_type   = row.relationship_type,
  r.relationship_start  = row.relationship_start,
  r.relationship_end    = row.relationship_end,
  r.relationship_strength = toFloat(row.relationship_strength),
  r.relationship_status = row.relationship_status,
  r.is_explicit         = toBoolean(row.is_explicit),
  r.is_inferred         = toBoolean(row.is_inferred),
  r.is_predicted        = toBoolean(row.is_predicted),
  r.source_id           = row.source_id,
  r.evidence_id         = row.evidence_id,
  r.confidence_score    = toFloat(row.confidence_score),
  r.verification_status = row.verification_status
"""


def load_generic_relationships(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "RELATIONSHIPS" / "relationships.csv")
    total = 0

    pairs = df.groupby(["source_entity_type", "target_entity_type"])
    for (src_type, tgt_type), group in pairs:
        src_info = _ENTITY_MAP.get(src_type.upper())
        tgt_info = _ENTITY_MAP.get(tgt_type.upper())
        if not src_info or not tgt_info:
            logger.warning(f"Skipping unknown entity type pair: {src_type} → {tgt_type}")
            continue

        src_label, src_id = src_info
        tgt_label, tgt_id = tgt_info
        cypher = _LINKED_TO_TEMPLATE.format(
            src_label=src_label, src_id=src_id,
            tgt_label=tgt_label, tgt_id=tgt_id,
        )
        written = run_batches(
            driver, group,
            cypher,
            desc=f"LINKED_TO ({src_type}→{tgt_type})",
        )
        total += written

    return total


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def load_all_relationships(driver, dataset_root: Path) -> dict:
    logger.info("=== Loading Relationship Edges ===")
    return {
        "communications":    load_communications(driver, dataset_root),
        "memberships":       load_memberships(driver, dataset_root),
        "movements":         load_movements(driver, dataset_root),
        "transactions":      load_transactions(driver, dataset_root),
        "generic_relations": load_generic_relationships(driver, dataset_root),
    }
