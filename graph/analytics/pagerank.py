"""
graph/analytics/pagerank.py

Performs PageRank & Network Centrality analysis on the Criminal Communication Network
using NetworkX and Neo4j.

Identifies key communication hubs, brokers, and influential phone numbers across CDRs.
"""

from typing import Dict, List, Any, Optional
import networkx as nx
from loguru import logger
from neo4j import Driver


def fetch_communication_edges(driver: Driver) -> List[Dict[str, Any]]:
    """Fetch all phone-to-phone communication edges from Neo4j."""
    query = """
    MATCH (src:PhoneNumber)-[r:CALLED]->(tgt:PhoneNumber)
    RETURN src.phone_id AS source,
           tgt.phone_id AS target,
           coalesce(r.duration_seconds, 60) AS duration,
           coalesce(r.confidence_score, 1.0) AS confidence
    """
    logger.info("Extracting CALLED edges from Neo4j...")
    with driver.session() as session:
        result = session.run(query)
        records = [record.data() for record in result]
    logger.info(f"Retrieved {len(records)} communication records from Neo4j.")
    return records


def build_phone_graph(records: List[Dict[str, Any]], weighted: bool = True) -> nx.DiGraph:
    """Build a directed NetworkX graph from communication records.
    
    If weighted=True, edge weights represent total call count.
    """
    G = nx.DiGraph()
    for row in records:
        src = row["source"]
        tgt = row["target"]
        if G.has_edge(src, tgt):
            G[src][tgt]["weight"] += 1
            G[src][tgt]["total_duration"] += row.get("duration", 0)
        else:
            G.add_edge(src, tgt, weight=1, total_duration=row.get("duration", 0))
    logger.info(f"Constructed DiGraph with {G.number_of_nodes()} nodes and {G.number_of_edges()} unique directed edges.")
    return G


def compute_pagerank(
    G: nx.DiGraph,
    alpha: float = 0.85,
    max_iter: int = 200,
    weight: Optional[str] = "weight"
) -> Dict[str, float]:
    """Compute PageRank scores for all nodes in the communication graph."""
    logger.info(f"Computing PageRank (alpha={alpha}, weight={weight})...")
    scores = nx.pagerank(G, alpha=alpha, max_iter=max_iter, weight=weight)
    return scores


def fetch_phone_metadata(driver: Driver, phone_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch associated details and subscriber / owner info for given phone numbers."""
    query = """
    UNWIND $phone_ids AS pid
    MATCH (ph:PhoneNumber {phone_id: pid})
    OPTIONAL MATCH (owner:Person)-[:OWNS_PHONE]->(ph)
    OPTIONAL MATCH (org:Organization)-[:OWNS_PHONE]->(ph)
    RETURN ph.phone_id AS phone_id,
           ph.phone_number_hash AS phone_hash,
           ph.service_provider AS service_provider,
           ph.status AS phone_status,
           owner.person_id AS owner_id,
           owner.full_name AS owner_name,
           owner.status AS owner_status,
           org.organization_name AS org_name
    """
    metadata = {}
    with driver.session() as session:
        result = session.run(query, phone_ids=phone_ids)
        for record in result:
            data = record.data()
            metadata[data["phone_id"]] = data
    return metadata


def write_pagerank_to_neo4j(
    driver: Driver,
    pagerank_scores: Dict[str, float],
    G: nx.DiGraph,
    batch_size: int = 1000
) -> int:
    """Write PageRank scores and degree metrics back into Neo4j PhoneNumber nodes."""
    logger.info("Writing PageRank scores and centrality metrics back to Neo4j...")
    query = """
    UNWIND $batch AS item
    MATCH (ph:PhoneNumber {phone_id: item.phone_id})
    SET ph.pagerank_score = item.pagerank,
        ph.in_degree       = item.in_degree,
        ph.out_degree      = item.out_degree
    """
    items = [
        {
            "phone_id": node,
            "pagerank": round(float(score), 8),
            "in_degree": int(G.in_degree(node)),
            "out_degree": int(G.out_degree(node)),
        }
        for node, score in pagerank_scores.items()
    ]

    total_updated = 0
    with driver.session() as session:
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            session.run(query, batch=batch)
            total_updated += len(batch)
    logger.success(f"Updated {total_updated} PhoneNumber nodes with PageRank scores in Neo4j.")
    return total_updated


def run_phone_pagerank_analysis(
    driver: Driver,
    top_n: int = 20,
    alpha: float = 0.85,
    weighted: bool = True,
    write_back: bool = False
) -> List[Dict[str, Any]]:
    """Orchestrates end-to-end PageRank analysis on phone communications."""
    records = fetch_communication_edges(driver)
    if not records:
        logger.warning("No communication records found in the database.")
        return []

    weight_attr = "weight" if weighted else None
    G = build_phone_graph(records, weighted=weighted)
    scores = compute_pagerank(G, alpha=alpha, weight=weight_attr)

    # Sort descending by PageRank score
    sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_nodes = sorted_nodes[:top_n]
    top_pids = [node for node, _ in top_nodes]

    # Fetch node metadata and owner information
    meta = fetch_phone_metadata(driver, top_pids)

    results = []
    for rank, (node, score) in enumerate(top_nodes, start=1):
        info = meta.get(node, {})
        results.append({
            "rank": rank,
            "phone_id": node,
            "pagerank": round(score, 6),
            "in_degree": G.in_degree(node),
            "out_degree": G.out_degree(node),
            "total_calls": G.in_degree(node) + G.out_degree(node),
            "service_provider": info.get("service_provider") or "Unknown",
            "owner_name": info.get("owner_name") or info.get("org_name") or "Unlinked / Unknown",
            "owner_id": info.get("owner_id") or "N/A",
            "owner_status": info.get("owner_status") or "N/A",
        })

    if write_back:
        write_pagerank_to_neo4j(driver, scores, G)

    return results
