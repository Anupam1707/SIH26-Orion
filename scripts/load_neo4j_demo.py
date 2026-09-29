#!/usr/bin/env python3
"""
MuleTrail / SIH26 — Neo4j Demo Graph Loader (Problem Statement 26184)
Connects to Neo4j instance and executes the demo graph queries.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
root_dir = Path(__file__).resolve().parent.parent
load_dotenv(root_dir / ".env")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

CYPHER_FILE = Path(__file__).resolve().parent / "neo4j_demo_graph.cypher"


def load_demo_graph():
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("[-] neo4j driver not installed. Install via: pip install neo4j")
        sys.exit(1)

    if not CYPHER_FILE.exists():
        print(f"[-] Cypher file not found at: {CYPHER_FILE}")
        sys.exit(1)

    print(f"[*] Connecting to Neo4j at {NEO4J_URI} as {NEO4J_USER}...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            session.run("RETURN 1").single()
            print("[+] Neo4j connection verified successfully!")
    except Exception as e:
        print(f"[-] Could not connect to Neo4j: {e}")
        print("    Please check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in your .env file.")
        sys.exit(1)

    raw_cypher = CYPHER_FILE.read_text(encoding="utf-8")

    # Split on semicolon while ignoring comments
    statements = []
    current = []
    for line in raw_cypher.splitlines():
        stripped = line.strip()
        if stripped.startswith("//") or not stripped:
            continue
        current.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(current).rstrip(";").strip()
            if stmt and not stmt.upper().startswith("MATCH p=") and not stmt.upper().startswith("MATCH (N {DEMO: TRUE})-[R]->(M)"):
                statements.append(stmt)
            current = []

    print(f"[*] Executing {len(statements)} Cypher blocks...")
    with driver.session() as session:
        for idx, stmt in enumerate(statements, 1):
            try:
                session.run(stmt)
                print(f"  [{idx}/{len(statements)}] Executed Cypher block successfully.")
            except Exception as e:
                print(f"[-] Error in block {idx}:\n{stmt}\nError: {e}")

    print("\n[+] Demo Graph loaded successfully into Neo4j!")
    print("\nVerification Query:")
    print("  MATCH (n {demo: true})-[r]->(m) RETURN n, r, m;")
    print("\nPresentation Chain Query:")
    print("  MATCH p=(v:Victim)-[:TRANSACTED*1..4]->(m:Mule)-[:PREDICTED_CASHOUT]->(pa:PredictedATM) RETURN p;")
    driver.close()


if __name__ == "__main__":
    load_demo_graph()
