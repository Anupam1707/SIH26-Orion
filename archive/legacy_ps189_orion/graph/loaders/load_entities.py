"""
graph/loaders/load_entities.py

Loads all six entity node types into Neo4j:
  - Person
  - Location
  - Organization
  - Vehicle
  - PhoneNumber  (+ OWNS_PHONE edges)
  - Account      (+ HOLDS_ACCOUNT edges)
  - Vehicle      (+ OWNS_VEHICLE edges)

All writes use MERGE (idempotent — safe to re-run).
"""

from pathlib import Path

from loguru import logger

from graph.utils import load_csv, run_batches


# ─────────────────────────────────────────────────────────────────────────────
# Persons
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_PERSON = """
UNWIND $batch AS row
MERGE (p:Person {person_id: row.person_id})
SET
  p.full_name        = row.full_name,
  p.alias            = row.alias,
  p.date_of_birth    = row.date_of_birth,
  p.gender           = row.gender,
  p.nationality      = row.nationality,
  p.occupation       = row.occupation,
  p.address          = row.address,
  p.city             = row.city,
  p.state            = row.state,
  p.postal_code      = row.postal_code,
  p.status           = row.status,
  p.source_id        = row.source_id,
  p.confidence_score = toFloat(row.confidence_score),
  p.created_at       = row.created_at,
  p.updated_at       = row.updated_at
"""


def load_persons(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "ENTITIES" / "persons.csv")
    return run_batches(driver, df, _MERGE_PERSON, "Persons")


# ─────────────────────────────────────────────────────────────────────────────
# Locations
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_LOCATION = """
UNWIND $batch AS row
MERGE (l:Location {location_id: row.location_id})
SET
  l.location_name    = row.location_name,
  l.location_type    = row.location_type,
  l.address          = row.address,
  l.city             = row.city,
  l.state            = row.state,
  l.country          = row.country,
  l.latitude         = toFloat(row.latitude),
  l.longitude        = toFloat(row.longitude),
  l.postal_code      = row.postal_code,
  l.risk_category    = row.risk_category,
  l.source_id        = row.source_id,
  l.confidence_score = toFloat(row.confidence_score),
  l.created_at       = row.created_at,
  l.updated_at       = row.updated_at
"""


def load_locations(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "ENTITIES" / "locations.csv")
    return run_batches(driver, df, _MERGE_LOCATION, "Locations")


# ─────────────────────────────────────────────────────────────────────────────
# Organizations
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_ORG = """
UNWIND $batch AS row
MERGE (o:Organization {organization_id: row.organization_id})
SET
  o.organization_name  = row.organization_name,
  o.alias              = row.alias,
  o.organization_type  = row.organization_type,
  o.registration_number= row.registration_number,
  o.address            = row.address,
  o.city               = row.city,
  o.state              = row.state,
  o.country            = row.country,
  o.industry           = row.industry,
  o.status             = row.status,
  o.source_id          = row.source_id,
  o.confidence_score   = toFloat(row.confidence_score),
  o.created_at         = row.created_at,
  o.updated_at         = row.updated_at
"""


def load_organizations(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "ENTITIES" / "organizations.csv")
    return run_batches(driver, df, _MERGE_ORG, "Organizations")


# ─────────────────────────────────────────────────────────────────────────────
# Vehicles  +  OWNS_VEHICLE edges
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_VEHICLE = """
UNWIND $batch AS row
MERGE (v:Vehicle {vehicle_id: row.vehicle_id})
SET
  v.registration_number = row.registration_number,
  v.vehicle_type        = row.vehicle_type,
  v.make                = row.make,
  v.model               = row.model,
  v.manufacturing_year  = row.manufacturing_year,
  v.color               = row.color,
  v.registration_date   = row.registration_date,
  v.status              = row.status,
  v.source_id           = row.source_id,
  v.confidence_score    = toFloat(row.confidence_score),
  v.created_at          = row.created_at,
  v.updated_at          = row.updated_at
"""

_OWNS_VEHICLE_PERSON = """
UNWIND $batch AS row
MATCH (v:Vehicle {vehicle_id: row.vehicle_id})
MATCH (p:Person   {person_id: row.owner_person_id})
MERGE (p)-[:OWNS_VEHICLE {source_id: row.source_id, confidence_score: toFloat(row.confidence_score)}]->(v)
"""

_OWNS_VEHICLE_ORG = """
UNWIND $batch AS row
MATCH (v:Vehicle      {vehicle_id:      row.vehicle_id})
MATCH (o:Organization {organization_id: row.owner_organization_id})
MERGE (o)-[:OWNS_VEHICLE {source_id: row.source_id, confidence_score: toFloat(row.confidence_score)}]->(v)
"""


def load_vehicles(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "ENTITIES" / "vehicles.csv")
    total = run_batches(driver, df, _MERGE_VEHICLE, "Vehicles (nodes)")

    # Person owners
    person_owners = df[df["owner_person_id"].notna()].copy()
    run_batches(driver, person_owners, _OWNS_VEHICLE_PERSON, "OWNS_VEHICLE (person)")

    # Org owners
    org_owners = df[df["owner_organization_id"].notna()].copy()
    run_batches(driver, org_owners, _OWNS_VEHICLE_ORG, "OWNS_VEHICLE (org)")

    return total


