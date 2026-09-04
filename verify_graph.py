"""
verify_graph.py

Post-load sanity checker.
Runs Cypher COUNT queries against the loaded graph and compares results
against expected CSV row counts. Prints a formatted table to stdout.

Usage:
    python verify_graph.py
"""

import sys
from pathlib import Path

from loguru import logger

from graph.config import get_driver, DATASET_ROOT
from graph.utils import load_csv

# ── Logger setup ──────────────────────────────────────────────────────────────
logger.remove()
logger.add(sys.stderr, format="<level>{message}</level>", level="INFO", colorize=True)


# ── Expected counts from CSVs ─────────────────────────────────────────────────

def _csv_count(rel_path: str) -> int:
    """Return number of data rows (excluding header) in a CSV."""
    p = DATASET_ROOT / rel_path
    df = load_csv(p)
    return len(df)


# ── Cypher count queries ──────────────────────────────────────────────────────

NODE_CHECKS = [
    ("Person",       "ENTITIES/persons.csv",              "MATCH (n:Person) RETURN count(n) AS c"),
    ("Location",     "ENTITIES/locations.csv",            "MATCH (n:Location) RETURN count(n) AS c"),
    ("Organization", "ENTITIES/organizations.csv",        "MATCH (n:Organization) RETURN count(n) AS c"),
    ("Vehicle",      "ENTITIES/vehicles.csv",             "MATCH (n:Vehicle) RETURN count(n) AS c"),
    ("PhoneNumber",  "ENTITIES/phone_numbers.csv",        "MATCH (n:PhoneNumber) RETURN count(n) AS c"),
    ("Account",      "ENTITIES/accounts.csv",             "MATCH (n:Account) RETURN count(n) AS c"),
    ("Case",         "CASES_EVENTS/cases.csv",            "MATCH (n:Case) RETURN count(n) AS c"),
    ("Crime",        "CASES_EVENTS/crimes.csv",           "MATCH (n:Crime) RETURN count(n) AS c"),
    ("Event",        "CASES_EVENTS/events.csv",           "MATCH (n:Event) RETURN count(n) AS c"),
    ("Evidence",     "EVIDENCE/evidence.csv",             "MATCH (n:Evidence) RETURN count(n) AS c"),
    ("Source",       "EVIDENCE/sources.csv",              "MATCH (n:Source) RETURN count(n) AS c"),
    ("Document",     "UNSTRUCTURED/documents.csv",        "MATCH (n:Document) RETURN count(n) AS c"),
    ("Alias",        "ENTITY_RESOLUTION/aliases.csv",     "MATCH (n:Alias) RETURN count(n) AS c"),
]

EDGE_CHECKS = [
    ("CALLED",         "RELATIONSHIPS/communications.csv",     "MATCH ()-[r:CALLED]->() RETURN count(r) AS c"),
    ("MEMBER_OF",      "RELATIONSHIPS/memberships.csv",        "MATCH ()-[r:MEMBER_OF]->() RETURN count(r) AS c"),
    ("TRANSACTED",     "RELATIONSHIPS/transactions.csv",       "MATCH ()-[r:TRANSACTED]->() RETURN count(r) AS c"),
    ("LINKED_TO",      "RELATIONSHIPS/relationships.csv",      "MATCH ()-[r:LINKED_TO]->() RETURN count(r) AS c"),
    ("OWNS_PHONE",     None,                                   "MATCH ()-[r:OWNS_PHONE]->() RETURN count(r) AS c"),
    ("OWNS_VEHICLE",   None,                                   "MATCH ()-[r:OWNS_VEHICLE]->() RETURN count(r) AS c"),
    ("HOLDS_ACCOUNT",  None,                                   "MATCH ()-[r:HOLDS_ACCOUNT]->() RETURN count(r) AS c"),
    ("MOVED_TO",       "RELATIONSHIPS/movements.csv",          "MATCH ()-[r:MOVED_TO]->() RETURN count(r) AS c"),
    ("PART_OF_CASE",   None,                                   "MATCH ()-[r:PART_OF_CASE]->() RETURN count(r) AS c"),
    ("OCCURRED_AT",    None,                                   "MATCH ()-[r:OCCURRED_AT]->() RETURN count(r) AS c"),
    ("ALIAS_OF",       None,                                   "MATCH ()-[r:ALIAS_OF]->() RETURN count(r) AS c"),
    ("SAME_ENTITY",    None,                                   "MATCH ()-[r:SAME_ENTITY]->() RETURN count(r) AS c"),
]


# ── Totals via Cypher ─────────────────────────────────────────────────────────

TOTAL_QUERIES = [
    ("Total nodes",    "MATCH (n) RETURN count(n) AS c"),
    ("Total edges",    "MATCH ()-[r]->() RETURN count(r) AS c"),
    ("Total labels",   "CALL db.labels() YIELD label RETURN count(label) AS c"),
    ("Total rel types","CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) AS c"),
]


# ── Report printer ────────────────────────────────────────────────────────────

def _col(s: str, w: int) -> str:
    return str(s).ljust(w)[:w]


def _run(session, cypher: str) -> int:
    result = session.run(cypher)
    record = result.single()
    return int(record["c"]) if record else 0


def _status(actual: int, expected: int | None) -> str:
    if expected is None:
        return "  —  "
    pct = actual / expected if expected else 0
    if pct >= 0.95:
        return "  ✅  "
    if pct >= 0.80:
        return "  ⚠️  "
    return "  ❌  "


def main() -> None:
    driver = get_driver()

    print()
    print("=" * 72)
    print("  Criminal Knowledge Graph — Verification Report")
    print("=" * 72)

    with driver.session() as session:

        # ── Node checks ──────────────────────────────────────────────────────
        print(f"\n{'NODE LABEL':<20} {'EXPECTED':>10} {'IN GRAPH':>10}  STATUS")
        print("-" * 55)
        for label, csv_path, cypher in NODE_CHECKS:
            expected = _csv_count(csv_path) if csv_path else None
            actual   = _run(session, cypher)
            exp_str  = f"{expected:,}" if expected is not None else "  n/a"
            print(f"  {label:<18} {exp_str:>10} {actual:>10,}  {_status(actual, expected)}")

        # ── Edge checks ──────────────────────────────────────────────────────
        print(f"\n{'EDGE TYPE':<20} {'EXPECTED':>10} {'IN GRAPH':>10}  STATUS")
        print("-" * 55)
        for rel_type, csv_path, cypher in EDGE_CHECKS:
            expected = _csv_count(csv_path) if csv_path else None
            actual   = _run(session, cypher)
            exp_str  = f"{expected:,}" if expected is not None else "  n/a"
            print(f"  {rel_type:<18} {exp_str:>10} {actual:>10,}  {_status(actual, expected)}")

        # ── Totals ────────────────────────────────────────────────────────────
        print(f"\n{'METRIC':<30} {'VALUE':>12}")
        print("-" * 45)
        for label, cypher in TOTAL_QUERIES:
            val = _run(session, cypher)
            print(f"  {label:<28} {val:>12,}")

    driver.close()
    print()
    print("✅ = ≥95% of expected rows   ⚠️  = 80–95%   ❌ = <80%   — = computed")
    print()


if __name__ == "__main__":
    main()
