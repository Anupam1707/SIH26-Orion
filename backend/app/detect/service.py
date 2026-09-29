"""Reusable detection snapshots; public inputs only."""
import numpy as np
from app.detect.rules import detect_rules
from app.detect.oddball import oddball
from app.detect.temporal import temporal
from app.graph.builder import build_graph


def analyze(public, clock, config):
    graph = build_graph(public, clock)
    matches = detect_rules(graph, config)
    structural, bursts = oddball(graph), temporal(graph)
    risks = {}
    for aid in graph:
        hits = [m for m in matches if aid in m['flagged']]
        rules = sorted({m['rule'] for m in hits})
        signals = [{'name': m['rule'], 'reason': m['detail']['reason'], 'tx_ids': m['tx_ids']}
                   for m in hits]
        odd, burst = structural[aid], bursts[aid]
        if odd['oddball_z'] > 0:
            neighbours = set(graph.predecessors(aid)) | set(graph.successors(aid))
            ids = [d['id'] for u in neighbours | {aid} for _, v, d in graph.out_edges(u, data=True)
                   if v in neighbours | {aid}]
            signals.append({'name': 'OddBall', 'reason': f"{odd['shape']} structure has a within-shape z-score of {odd['oddball_z']:.2f}.", 'tx_ids': ids})
        if burst['temporal_score'] > 0:
            signals.append({'name': 'Temporal burst', 'reason': 'Regular timing and amounts concentrate in the densest 48-hour window.',
                            'tx_ids': burst['temporal_tx_ids']})
        raw = len(rules) + max(odd['oddball_z'], 0) + max(burst['temporal_score'], 0)
        risks[aid] = {'raw': raw, 'rules': rules, 'signals': signals, **odd, **burst}
    p99 = float(np.percentile([r['raw'] for r in risks.values()], 99)) if risks else 0.
    for risk in risks.values():
        risk['risk'] = min(risk['raw'] / p99, 1.) if p99 > 0 else 0.
    return {'clock': clock.isoformat(), 'risks': risks, 'matches': matches, 'p99': p99}
