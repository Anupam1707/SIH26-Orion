"""OddBall egonet score, normalized independently by shape."""
import numpy as np


def oddball(graph) -> dict:
    counts = []
    for aid in graph:
        neighbours = (set(graph.predecessors(aid)) | set(graph.successors(aid))) - {aid}
        edges = sum(len(graph[u][v]) for u in neighbours for v in graph.successors(u) if v in neighbours)
        if len(neighbours) > 1 and edges > 0:
            counts.append((aid, len(neighbours), edges))
    result = {a: {'oddball_z': 0., 'oddball_raw': 0., 'shape': None} for a in graph}
    if len(counts) < 2:
        return result
    x = np.log10([r[1] for r in counts])
    y = np.log10([r[2] for r in counts])
    alpha, intercept = np.polyfit(x, y, 1) if np.std(x) > 1e-12 else (0., float(y.mean()))
    for (aid, n, e), expected in zip(counts, 10 ** (alpha * x + intercept)):
        score = max(e, expected) / min(e, expected) * np.log10(abs(e - expected) + 1)
        result[aid] = {'oddball_z': 0., 'oddball_raw': float(score),
                       'shape': 'STAR' if e < expected else 'NEAR_CLIQUE',
                       'egonet_nodes': n, 'egonet_edges': e}
    for shape in ('STAR', 'NEAR_CLIQUE'):
        ids = [a for a in result if result[a]['shape'] == shape]
        values = np.array([result[a]['oddball_raw'] for a in ids])
        if len(values) and values.std() > 1e-12:
            for aid, z in zip(ids, (values - values.mean()) / values.std()):
                result[aid]['oddball_z'] = float(z)
    return result
