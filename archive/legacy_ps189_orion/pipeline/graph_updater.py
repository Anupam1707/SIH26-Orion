"""
pipeline/graph_updater.py — Tri-Partite Criminal Knowledge Graph (CKG) Manager
SIH PS 189 · I4C / Ministry of Home Affairs

Manages graph state, provenance binding, and enforces the Tri-Partite Taxonomy:
- EXPLICIT: Documented evidentiary relationships (bank transfers, CDR logs, registered ownership)
- INFERRED: Structural & cross-domain deduced ties (co-occurrence in case records, multi-hop reachability)
- PREDICTED: Machine Learning forecasted links (probable hidden accomplices, concealed conduits)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

class GraphNode:
    def __init__(self, node_id: str, label: str, entity_type: str, properties: Dict[str, Any] = None):
        self.id = node_id
        self.label = label
        self.entity_type = entity_type
        self.properties = properties or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "entity_type": self.entity_type,
            **self.properties
        }


class GraphEdge:
    def __init__(self, edge_id: str, source: str, target: str, edge_type: str, 
                 taxonomy: str, evidence_id: str, confidence: float, properties: Dict[str, Any] = None):
        if taxonomy not in ("Explicit", "Inferred", "Predicted"):
            raise ValueError(f"Invalid taxonomy: {taxonomy}. Must be 'Explicit', 'Inferred', or 'Predicted'.")
        self.id = edge_id
        self.source = source
        self.target = target
        self.edge_type = edge_type
        self.taxonomy = taxonomy
        self.evidence_id = evidence_id
        self.confidence = confidence
        self.properties = properties or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
            "taxonomy": self.taxonomy,
            "evidence_id": self.evidence_id,
            "confidence": round(self.confidence, 3),
            **self.properties
        }


class CriminalKnowledgeGraph:
    """
    In-memory graph representation with indexing and tri-partite edge taxonomy enforcement.
    """

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.adjacency: Dict[str, List[str]] = {}
        self.in_degree: Dict[str, int] = {}
        self.out_degree: Dict[str, int] = {}

    def add_node(self, node_id: str, label: str, entity_type: str, properties: Dict[str, Any] = None) -> GraphNode:
        if node_id not in self.nodes:
            node = GraphNode(node_id, label, entity_type, properties)
            self.nodes[node_id] = node
            self.adjacency[node_id] = []
            self.in_degree[node_id] = 0
            self.out_degree[node_id] = 0
        else:
            if properties:
                self.nodes[node_id].properties.update(properties)
        return self.nodes[node_id]

    def add_edge(self, edge_id: str, source: str, target: str, edge_type: str,
                 taxonomy: str, evidence_id: str, confidence: float = 0.95,
                 properties: Dict[str, Any] = None) -> GraphEdge:
        if source not in self.nodes:
            self.add_node(source, source, "Unknown")
        if target not in self.nodes:
            self.add_node(target, target, "Unknown")

        edge = GraphEdge(edge_id, source, target, edge_type, taxonomy, evidence_id, confidence, properties)
        self.edges[edge_id] = edge
        self.adjacency[source].append(target)
        self.out_degree[source] = self.out_degree.get(source, 0) + 1
        self.in_degree[target] = self.in_degree.get(target, 0) + 1
        return edge

    def get_neighbors(self, node_id: str) -> List[str]:
        return self.adjacency.get(node_id, [])

    def get_egonet(self, node_id: str) -> Dict[str, Any]:
        """Returns the 1-hop egonet nodes and internal edges for OddBall analysis."""
        if node_id not in self.nodes:
            return {"nodes": [], "edges": []}
        
        # 1-hop neighbors (undirected sense)
        neighbors = set()
        for e in self.edges.values():
            if e.source == node_id:
                neighbors.add(e.target)
            elif e.target == node_id:
                neighbors.add(e.source)
        
        egonet_node_ids = {node_id} | neighbors
        egonet_nodes = [self.nodes[nid].to_dict() for nid in egonet_node_ids if nid in self.nodes]
        egonet_edges = [
            e.to_dict() for e in self.edges.values()
            if e.source in egonet_node_ids and e.target in egonet_node_ids
        ]
        return {
            "center": node_id,
            "nodes": egonet_nodes,
            "edges": egonet_edges,
            "node_count": len(egonet_nodes),
            "edge_count": len(egonet_edges)
        }

    def summary(self) -> Dict[str, Any]:
        tax_counts = {"Explicit": 0, "Inferred": 0, "Predicted": 0}
        for e in self.edges.values():
            tax_counts[e.taxonomy] = tax_counts.get(e.taxonomy, 0) + 1
        
        type_counts = {}
        for n in self.nodes.values():
            type_counts[n.entity_type] = type_counts.get(n.entity_type, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_breakdown": type_counts,
            "taxonomy_breakdown": tax_counts
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges.values()],
            "summary": self.summary()
        }
