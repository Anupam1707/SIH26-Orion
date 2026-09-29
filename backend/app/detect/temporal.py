"""Regularity within the single densest 48-hour window."""
import numpy as np


def zscore(values):
    values = np.asarray(values, dtype=float)
    return (values - values.mean()) / values.std() if len(values) and values.std() > 1e-12 else np.zeros_like(values)


def temporal(graph) -> dict:
    result = {a: {'temporal_score': 0., 'temporal_tx_ids': []} for a in graph}
    rows = []
    for aid in graph:
        tx = sorted((d for *_, d in graph.out_edges(aid, data=True)), key=lambda d: (d['t'], d['id']))
        if len(tx) < 5:
            continue
        times = np.array([t['t'] for t in tx])
        ends = np.searchsorted(times, times + 48 * 3600, side='right')
        start = int(np.argmax(ends - np.arange(len(times))))
        end = int(ends[start])
        if end - start < 5:
            continue
        gaps = np.diff(times[start:end]) / 60
        amounts = np.array([t['amount_inr'] for t in tx[start:end]])
        gap_cv = float(gaps.std() / gaps.mean()) if gaps.mean() else 0.
        amount_cv = float(amounts.std() / amounts.mean()) if amounts.mean() else 0.
        rows.append((aid, gap_cv, (end - start) / len(tx), amount_cv))
        result[aid].update(temporal_tx_ids=[t['id'] for t in tx[start:end]],
                           cv_gap=gap_cv, burst_ratio=(end - start) / len(tx), cv_amount=amount_cv)
    if rows:
        scores = -zscore([r[1] for r in rows]) + zscore([r[2] for r in rows]) - zscore([r[3] for r in rows])
        for row, score in zip(rows, scores):
            result[row[0]]['temporal_score'] = float(score)
    return result
