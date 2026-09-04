"""
graph/schema.py

Creates all Neo4j uniqueness constraints and indexes for the Criminal
Knowledge Graph. Safe to re-run (uses IF NOT EXISTS).

Call:
    from graph.schema import apply_schema
    apply_schema(driver)
"""

from loguru import logger


# ── Uniqueness Constraints ────────────────────────────────────────────────────
# Guarantees each node ID is unique and automatically creates a backing index.

CONSTRAINTS = [
    ("Person",       "person_id"),
    ("Location",     "location_id"),
    ("Organization", "organization_id"),
    ("Vehicle",      "vehicle_id"),
    ("PhoneNumber",  "phone_id"),
    ("Account",      "account_id"),
    ("Case",         "case_id"),
    ("Crime",        "crime_id"),
    ("Event",        "event_id"),
    ("Evidence",     "evidence_id"),
    ("Document",     "document_id"),
    ("Source",       "source_id"),
    ("Alias",        "alias_id"),
]

# ── Additional property indexes ───────────────────────────────────────────────
# Speeds up lookup-heavy analytics queries.

INDEXES = [
    ("Person",       "full_name"),
    ("Person",       "status"),
    ("Person",       "city"),
    ("Location",     "city"),
    ("Location",     "risk_category"),
    ("Organization", "organization_name"),
    ("Organization", "status"),
    ("Case",         "case_status"),
    ("Case",         "case_type"),
    ("Crime",        "crime_type"),
    ("Crime",        "severity_level"),
    ("PhoneNumber",  "status"),
    ("Account",      "status"),
    ("Evidence",     "evidence_type"),
]


def apply_schema(driver) -> None:
    """Create all constraints and indexes; safe to call on a populated DB."""
    with driver.session() as session:
        # -- Uniqueness constraints --
        for label, prop in CONSTRAINTS:
            cypher = (
                f"CREATE CONSTRAINT IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
            )
            session.run(cypher)
            logger.debug(f"Constraint ensured: ({label}).{prop}")

        logger.info(f"Created/verified {len(CONSTRAINTS)} uniqueness constraints.")

        # -- Property indexes --
        for label, prop in INDEXES:
            idx_name = f"idx_{label.lower()}_{prop}"
            cypher = (
                f"CREATE INDEX {idx_name} IF NOT EXISTS "
                f"FOR (n:{label}) ON (n.{prop})"
            )
            session.run(cypher)
            logger.debug(f"Index ensured: ({label}).{prop}")

        logger.info(f"Created/verified {len(INDEXES)} property indexes.")

    logger.success("Schema applied successfully.")