# ─────────────────────────────────────────────────────────────────────────────
# Phone Numbers  +  OWNS_PHONE edges
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_PHONE = """
UNWIND $batch AS row
MERGE (ph:PhoneNumber {phone_id: row.phone_id})
SET
  ph.phone_number_hash = row.phone_number_hash,
  ph.country_code      = row.country_code,
  ph.phone_type        = row.phone_type,
  ph.sim_id            = row.sim_id,
  ph.service_provider  = row.service_provider,
  ph.activation_date   = row.activation_date,
  ph.deactivation_date = row.deactivation_date,
  ph.status            = row.status,
  ph.source_id         = row.source_id,
  ph.confidence_score  = toFloat(row.confidence_score),
  ph.created_at        = row.created_at,
  ph.updated_at        = row.updated_at
"""

_OWNS_PHONE_PERSON = """
UNWIND $batch AS row
MATCH (ph:PhoneNumber {phone_id:   row.phone_id})
MATCH (p:Person       {person_id:  row.subscriber_person_id})
MERGE (p)-[:OWNS_PHONE {source_id: row.source_id, confidence_score: toFloat(row.confidence_score)}]->(ph)
"""

_OWNS_PHONE_ORG = """
UNWIND $batch AS row
MATCH (ph:PhoneNumber  {phone_id:        row.phone_id})
MATCH (o:Organization  {organization_id: row.subscriber_organization_id})
MERGE (o)-[:OWNS_PHONE {source_id: row.source_id, confidence_score: toFloat(row.confidence_score)}]->(ph)
"""


def load_phones(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "ENTITIES" / "phone_numbers.csv")
    total = run_batches(driver, df, _MERGE_PHONE, "PhoneNumbers (nodes)")

    person_subs = df[df["subscriber_person_id"].notna()].copy()
    run_batches(driver, person_subs, _OWNS_PHONE_PERSON, "OWNS_PHONE (person)")

    org_subs = df[df["subscriber_organization_id"].notna()].copy()
    run_batches(driver, org_subs, _OWNS_PHONE_ORG, "OWNS_PHONE (org)")

    return total


# ─────────────────────────────────────────────────────────────────────────────
# Accounts  +  HOLDS_ACCOUNT edges
# ─────────────────────────────────────────────────────────────────────────────

_MERGE_ACCOUNT = """
UNWIND $batch AS row
MERGE (a:Account {account_id: row.account_id})
SET
  a.account_number_hash         = row.account_number_hash,
  a.account_type                = row.account_type,
  a.financial_institution       = row.financial_institution,
  a.branch_code                 = row.branch_code,
  a.account_opening_date        = row.account_opening_date,
  a.account_closing_date        = row.account_closing_date,
  a.status                      = row.status,
  a.source_id                   = row.source_id,
  a.confidence_score            = toFloat(row.confidence_score),
  a.created_at                  = row.created_at,
  a.updated_at                  = row.updated_at
"""

_HOLDS_ACCOUNT_PERSON = """
UNWIND $batch AS row
MATCH (a:Account {account_id: row.account_id})
MATCH (p:Person  {person_id:  row.account_holder_person_id})
MERGE (p)-[:HOLDS_ACCOUNT {source_id: row.source_id, confidence_score: toFloat(row.confidence_score)}]->(a)
"""

_HOLDS_ACCOUNT_ORG = """
UNWIND $batch AS row
MATCH (a:Account      {account_id:      row.account_id})
MATCH (o:Organization {organization_id: row.account_holder_organization_id})
MERGE (o)-[:HOLDS_ACCOUNT {source_id: row.source_id, confidence_score: toFloat(row.confidence_score)}]->(a)
"""


def load_accounts(driver, dataset_root: Path) -> int:
    df = load_csv(dataset_root / "ENTITIES" / "accounts.csv")
    total = run_batches(driver, df, _MERGE_ACCOUNT, "Accounts (nodes)")

    person_holders = df[df["account_holder_person_id"].notna()].copy()
    run_batches(driver, person_holders, _HOLDS_ACCOUNT_PERSON, "HOLDS_ACCOUNT (person)")

    org_holders = df[df["account_holder_organization_id"].notna()].copy()
    run_batches(driver, org_holders, _HOLDS_ACCOUNT_ORG, "HOLDS_ACCOUNT (org)")

    return total


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def load_all_entities(driver, dataset_root: Path) -> dict:
    logger.info("=== Loading Entity Nodes ===")
    return {
        "persons":       load_persons(driver, dataset_root),
        "locations":     load_locations(driver, dataset_root),
        "organizations": load_organizations(driver, dataset_root),
        "vehicles":      load_vehicles(driver, dataset_root),
        "phones":        load_phones(driver, dataset_root),
        "accounts":      load_accounts(driver, dataset_root),
    }
