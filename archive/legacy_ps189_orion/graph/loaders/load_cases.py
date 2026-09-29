"""
graph/loaders/load_cases.py

Loads Case, Crime, and Event nodes, plus:
  - PART_OF_CASE  (Crime → Case)
  - OCCURRED_AT   (Crime → Location, Event → Location)
  - RELATES_TO    (Event → Case)
"""

from pathlib import Path

from loguru import logger

from graph.utils import load_csv, run_batches


# ─────────────────────────────────────────────────────────────────────────────
# Cases
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_CASE = """
UNWIND $batch AS row
MERGE (c:Case {case_id: row.case_id})
SET
  c.fir_number          = row.fir_number,
  c.case_type           = row.case_type,
  c.case_category       = row.case_category,
  c.registration_date   = row.registration_date,
  c.incident_date       = row.incident_date,
  c.police_station      = row.police_station,
  c.jurisdiction        = row.jurisdiction,
  c.case_status         = row.case_status,
  c.investigating_unit  = row.investigating_unit,
  c.source_document_id  = row.source_document_id,
  c.confidence_score    = toFloat(row.confidence_score),
  c.created_at          = row.created_at,
  c.updated_at          = row.updated_at
"""

_CASE_AT_LOCATION = """
UNWIND $batch AS row
MATCH (c:Case     {case_id:     row.case_id})
MATCH (l:Location {location_id: row.incident_location_id})
MERGE (c)-[:OCCURRED_AT]->(l)
"""


def load_cases(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "CASES_EVENTS" / "cases.csv")
    total = run_batches(driver, df, _MERGE_CASE, "Cases (nodes)")

    located = df[df["incident_location_id"].notna()].copy()
    run_batches(driver, located, _CASE_AT_LOCATION, "OCCURRED_AT (case→location)")
    return total


# ─────────────────────────────────────────────────────────────────────────────
# Crimes
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_CRIME = """
UNWIND $batch AS row
MERGE (cr:Crime {crime_id: row.crime_id})
SET
  cr.case_id           = row.case_id,
  cr.crime_type        = row.crime_type,
  cr.crime_category    = row.crime_category,
  cr.description       = row.description,
  cr.event_date        = row.event_date,
  cr.event_time        = row.event_time,
  cr.severity_level    = row.severity_level,
  cr.modus_operandi    = row.modus_operandi,
  cr.status            = row.status,
  cr.source_document_id= row.source_document_id,
  cr.confidence_score  = toFloat(row.confidence_score),
  cr.created_at        = row.created_at,
  cr.updated_at        = row.updated_at
"""

_CRIME_PART_OF_CASE = """
UNWIND $batch AS row
MATCH (cr:Crime {crime_id: row.crime_id})
MATCH (c:Case   {case_id:  row.case_id})
MERGE (cr)-[:PART_OF_CASE]->(c)
"""

_CRIME_AT_LOCATION = """
UNWIND $batch AS row
MATCH (cr:Crime   {crime_id:   row.crime_id})
MATCH (l:Location {location_id: row.location_id})
MERGE (cr)-[:OCCURRED_AT]->(l)
"""


def load_crimes(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "CASES_EVENTS" / "crimes.csv")
    total = run_batches(driver, df, _MERGE_CRIME, "Crimes (nodes)")

    run_batches(driver, df[df["case_id"].notna()].copy(), _CRIME_PART_OF_CASE, "PART_OF_CASE")
    run_batches(driver, df[df["location_id"].notna()].copy(), _CRIME_AT_LOCATION, "OCCURRED_AT (crime→loc)")
    return total


# ─────────────────────────────────────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_EVENT = """
UNWIND $batch AS row
MERGE (e:Event {event_id: row.event_id})
SET
  e.event_type         = row.event_type,
  e.event_name         = row.event_name,
  e.description        = row.description,
  e.start_timestamp    = row.start_timestamp,
  e.end_timestamp      = row.end_timestamp,
  e.primary_entity_type= row.primary_entity_type,
  e.primary_entity_id  = row.primary_entity_id,
  e.source_id          = row.source_id,
  e.evidence_id        = row.evidence_id,
  e.confidence_score   = toFloat(row.confidence_score),
  e.created_at         = row.created_at
"""

_EVENT_AT_LOCATION = """
UNWIND $batch AS row
MATCH (e:Event    {event_id:   row.event_id})
MATCH (l:Location {location_id: row.location_id})
MERGE (e)-[:OCCURRED_AT]->(l)
"""

_EVENT_RELATES_CASE = """
UNWIND $batch AS row
MATCH (e:Event {event_id: row.event_id})
MATCH (c:Case  {case_id:  row.case_id})
MERGE (e)-[:RELATES_TO]->(c)
"""


def load_events(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "CASES_EVENTS" / "events.csv")
    total = run_batches(driver, df, _MERGE_EVENT, "Events (nodes)")

    run_batches(driver, df[df["location_id"].notna()].copy(), _EVENT_AT_LOCATION, "OCCURRED_AT (event→loc)")
    run_batches(driver, df[df["case_id"].notna()].copy(), _EVENT_RELATES_CASE, "RELATES_TO (event→case)")
    return total


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def load_all_cases(driver, dataset_root: Path) -> dict:
    logger.info("=== Loading Case / Crime / Event Nodes ===")
    return {
        "cases":  load_cases(driver, dataset_root),
        "crimes": load_crimes(driver, dataset_root),
        "events": load_events(driver, dataset_root),
    }
