"""Conservative chronological flow attribution; no hidden case labels."""
from collections import defaultdict
import networkx as nx


def trace_case(graph: nx.MultiDiGraph, complaint: dict, risks: dict | None = None,
               max_hops: int = 5, min_share: float = .05) -> dict:
    risks = risks or {}
    victim = complaint['victim_account_id']
    amount = float(complaint['amount_inr'])
    balances = defaultdict(float, {victim: amount})
    hops = {victim: 0}
    edges = []
    transactions = sorted((d for *_, d in graph.edges(data=True)), key=lambda d: (d['ts'], d['id']))
    for tx in transactions:
        src, dst = tx['src'], tx['dst']
        if tx['ts'] < complaint['incident_at'] or src not in hops or hops[src] >= max_hops:
            continue
        if dst == victim or (dst in hops and hops[dst] <= hops[src]):
            continue
        traced = min(balances[src], float(tx['amount_inr']))
        balances[src] -= traced
        if traced < amount * min_share:
            continue
        balances[dst] += traced
        hops[dst] = min(hops.get(dst, max_hops), hops[src] + 1)
        edges.append({**tx, 'traced_amount_inr': traced, 'hop': hops[src] + 1})
    nodes = []
    for aid, hop in sorted(hops.items(), key=lambda item: (item[1], item[0])):
        risk = risks.get(aid, {'risk': 0, 'signals': [], 'rules': []})
        rules = risk.get('rules', [])
        role = ('victim' if aid == victim else 'collector' if 'Mule fan-in' in rules
                else 'pass-through' if 'Rapid pass-through' in rules or 'Layering chain' in rules
                else 'recipient')
        nodes.append({'id': aid, 'hop': hop, 'inferred_role': role, **risk})
    return {'complaint': complaint, 'nodes': nodes, 'edges': edges,
            'hop_order': sorted(set(e['hop'] for e in edges)),
            'attribution_note': 'Chronological flow estimate; account balances and ownership of funds are not known.'}
