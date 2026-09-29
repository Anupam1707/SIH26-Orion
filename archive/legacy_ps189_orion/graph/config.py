"""
graph/config.py

Reads Neo4j connection settings from environment / .env file.
Usage:
    from graph.config import get_driver, DATASET_ROOT
    driver = get_driver()
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
from loguru import logger

# ── Load .env from project root ──────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# ── Connection settings ───────────────────────────────────────────────────────
NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# ── Dataset root ──────────────────────────────────────────────────────────────
_DEFAULT_DATASET = _PROJECT_ROOT / "data" / "dataset"
DATASET_ROOT: Path = Path(os.getenv("DATASET_ROOT", str(_DEFAULT_DATASET)))


def get_driver():
    """Return an authenticated Neo4j driver instance."""
    if not NEO4J_PASSWORD:
        raise EnvironmentError(
            "NEO4J_PASSWORD is not set. "
            "Copy .env.example → .env and fill in your credentials."
        )
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
    )
    driver.verify_connectivity()
    logger.info(f"Connected to Neo4j at {NEO4J_URI}")
    return driver
