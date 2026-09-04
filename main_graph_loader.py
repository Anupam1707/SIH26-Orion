"""
main_graph_loader.py

Orchestrates the full Criminal Knowledge Graph build into Neo4j.

Usage:
    python main_graph_loader.py

Prerequisites:
    1. Copy .env.example → .env and set NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD
    2. Ensure Neo4j is reachable at the configured URI
    3. pip install -r requirements.txt
"""

import sys
import time
from pathlib import Path

from loguru import logger

from graph.config import get_driver, DATASET_ROOT
from graph.schema import apply_schema
from graph.loaders.load_entities import load_all_entities
from graph.loaders.load_cases import load_all_cases
from graph.loaders.load_evidence import load_all_evidence
from graph.loaders.load_relationships import load_all_relationships
from graph.loaders.load_entity_resolution import load_all_entity_resolution


# ── Logger setup ──────────────────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO",
    colorize=True,
)
logger.add(
    "graph_load.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="DEBUG",
    rotation="10 MB",
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_summary(phase: str, counts: dict, elapsed: float) -> None:
    logger.info(f"── {phase} completed in {elapsed:.1f}s ──")
    for k, v in counts.items():
        logger.info(f"   {k:<30} {v:>8,} rows")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    overall_start = time.time()

    logger.info("╔══════════════════════════════════════════════════╗")
    logger.info("║   Criminal Knowledge Graph — Full Load           ║")
    logger.info("╚══════════════════════════════════════════════════╝")
    logger.info(f"Dataset root : {DATASET_ROOT}")

    if not DATASET_ROOT.exists():
        logger.error(f"Dataset root not found: {DATASET_ROOT}")
        sys.exit(1)

    # 1. Connect ───────────────────────────────────────────────────────────────
    driver = get_driver()

    # 2. Schema ────────────────────────────────────────────────────────────────
    t = time.time()
    logger.info("── Phase 1 / 5 : Applying schema (constraints + indexes) ──")
    apply_schema(driver)
    logger.info(f"   Schema applied in {time.time() - t:.1f}s")

    # 3. Entities ──────────────────────────────────────────────────────────────
    t = time.time()
    logger.info("── Phase 2 / 5 : Loading entity nodes ──")
    entity_counts = load_all_entities(driver, DATASET_ROOT)
    _print_summary("Entity nodes", entity_counts, time.time() - t)

    # 4. Cases / Crimes / Events ───────────────────────────────────────────────
    t = time.time()
    logger.info("── Phase 3 / 5 : Loading case / crime / event nodes ──")
    case_counts = load_all_cases(driver, DATASET_ROOT)
    _print_summary("Case nodes", case_counts, time.time() - t)

    # 5. Evidence / Provenance ─────────────────────────────────────────────────
    t = time.time()
    logger.info("── Phase 4 / 5 : Loading evidence / provenance nodes ──")
    evidence_counts = load_all_evidence(driver, DATASET_ROOT)
    _print_summary("Evidence nodes", evidence_counts, time.time() - t)

    # 6. Relationships ─────────────────────────────────────────────────────────
    t = time.time()
    logger.info("── Phase 5a / 5 : Loading relationship edges ──")
    rel_counts = load_all_relationships(driver, DATASET_ROOT)
    _print_summary("Relationship edges", rel_counts, time.time() - t)

    # 7. Entity Resolution ─────────────────────────────────────────────────────
    t = time.time()
    logger.info("── Phase 5b / 5 : Loading entity resolution artefacts ──")
    er_counts = load_all_entity_resolution(driver, DATASET_ROOT)
    _print_summary("Entity resolution", er_counts, time.time() - t)

    driver.close()

    total_elapsed = time.time() - overall_start
    logger.success("╔══════════════════════════════════════════════════╗")
    logger.success(f"║  Graph load complete in {total_elapsed:.1f}s".ljust(50) + "║")
    logger.success("╚══════════════════════════════════════════════════╝")
    logger.info("Run  python verify_graph.py  to check node/edge counts.")


if __name__ == "__main__":
    main()
